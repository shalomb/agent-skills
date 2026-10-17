#!/usr/bin/env python3
"""smart_squash: fold insignificant commits into the next significant one.

Classifies each first-parent commit as ANCHOR (kept) or NOISE (folded), writes a
reviewable plan, and applies it to a NEW branch whose final tree is byte-identical
to the source branch. Never moves existing refs, never pushes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

RELEASE_TYPE = re.compile(r"^(feat|fix|perf|revert)(\([^)]*\))?(!)?:", re.IGNORECASE)
BREAKING_BANG = re.compile(r"^[a-z]+(\([^)]*\))?!:", re.IGNORECASE)
PR_REF = re.compile(r"\(#\d+\)")
NOISE = re.compile(
    r"^(wip|tmp|oops|typo|lint|fmt|format|fixup!|squash!|sync)\b"
    r"|\btypo\b|ruff format|address review|review comments|whitespace",
    re.IGNORECASE,
)
NON_RUNTIME_DIRS = ("tests/", "test/", "examples/", "docs/", ".github/")
RUNTIME_EXT = (".tf", ".tfvars", ".tpl")


@dataclass(frozen=True)
class Commit:
    sha: str
    parents: tuple
    subject: str
    body: str = ""
    files: tuple = ()
    added: int = 0
    deleted: int = 0
    tags: tuple = ()


@dataclass(frozen=True)
class Config:
    large_lines: int = 100
    runtime_tf_is_anchor: bool = True


@dataclass(frozen=True)
class Classification:
    anchor: bool
    reason: str


def is_runtime_path(path: str) -> bool:
    if path.startswith(NON_RUNTIME_DIRS):
        return False
    return path.endswith(RUNTIME_EXT) and not path.endswith(".tftest.hcl")


def classify(c: Commit, cfg: Config) -> Classification:
    if not c.parents:
        return Classification(True, "root commit")
    if len(c.parents) > 1:
        return Classification(True, "merge commit")
    if c.tags:
        return Classification(True, f"tagged {c.tags[0]}")
    if RELEASE_TYPE.match(c.subject):
        return Classification(True, f"release-driving type ({c.subject.split(':')[0]})")
    if BREAKING_BANG.match(c.subject) or "BREAKING CHANGE" in c.body:
        return Classification(True, "breaking change")
    if PR_REF.search(c.subject):
        return Classification(True, "PR reference")
    if NOISE.search(c.subject):
        return Classification(False, "noise pattern")
    if c.added + c.deleted >= cfg.large_lines:
        return Classification(True, f"large change ({c.added + c.deleted} lines)")
    if cfg.runtime_tf_is_anchor and any(is_runtime_path(f) for f in c.files):
        return Classification(True, "touches runtime .tf")
    return Classification(False, "small, non-runtime")


# ---------------------------------------------------------------- reading history

def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def _tag_map(repo: Path) -> dict:
    """sha -> tuple of tag names, peeling annotated tags to their commit."""
    out = _git(repo, "for-each-ref", "refs/tags", "--format=%(refname:short)\t%(*objectname)\t%(objectname)")
    tags: dict = {}
    for line in out.splitlines():
        name, peeled, direct = line.split("\t")
        tags.setdefault(peeled or direct, []).append(name)
    return {k: tuple(v) for k, v in tags.items()}


def read_commits(repo: Path, base: str | None, branch: str) -> list:
    """First-parent commits of base..branch, oldest first, with numstat and tags."""
    rng = f"{base}..{branch}" if base else branch
    fmt = "%x1e%H%x1f%P%x1f%s%x1f%b%x1f"
    out = _git(repo, "log", "--first-parent", "--reverse", "--no-renames", "--numstat", f"--format={fmt}", rng)
    tags = _tag_map(repo)
    commits = []
    for rec in out.split("\x1e")[1:]:
        sha, parents, subject, body, stats = rec.split("\x1f", 4)
        files, added, deleted = [], 0, 0
        for line in stats.strip().splitlines():
            a, d, path = line.split("\t", 2)
            files.append(path)
            added += int(a) if a.isdigit() else 0
            deleted += int(d) if d.isdigit() else 0
        commits.append(Commit(sha, tuple(parents.split()), subject, body.strip(), tuple(files), added, deleted, tags.get(sha, ())))
    return commits


# ---------------------------------------------------------------- planning

@dataclass
class Group:
    anchor: str                 # commit whose message/author the squashed commit keeps
    anchor_subject: str
    reason: str
    members: list = field(default_factory=list)   # every source sha folded in, oldest first
    folded: list = field(default_factory=list)    # (sha, subject) of the non-anchor members
    tip: str = ""               # last member: its tree is the squashed commit's tree


@dataclass
class Plan:
    groups: list
    before: int
    after: int


def build_plan(commits: list, cfg: Config) -> Plan:
    groups: list = []
    pending: list = []
    for c in commits:
        verdict = classify(c, cfg)
        if verdict.anchor:
            g = Group(c.sha, c.subject, verdict.reason, [x.sha for x in pending] + [c.sha],
                      [(x.sha, x.subject) for x in pending], c.sha)
            groups.append(g)
            pending = []
        else:
            pending.append(c)
    if pending:
        if groups:
            g = groups[-1]
            g.members += [x.sha for x in pending]
            g.folded += [(x.sha, x.subject) for x in pending]
            g.tip = pending[-1].sha
        else:
            last = pending[-1]
            groups.append(Group(last.sha, last.subject, "no anchors: single group", [x.sha for x in pending],
                                [(x.sha, x.subject) for x in pending[:-1]], last.sha))
    return Plan(groups, len(commits), len(groups))


# ---------------------------------------------------------------- safety + range

class Refused(Exception):
    """A safety rule stopped the operation; nothing was written."""


def _ref_exists(repo: Path, ref: str) -> bool:
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", ref], capture_output=True, text=True)
    return r.returncode == 0


def default_branch(repo: Path) -> str | None:
    r = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                       capture_output=True, text=True)
    if r.returncode == 0 and "/" in r.stdout:
        return r.stdout.strip().split("/", 1)[1]
    for name in ("main", "master"):
        if _ref_exists(repo, f"refs/heads/{name}"):
            return name
    return None


def resolve_range(repo: Path, branch: str, base: str | None, allow_default: bool = False):
    """Return (base, default_branch). Default: only commits not already on the default branch."""
    default = default_branch(repo)
    if base:
        return base, default
    if branch == default:
        if not allow_default:
            raise Refused(f"{branch} is the default branch (published history); "
                          "pass --allow-default to plan it explicitly, or give --base")
        return None, default
    ref = f"origin/{default}" if default and _ref_exists(repo, f"refs/remotes/origin/{default}") else default
    if not ref:
        return None, default
    return _git(repo, "merge-base", ref, branch).strip(), default


def signing_args(repo: Path) -> list:
    r = subprocess.run(["git", "-C", str(repo), "config", "--type=bool", "commit.gpgsign"], capture_output=True, text=True)
    return ["-S"] if r.stdout.strip() == "true" else []


# ---------------------------------------------------------------- applying

@dataclass
class Result:
    branch: str
    tip: str
    sha_map: dict
    tag_map: dict


def _parents_of(repo: Path, sha: str) -> list:
    return _git(repo, "rev-list", "--parents", "-n1", sha).split()[1:]


def _message(repo: Path, group: Group) -> str:
    msg = _git(repo, "log", "-1", "--format=%B", group.anchor).strip()
    if group.folded:
        lines = [f"- {sha[:8]} {subject}" for sha, subject in group.folded]
        msg += f"\n\nFolded commits ({len(lines)}):\n" + "\n".join(lines)
    return msg + "\n"


def apply_plan(repo: Path, plan: Plan, branch: str, base: str | None, out_branch: str | None = None) -> Result:
    out = out_branch or f"{branch}-smart-squash"
    if _ref_exists(repo, f"refs/heads/{out}"):
        raise Refused(f"output branch {out} already exists; remove it or choose --out")
    if plan.after >= plan.before:
        raise Refused("nothing to squash: every commit is an anchor")
    prev = _parents_of(repo, plan.groups[0].members[0])[:1]
    sha_map: dict = {}
    sign = signing_args(repo)
    for g in plan.groups:
        tree = _git(repo, "rev-parse", f"{g.tip}^{{tree}}").strip()
        original = _parents_of(repo, g.anchor)
        parents = prev + original[1:]            # first parent is rewritten; merge side parents stay original
        name, email, date = _git(repo, "log", "-1", "--format=%an%x1f%ae%x1f%aI", g.anchor).strip().split("\x1f")
        env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_AUTHOR_DATE=date)
        args = ["git", "-C", str(repo), "commit-tree", tree, *sign]
        for p in parents:
            args += ["-p", p]
        r = subprocess.run(args, input=_message(repo, g), capture_output=True, text=True, env=env)
        if r.returncode:
            raise RuntimeError(f"commit-tree failed: {r.stderr.strip()}")
        new = r.stdout.strip()
        for m in g.members:
            sha_map[m] = new
        prev = [new]
    tip = prev[0]
    want = _git(repo, "rev-parse", f"{branch}^{{tree}}").strip()
    got = _git(repo, "rev-parse", f"{tip}^{{tree}}").strip()
    if want != got:
        raise RuntimeError(f"tree mismatch (source {want[:8]} vs squashed {got[:8]}); no branch created")
    _git(repo, "update-ref", f"refs/heads/{out}", tip, "")
    tag_map = {t: (sha, sha_map[sha]) for sha, names in _tag_map(repo).items() if sha in sha_map for t in names}
    return Result(out, tip, sha_map, tag_map)


# ---------------------------------------------------------------- command line

def _render(plan: Plan) -> str:
    lines = [f"{plan.before} commits -> {plan.after}"]
    for i, g in enumerate(plan.groups, 1):
        fold = f"  (folds {len(g.folded)})" if g.folded else ""
        lines.append(f"{i:3d}. {g.anchor[:8]} {g.anchor_subject}  [{g.reason}]{fold}")
        for sha, subject in g.folded:
            lines.append(f"       - {sha[:8]} {subject}")
    return "\n".join(lines)


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(prog="smart_squash", description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["plan", "apply"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--branch", default=None, help="branch to squash (default: current)")
    ap.add_argument("--base", default=None, help="exclusive lower bound (default: merge-base with default branch)")
    ap.add_argument("--out", default=None, help="output branch (default: <branch>-smart-squash)")
    ap.add_argument("--allow-default", action="store_true", help="allow planning the default branch")
    ap.add_argument("--large-lines", type=int, default=Config.large_lines)
    ap.add_argument("--no-runtime-anchor", action="store_true", help="free-form commits touching .tf are noise")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    cfg = Config(large_lines=a.large_lines, runtime_tf_is_anchor=not a.no_runtime_anchor)
    try:
        branch = a.branch or _git(repo, "branch", "--show-current").strip()
        base, _ = resolve_range(repo, branch, a.base, a.allow_default)
        plan = build_plan(read_commits(repo, base, branch), cfg)
        if a.command == "plan":
            if a.json:
                print(json.dumps({"before": plan.before, "after": plan.after,
                                  "groups": [g.__dict__ for g in plan.groups]}, indent=2))
            else:
                print(_render(plan))
            return 0
        res = apply_plan(repo, plan, branch, base, a.out)
        mapdir = Path(_git(repo, "rev-parse", "--absolute-git-dir").strip()) / "smart-squash"
        mapdir.mkdir(exist_ok=True)
        mapfile = mapdir / f"{res.branch}.json"
        mapfile.write_text(json.dumps({"source": branch, "branch": res.branch, "tip": res.tip,
                                       "sha_map": res.sha_map,
                                       "tag_map": {k: list(v) for k, v in res.tag_map.items()}}, indent=2))
        print(f"created {res.branch} ({plan.before} -> {plan.after} commits), tree identical to {branch}")
        print(f"sha map: {mapfile}")
        if res.tag_map:
            print(f"{len(res.tag_map)} tag(s) point at old commits; tags were NOT moved (see sha map)")
        return 0
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except (RuntimeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
