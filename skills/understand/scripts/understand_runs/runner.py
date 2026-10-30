# pyright: reportMissingImports=false
"""Report runner executing the plan, discover, converge, and render phases (Spec Units 1 & 4)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import understand_lenses.diff as diff_lens
import understand_lenses.pr as pr_lens
import understand_lenses.topic as topic_lens
from understand_lenses.models import LensFocus
from understand_plan.docs import generate_docs_bundle
from understand_plan.models import Lens
from understand_plan.planner import plan_discovery
from understand_plan.scanner import scan_directory
from understand_render.run import render_run
from understand_runs.slug import get_repo_root, get_repo_slug, is_git_repo
from understand_runs.storage import create_run_dir, normalize_lens
from understand_runs.urls import format_end_message, get_report_urls

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".cache"}


class GitRequiredError(Exception):
    """Raised when a lens requires a git repository but the target directory has none."""


@dataclass(frozen=True)
class ReportResult:
    run_dir: Path
    lens: Lens
    urls: dict[str, str]
    summary: str
    end_message: str
    focus_set: set[str] = field(default_factory=set)
    seed_nodes: set[str] = field(default_factory=set)


def parse_command(command_or_args: str) -> Lens:
    """Parses a slash command, CLI flag, or arguments into a Lens."""
    text = command_or_args.strip()
    if text.startswith("--lens"):
        text = text[len("--lens") :].strip()
        if text.startswith("="):
            text = text[1:].strip()
    if text.startswith("/understand-pr"):
        arg = text[len("/understand-pr") :].strip()
        return Lens("pr", arg or None)
    if text.startswith("/understand-diff"):
        arg = text[len("/understand-diff") :].strip()
        return Lens("diff", arg or None)
    if text.startswith("/understand"):
        text = text[len("/understand") :].strip()

    if not text:
        return Lens("full")

    parts = text.split(maxsplit=1)
    sub = parts[0]
    rest = parts[1].strip() if len(parts) > 1 else ""

    if sub == "pr":
        return Lens("pr", rest or None)
    if sub == "diff":
        return Lens("diff", rest or None)
    if sub == "full":
        return Lens("full")
    if sub == "topic":
        return Lens("topic", rest or None)
    return Lens("topic", text)


def _scan_files_and_folders(root: Path) -> tuple[list[str], list[str]]:
    """Discovers files and folders under root without modifying anything."""
    files: list[str] = []
    folders: list[str] = []
    for current, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        curr_p = Path(current)
        try:
            rel = curr_p.relative_to(root)
            if str(rel) != ".":
                folders.append(str(rel))
        except ValueError:
            continue
        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            fpath = curr_p / fname
            try:
                rel_f = fpath.relative_to(root)
                files.append(str(rel_f))
            except ValueError:
                continue
    return sorted(folders), sorted(files)


def _create_bundle(
    bundle_dir: Path,
    repo_path: Path,
    lens: Lens,
    folders: list[str],
    files: list[str],
    focus_set: set[str] | None = None,
    seed_nodes: set[str] | None = None,
    edges: list[tuple[str, str]] | None = None,
) -> str:
    """Writes a minimal schema-compliant bundle for the repository and lens."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = bundle_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    nodes = []
    for f in files:
        dimmed = (focus_set is not None and f not in focus_set)
        nodes.append({
            "anchor_id": f,
            "label": Path(f).name,
            "path": f,
            "kind": "file",
            "summary": f"File {f}",
            "dimmed": dimmed,
        })
    if not nodes:
        nodes.append({
            "anchor_id": "root",
            "label": repo_path.name or "root",
            "path": "",
            "kind": "folder",
            "summary": "Root folder",
            "dimmed": False,
        })

    graph_edges = []
    if edges:
        valid_files = set(files)
        for s, t in edges:
            if s in valid_files and t in valid_files:
                graph_edges.append({
                    "source": s,
                    "target": t,
                    "kind": "uses",
                })

    graph = {
        "schema_version": 1,
        "title": f"Report: {lens.target or lens.type.capitalize()}",
        "nodes": nodes,
        "edges": graph_edges,
    }
    (bundle_dir / "graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    if lens.type == "topic":
        title = f"Topic: {lens.target}"
        seeds_md = "\n".join(f"- `{s}`" for s in sorted(seed_nodes or [])) if seed_nodes else "- (none)"
        focus_md = "\n".join(f"- `{f}`" for f in sorted(focus_set or [])) if focus_set else "- (none)"
        content = (
            f"# {title}\n\n"
            f"This topic report focuses on **{lens.target}**.\n\n"
            f"### Seed Nodes\n{seeds_md}\n\n"
            f"### Focus Set (Seeds + 1-hop neighbours)\n{focus_md}\n\n"
            f"### Files examined\n"
            + "\n".join(f"- `{f}`" for f in files[:30])
        )
        summary = f"Topic report on {lens.target} focusing on {len(focus_set or [])} of {len(files)} files."
    elif lens.type == "diff":
        title = f"Diff: {lens.target}"
        focus_md = "\n".join(f"- `{f}`" for f in sorted(focus_set or [])) if focus_set else "- (clean)"
        content = (
            f"# {title}\n\n"
            f"This diff report focuses on changes against **{lens.target}**.\n\n"
            f"### Changed Files in Focus Set\n{focus_md}\n\n"
            f"### All Files\n"
            + "\n".join(f"- `{f}`" for f in files[:30])
        )
        summary = f"Diff report against {lens.target} focusing on {len(focus_set or [])} changed files."
    elif lens.type == "pr":
        title = f"Pull Request: {lens.target}"
        focus_md = "\n".join(f"- `{f}`" for f in sorted(focus_set or [])) if focus_set else "- (none)"
        content = (
            f"# {title}\n\n"
            f"This pull request report focuses on PR **#{lens.target}**.\n\n"
            f"### Changed Files in Focus Set\n{focus_md}\n\n"
            f"### All Files at Head\n"
            + "\n".join(f"- `{f}`" for f in files[:30])
        )
        summary = f"Pull request report for PR #{lens.target} focusing on {len(focus_set or [])} changed files."
    else:
        title = "Repository Structure"
        folders_list = "\n".join(f"- `{f}/`" for f in folders[:15]) if folders else "- (root only)"
        files_list = "\n".join(f"- `{f}`" for f in files[:30]) if files else "- (empty)"
        content = (
            f"# {title}\n\n"
            f"### Folders\n{folders_list}\n\n"
            f"### Files\n{files_list}\n"
        )
        summary = f"Full overview of {len(files)} files and {len(folders)} folders."

    (sections_dir / "01-overview.md").write_text(content + "\n", encoding="utf-8")
    return summary


def _execute_phases(
    repo_path: Path,
    source_root: Path,
    parsed_lens: Lens,
    on_phase: Callable[[str], None] | None = None,
    commit: str | None = None,
    base_dir: Path | None = None,
    lens_focus: LensFocus | None = None,
) -> ReportResult:
    """Executes the 4 phases: plan, discover, converge, render."""
    # Phase 1: plan
    if on_phase:
        on_phase("plan")
    prescan = scan_directory(source_root)
    plan = plan_discovery(prescan, parsed_lens)

    # Phase 2: discover
    if on_phase:
        on_phase("discover")
    folders, files = _scan_files_and_folders(source_root)

    # Compute or complete lens focus
    focus_set: set[str] = set()
    seed_nodes: set[str] = set()
    edges: list[tuple[str, str]] = []

    if parsed_lens.type == "topic":
        computed = topic_lens.compute_topic_focus(source_root, parsed_lens.target or "", files=files)
        focus_set = computed.focus_set
        seed_nodes = computed.seed_nodes
        edges = computed.metadata.get("edges", [])
    elif parsed_lens.type == "diff":
        if lens_focus is not None:
            focus_set = lens_focus.focus_set
            seed_nodes = lens_focus.seed_nodes
        else:
            computed = diff_lens.compute_diff_focus(source_root, parsed_lens.target or "main")
            focus_set = computed.focus_set
            seed_nodes = computed.seed_nodes
    elif parsed_lens.type == "pr":
        if lens_focus is not None:
            focus_set = lens_focus.focus_set
            seed_nodes = lens_focus.seed_nodes
    else:  # full
        focus_set = set(files)
        seed_nodes = set(files)

    # Phase 3: converge
    if on_phase:
        on_phase("converge")
    temp_bundle_dir = Path(tempfile.mkdtemp(prefix="understand-bundle-"))
    try:
        if plan.profile == "docs":
            summary = generate_docs_bundle(temp_bundle_dir, source_root, parsed_lens, files)
        else:
            summary = _create_bundle(
                temp_bundle_dir,
                source_root,
                parsed_lens,
                folders,
                files,
                focus_set=focus_set if parsed_lens.type != "full" else None,
                seed_nodes=seed_nodes if parsed_lens.type != "full" else None,
                edges=edges,
            )

        # Phase 4: render
        if on_phase:
            on_phase("render")

        repo_root = get_repo_root(repo_path)
        repo_slug = get_repo_slug(repo_root)
        lens_id = normalize_lens(parsed_lens.type, parsed_lens.target)
        run_dir = create_run_dir(
            repo_root,
            lens=parsed_lens.type,
            target=parsed_lens.target,
            commit=commit,
            base_dir=base_dir,
        )

        render_run(
            temp_bundle_dir,
            source_root=source_root,
            out_dir=run_dir,
            mmdc_path="mmdc",
            chromium_path="/usr/bin/chromium-headless-shell",
            log=lambda m: None,
        )

        urls = get_report_urls(repo_slug, lens_id, run_dir.name)
        end_message = format_end_message(repo_slug, lens_id, urls, summary=summary)

        return ReportResult(
            run_dir=run_dir,
            lens=parsed_lens,
            urls=urls,
            summary=summary,
            end_message=end_message,
            focus_set=focus_set,
            seed_nodes=seed_nodes,
        )
    finally:
        shutil.rmtree(temp_bundle_dir, ignore_errors=True)


def run_report(
    repo_path: Path | str,
    lens: Lens | str | None = None,
    target: str | None = None,
    on_phase: Callable[[str], None] | None = None,
    commit: str | None = None,
    base_dir: Path | None = None,
    **kwargs: Any,
) -> ReportResult:
    """Executes a report run through the 4 phases: plan, discover, converge, render.

    Integrates topic, PR, and diff lenses.
    """
    path = Path(repo_path)

    if lens is None:
        parsed_lens = Lens("full")
    elif isinstance(lens, str):
        parsed_lens = parse_command(lens)
        if target:
            parsed_lens = Lens(parsed_lens.type, target)
    else:
        parsed_lens = lens

    # Enforce git requirements
    if parsed_lens.type in ("pr", "diff"):
        if not is_git_repo(path):
            if parsed_lens.type == "pr":
                raise GitRequiredError("A pull request report needs a git repository")
            raise GitRequiredError("A diff report needs a git repository")

    # PR Lens: executes discovery and rendering inside detached worktree
    if parsed_lens.type == "pr":
        pr_number = parsed_lens.target or "1"
        pr_meta = kwargs.get("pr_metadata") or pr_lens.fetch_pr_metadata(path, pr_number)
        head_oid = pr_meta.get("headRefOid", "HEAD")
        lens_focus = pr_lens.compute_pr_focus(path, pr_number, pr_meta)

        with pr_lens.pr_worktree_context(path, pr_number, head_oid, base_dir=base_dir) as wt_dir:
            return _execute_phases(
                repo_path=path,
                source_root=wt_dir,
                parsed_lens=parsed_lens,
                on_phase=on_phase,
                commit=commit,
                base_dir=base_dir,
                lens_focus=lens_focus,
            )

    # Diff Lens: computes diff focus against merge-base
    if parsed_lens.type == "diff":
        base_ref = parsed_lens.target or "main"
        lens_focus = diff_lens.compute_diff_focus(path, base_ref)
        return _execute_phases(
            repo_path=path,
            source_root=path,
            parsed_lens=parsed_lens,
            on_phase=on_phase,
            commit=commit,
            base_dir=base_dir,
            lens_focus=lens_focus,
        )

    # Full and Topic lenses
    return _execute_phases(
        repo_path=path,
        source_root=path,
        parsed_lens=parsed_lens,
        on_phase=on_phase,
        commit=commit,
        base_dir=base_dir,
    )


make_report = run_report

__all__ = [
    "GitRequiredError",
    "Lens",
    "ReportResult",
    "make_report",
    "parse_command",
    "run_report",
]

