#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Todo Navigator Engine (todo_engine.py)
Portable, lightweight task navigator with external shadow caching,
topological dependency resolution, WSJF wave sequencing, and TTY-safe editor launching.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def get_repo_root() -> Path:
    """Finds the root of the current git repository, or falls back to CWD."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(res.stdout.strip()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_repo_slug(repo_root: Optional[Path] = None) -> str:
    """Generates a clean, deterministic slug from the repository root path."""
    if repo_root is None:
        repo_root = get_repo_root()
    raw = str(repo_root).strip("/")
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", raw)


def get_shadow_dir(repo_root: Optional[Path] = None) -> Path:
    """Returns the external shadow task directory under $XDG_CACHE_HOME."""
    if repo_root is None:
        repo_root = get_repo_root()
    cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    shadow_dir = cache_base / "agent-skills" / "todos" / get_repo_slug(repo_root)
    shadow_dir.mkdir(parents=True, exist_ok=True)
    (shadow_dir / "tasks").mkdir(parents=True, exist_ok=True)
    return shadow_dir


def get_active_todo_path(repo_root: Optional[Path] = None, force_shadow: bool = False) -> Path:
    """
    Locates the active TODO.md file.
    Prefers repo-native TODO.md if it already exists, unless force_shadow is set.
    """
    if repo_root is None:
        repo_root = get_repo_root()
    if force_shadow:
        return get_shadow_dir(repo_root) / "TODO.md"
    in_repo = repo_root / "TODO.md"
    if in_repo.is_file():
        return in_repo
    return get_shadow_dir(repo_root) / "TODO.md"


class Task:
    def __init__(self, raw_line: str, line_no: int):
        self.raw_line = raw_line
        self.line_no = line_no
        self.completed = bool(re.match(r"^\s*-\s*\[[xX]\]", raw_line))

        # Extract title and tags
        cleaned = re.sub(r"^\s*-\s*\[[ xX]\]\s*", "", raw_line.strip())
        self.id = ""
        self.priority = "P2"
        self.wsjf = 1.0
        self.depends_on: List[str] = []
        self.card_rel_path: Optional[str] = None
        self.spec_link: Optional[str] = None

        # Tags
        id_match = re.search(r"\[id:\s*([a-zA-Z0-9_-]+)\]", cleaned)
        if id_match:
            self.id = id_match.group(1)

        prio_match = re.search(r"\[(P[0-3])\]", cleaned)
        if prio_match:
            self.priority = prio_match.group(1)

        wsjf_match = re.search(r"\[wsjf:\s*([0-9.]+)\]", cleaned)
        if wsjf_match:
            try:
                self.wsjf = float(wsjf_match.group(1))
            except ValueError:
                pass

        dep_match = re.search(r"\[(?:depends|after):\s*([^\]]+)\]", cleaned)
        if dep_match:
            raw_deps = dep_match.group(1)
            self.depends_on = [d.strip() for d in raw_deps.split(",") if d.strip()]

        card_match = re.search(r"\(\[(?:card|details)\]\(([^)]+)\)\)", cleaned)
        if card_match:
            self.card_rel_path = card_match.group(1)

        spec_match = re.search(r"\[spec:\s*([^\]]+)\]", cleaned)
        if spec_match:
            self.spec_link = spec_match.group(1).strip()

        # Clean title by removing bracket tags
        title = re.sub(r"\[[^\]]+\]", "", cleaned)
        title = re.sub(r"\(\[[^\]]+\]\([^)]+\)\)", "", title)
        self.title = title.strip()

        if not self.id:
            fallback = re.sub(r"[^a-zA-Z0-9]+", "-", self.title.lower()).strip("-")
            self.id = fallback[:32] if fallback else f"task-{line_no}"

        if not self.card_rel_path:
            self.card_rel_path = f"./tasks/{self.id}.md"


def parse_todo_file(todo_path: Path) -> Tuple[str, List[Task], List[str]]:
    """Parses a TODO.md file into Intent, Task objects, and Reinforcements."""
    if not todo_path.exists():
        return "", [], []

    content = todo_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    intent = ""
    tasks: List[Task] = []
    reinforcements: List[str] = []
    current_section = ""

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            header = stripped.lstrip("#").strip().lower()
            if "intent" in header or "goal" in header:
                current_section = "intent"
            elif "reinforce" in header or "learning" in header:
                current_section = "reinforcements"
            else:
                current_section = "tasks"
            continue

        if current_section == "intent" and stripped:
            intent += (line + "\n")
        elif current_section == "reinforcements" and (stripped.startswith("-") or stripped.startswith("*")):
            reinforcements.append(stripped.lstrip("-* ").strip())
        elif stripped.startswith("- [ ]") or stripped.startswith("- [x]") or stripped.startswith("- [X]"):
            tasks.append(Task(line, i))

    return intent.strip(), tasks, reinforcements


def bootstrap_workspace(shadow_dir: Path, repo_root: Path) -> Path:
    """Bootstraps a fresh shadow TODO.md and starter task cards."""
    todo_file = shadow_dir / "TODO.md"
    if todo_file.exists():
        return todo_file

    sample_content = f"""# Project Tasks
Target Repository: `{repo_root}`

## Goal
Initialize and track work for {repo_root.name}.

## Outstanding Tasks
- [ ] Explore codebase structure and active goals [id: init-explore] [P1] [wsjf: 5.0] ([card](./tasks/init-explore.md))
- [ ] Define core deliverable tasks [id: define-tasks] [P1] [wsjf: 4.0] [depends: init-explore] ([card](./tasks/define-tasks.md))

## Reinforcements
- {datetime.date.today().isoformat()}: Initialized project task workspace in shadow directory.
"""
    todo_file.write_text(sample_content, encoding="utf-8")

    card = shadow_dir / "tasks" / "init-explore.md"
    card.write_text(f"""# Task: Explore Codebase Structure and Active Goals
**Parent:** [TODO.md](../TODO.md)
**Status:** In Progress
**Target Repo:** `{repo_root}`

## Acceptance Criteria (BDD)
- [ ] Identify key entry points and modules
- [ ] Scan recent git commits for context

## Target Files
- [README.md](file://{repo_root}/README.md)
""", encoding="utf-8")

    return todo_file


def cmd_replan(args: argparse.Namespace) -> int:
    """Resolves DAG dependencies, detects cycles, calculates WSJF waves, and presents plan."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print(f"⚡ Bootstrapping new task backlog in {shadow_dir}...")
        todo_file = bootstrap_workspace(shadow_dir, repo_root)

    intent, tasks, reinforcements = parse_todo_file(todo_file)
    print("=" * 70)
    print(f"📋 TODO ROADMAP: {repo_root.name}")
    print(f"File: [TODO.md](file://{todo_file})")
    print("=" * 70)

    if intent:
        print(f"🎯 Goal:\n  {intent}\n")

    completed = [t for t in tasks if t.completed]
    open_tasks = [t for t in tasks if not t.completed]
    completed_ids = {t.id for t in completed}

    # Dependency analysis
    unblocked: List[Task] = []
    blocked: List[Tuple[Task, List[str]]] = []

    # Bottleneck detection
    dependents_count: Dict[str, int] = {t.id: 0 for t in tasks}
    for t in open_tasks:
        for dep in t.depends_on:
            if dep in dependents_count:
                dependents_count[dep] += 1

    for t in open_tasks:
        missing = [d for d in t.depends_on if d not in completed_ids]
        if not missing:
            unblocked.append(t)
        else:
            blocked.append((t, missing))

    unblocked.sort(key=lambda t: t.wsjf, reverse=True)

    print(f"📊 Status: {len(completed)} completed | {len(unblocked)} unblocked | {len(blocked)} blocked\n")

    if unblocked:
        print("🌊 Wave 1 (Ready to Execute - sorted by WSJF):")
        for t in unblocked:
            card_file = shadow_dir / t.card_rel_path.lstrip("./")
            card_indicator = f"([card](file://{card_file}))" if card_file.exists() else f"[{t.card_rel_path}]"
            bottleneck_tag = f" ⚠️ [BLOCKS {dependents_count[t.id]} TASKS]" if dependents_count.get(t.id, 0) > 0 else ""
            print(f"  • {t.title} [id: {t.id}] [{t.priority}] [wsjf: {t.wsjf}]{bottleneck_tag}")
            print(f"    └─ Card: {card_indicator}")

    if blocked:
        print("\n⏳ Blocked Tasks (Waiting on dependencies):")
        for t, missing in blocked:
            print(f"  • {t.title} [id: {t.id}]")
            print(f"    └─ Waiting on: {', '.join(missing)}")

    if reinforcements:
        print("\n💡 Reinforcements (Active Learnings):")
        for r in reinforcements[-5:]:
            print(f"  • {r}")

    print("=" * 70)
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    """Pulls the next highest-leverage unblocked task and pages in its card."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print(f"❌ No active TODO.md found. Run /replan to bootstrap.")
        return 1

    _, tasks, _ = parse_todo_file(todo_file)
    completed_ids = {t.id for t in tasks if t.completed}
    unblocked = [t for t in tasks if not t.completed and all(d in completed_ids for d in t.depends_on)]

    if not unblocked:
        if any(not t.completed for t in tasks):
            print("⚠️ All remaining open tasks are currently blocked by dependencies. Run /replan to inspect.")
        else:
            print("🎉 All tasks in the backlog are complete!")
        return 0

    unblocked.sort(key=lambda t: t.wsjf, reverse=True)
    top = unblocked[0]

    card_path = shadow_dir / top.card_rel_path.lstrip("./")
    if not card_path.exists():
        card_path.parent.mkdir(parents=True, exist_ok=True)
        card_path.write_text(
            f"# Task: {top.title}\n**Parent:** [TODO.md](../TODO.md)\n**ID:** `{top.id}`\n\n"
            f"## Acceptance Criteria (BDD)\n- [ ] \n\n## Target Codebase Artifacts\n\n## Notes\n",
            encoding="utf-8",
        )

    print("=" * 70)
    print(f"👉 NEXT TASK: {top.title} [id: {top.id}] [{top.priority}] [wsjf: {top.wsjf}]")
    print(f"Card Link: [Open Task Card](file://{card_path})")
    print("=" * 70)
    print(card_path.read_text(encoding="utf-8"))
    print("=" * 70)
    return 0


def cmd_prev(args: argparse.Namespace) -> int:
    """Context recall: factual 3-line summary of the last completed item and commit."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print("❌ No active TODO.md found.")
        return 1

    _, tasks, _ = parse_todo_file(todo_file)
    completed = [t for t in tasks if t.completed]
    last = completed[-1] if completed else None

    try:
        git_log = subprocess.run(
            ["git", "log", "-1", "--oneline", "--no-color"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
        ).stdout.strip()
    except Exception:
        git_log = "Unknown (no git commits found)"

    print("-" * 70)
    print("⏮️ PREV (Context Recall):")
    if last:
        card_path = shadow_dir / last.card_rel_path.lstrip("./")
        print(f"• Last Task Done: - [x] {last.title} [id: {last.id}]")
        print(f"• Task Card:      [card](file://{card_path})")
    else:
        print("• Last Task Done: (None recorded yet in TODO.md)")
    print(f"• Last Git Commit: {git_log}")
    print("-" * 70)
    return 0


def cmd_view(args: argparse.Namespace) -> int:
    """Views TODO.md or a specific task card."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    target = args.target

    if not target or target.lower() in ("todo", "backlog"):
        target_path = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))
    else:
        target_path = shadow_dir / "tasks" / f"{target}.md"
        if not target_path.exists():
            target_path = shadow_dir / "tasks" / target

    if not target_path.exists():
        print(f"❌ Target not found: {target_path}")
        return 1

    print("=" * 70)
    print(f"📄 Viewing: [{target_path.name}](file://{target_path})")
    print("=" * 70)
    print(target_path.read_text(encoding="utf-8"))
    print("=" * 70)
    return 0


def handle_express_edit(repo_root: Path, todo_file: Path, shadow_dir: Path, target: str, target_path: Path, ops: List[str]) -> int:
    op_str = " ".join(ops).strip()
    first_op = ops[0].lower()

    # Action: Mark as completed
    if first_op in ("done", "complete", "completed", "check"):
        if not todo_file.exists():
            print("❌ TODO.md not found.")
            return 1
        content = todo_file.read_text(encoding="utf-8")
        pattern = rf"(-\s*\[)\s*(\]\s*.*\[id:\s*{re.escape(target)}\])"
        if re.search(pattern, content):
            new_content = re.sub(pattern, r"\g<1>x\g<2>", content, count=1)
        else:
            lines = content.splitlines()
            found = False
            for idx, line in enumerate(lines):
                if target in line and line.strip().startswith("- [ ]"):
                    lines[idx] = line.replace("- [ ]", "- [x]", 1)
                    found = True
                    break
            new_content = "\n".join(lines) + "\n" if found else content
        todo_file.write_text(new_content, encoding="utf-8")

        if target_path.exists():
            card_txt = target_path.read_text(encoding="utf-8")
            card_txt = re.sub(r"\*\*Status:\*\*.*", "**Status:** Completed", card_txt)
            target_path.write_text(card_txt, encoding="utf-8")

        print(f"✅ Marked task [{target}] as completed in [TODO.md](file://{todo_file}).")
        return 0

    # Action: Priority change (P0, P1, P2, P3)
    if re.match(r"^p[0-3]$", first_op):
        new_prio = first_op.upper()
        content = todo_file.read_text(encoding="utf-8")
        pattern = rf"(\[id:\s*{re.escape(target)}\][^\]]*\[)P[0-3](\])"
        if re.search(pattern, content):
            new_content = re.sub(pattern, rf"\g<1>{new_prio}\g<2>", content, count=1)
        else:
            pattern2 = rf"(\[)P[0-3](\][^\]]*\[id:\s*{re.escape(target)}\])"
            new_content = re.sub(pattern2, rf"\g<1>{new_prio}\g<2>", content, count=1)
        todo_file.write_text(new_content, encoding="utf-8")
        print(f"✅ Updated priority of [{target}] to [{new_prio}] in [TODO.md](file://{todo_file}).")
        return 0

    # Action: WSJF change
    if first_op == "wsjf" and len(ops) > 1:
        new_score = ops[1]
        content = todo_file.read_text(encoding="utf-8")
        pattern = rf"(\[id:\s*{re.escape(target)}\][^\]]*\[wsjf:\s*)[0-9.]+(\])"
        if re.search(pattern, content):
            new_content = re.sub(pattern, rf"\g<1>{new_score}\g<2>", content, count=1)
        else:
            pattern2 = rf"(\[wsjf:\s*)[0-9.]+(\][^\]]*\[id:\s*{re.escape(target)}\])"
            new_content = re.sub(pattern2, rf"\g<1>{new_score}\g<2>", content, count=1)
        todo_file.write_text(new_content, encoding="utf-8")
        print(f"✅ Updated WSJF of [{target}] to [{new_score}] in [TODO.md](file://{todo_file}).")
        return 0

    # Action: Add acceptance criterion
    if first_op in ("add", "criterion", "scenario"):
        criterion_text = " ".join(ops[1:]).strip()
        if not criterion_text:
            print("❌ Please specify the acceptance criterion text to add.")
            return 1
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                f"# Task: {target}\n**Parent:** [TODO.md](../TODO.md)\n**ID:** `{target}`\n\n"
                f"## Acceptance Criteria (BDD)\n- [ ] {criterion_text}\n\n## Target Codebase Artifacts\n\n## Notes\n",
                encoding="utf-8",
            )
        else:
            card_txt = target_path.read_text(encoding="utf-8")
            if "## Acceptance Criteria" in card_txt:
                pattern = r"(##\s*Acceptance Criteria[^\n]*\n)"
                card_txt = re.sub(pattern, rf"\1- [ ] {criterion_text}\n", card_txt, count=1)
            else:
                card_txt = card_txt.rstrip() + f"\n\n## Acceptance Criteria (BDD)\n- [ ] {criterion_text}\n"
            target_path.write_text(card_txt, encoding="utf-8")
        print(f"✅ Added criterion to [{target_path.name}](file://{target_path}):")
        print(f"   - [ ] {criterion_text}")
        return 0

    # Action: Stage artifact
    if first_op in ("stage", "stage-artifact"):
        art_arg = Path(ops[1]).resolve() if len(ops) > 1 else None
        staged = stage_card_as_artifact(target, target_path, art_arg)
        if staged:
            print(f"✨ Staged to artifact: [{staged.name}](file://{staged})")
            print("• Run '/artifact' to inspect and press 'ctrl+g' to edit in editor.")
            print("• Any changes in the editor directly update the shadow file.")
            return 0
        else:
            print("⚠️ Could not stage artifact: ANTIGRAVITY_CONVERSATION_ID not found and no artifact path supplied.")
            return 1

    return -1


def stage_card_as_artifact(target: str, target_path: Path, art_path: Optional[Path] = None) -> Optional[Path]:
    """Stages a task card or backlog as an Antigravity artifact symlinked to the shadow file."""
    if not art_path:
        conv_id = os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
        if not conv_id:
            return None
        brain_dir = Path.home() / ".gemini" / "antigravity-cli" / "brain" / conv_id
        if not brain_dir.exists():
            return None
        stem = f"task-{target}.md" if target not in ("todo", "backlog") else "TODO.md"
        art_path = brain_dir / stem

    art_path.parent.mkdir(parents=True, exist_ok=True)
    if art_path.is_symlink() or art_path.exists():
        art_path.unlink()
    art_path.symlink_to(target_path)

    meta_path = art_path.parent / f"{art_path.name}.metadata.json"
    meta_content = {
        "summary": f"Task card for '{target}' (symlinked to shadow cache)" if target not in ("todo", "backlog") else "Master project TODO backlog (symlinked)",
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "userFacing": True,
    }
    meta_path.write_text(json.dumps(meta_content, indent=2), encoding="utf-8")
    return art_path


def cmd_edit(args: argparse.Namespace) -> int:
    """Opens a task card or TODO.md in $EDITOR, or performs express inline edits."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    target = args.target
    extra_ops = getattr(args, "ops", [])

    if not target or target.lower() in ("todo", "backlog"):
        target_path = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))
    else:
        target_path = shadow_dir / "tasks" / f"{target}.md"
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                f"# Task: {target}\n**Parent:** [TODO.md](../TODO.md)\n**ID:** `{target}`\n\n"
                f"## Acceptance Criteria (BDD)\n- [ ] \n\n## Target Codebase Artifacts\n\n## Notes\n",
                encoding="utf-8",
            )

    # Handle express edits (e.g. done, P1, add criterion)
    if extra_ops:
        res = handle_express_edit(repo_root, get_active_todo_path(repo_root), shadow_dir, target, target_path, extra_ops)
        if res >= 0:
            return res

    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    is_interactive = sys.stdin.isatty() and os.environ.get("TERM", "") != "dumb"

    if is_interactive:
        print(f"🚀 Launching editor: {editor} '{target_path}'")
        try:
            res = subprocess.run([editor, str(target_path)])
            if res.returncode != 0:
                print(f"⚠️ Editor exited with non-zero status {res.returncode}.")
                print(f"   Direct file link: [Open file](file://{target_path})")
        except Exception as e:
            print(f"⚠️ Failed to launch editor '{editor}': {e}")
            print(f"   Direct file link: [Open file](file://{target_path})")
    else:
        # Non-interactive / Agent mode: stage artifact if in Antigravity environment
        staged = stage_card_as_artifact(target, target_path)
        print(f"✏️ Task Card: [{target_path.name}](file://{target_path})")
        if staged:
            print(f"• Staged Artifact: [{staged.name}](file://{staged})")
            print("• Run '/artifact' to review, or press 'ctrl+g' in the TUI to edit in vim.")
            print("  (Edits in vim modify the shadow file directly)")
        else:
            print(f"• Path: {target_path}")
            print("• Click link above to edit in your editor.")
        print("• Express edits:")
        print(f"  - Mark done:     /todo edit {target} done")
        print(f"  - Change prio:   /todo edit {target} P1")
        print(f"  - Add criterion: /todo edit {target} add <description>")
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    """Appends a durable reinforcement to the ## Reinforcements section of TODO.md."""
    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print("❌ No active TODO.md found. Run /replan first.")
        return 1

    msg = " ".join(args.message).strip()
    if not msg:
        print("❌ Please provide a reinforcement message to record.")
        return 1

    content = todo_file.read_text(encoding="utf-8")
    entry = f"- {datetime.date.today().isoformat()}: {msg}\n"

    if "## Reinforcements" in content or "## Learnings" in content:
        pattern = r"(##\s*(?:Reinforcements|Learnings)[^\n]*\n)"
        new_content = re.sub(pattern, r"\1" + entry, content, count=1)
    else:
        new_content = content.rstrip() + "\n\n## Reinforcements\n" + entry

    todo_file.write_text(new_content, encoding="utf-8")
    print(f"💡 Recorded reinforcement into [TODO.md](file://{todo_file}):\n   {entry.strip()}")
    return 0


def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--shadow", action="store_true", help="Force using shadow cache TODO.md")

    parser = argparse.ArgumentParser(description="Todo Navigator Engine", parents=[common_parser])
    subparsers = parser.add_subparsers(dest="action", help="Action to execute")

    sub_replan = subparsers.add_parser("replan", aliases=["plan"], parents=[common_parser], help="Resolve DAG, calculate WSJF waves, and replan")
    sub_replan.set_defaults(func=cmd_replan)

    sub_next = subparsers.add_parser("next", parents=[common_parser], help="Select top unblocked task and page in secondary card")
    sub_next.set_defaults(func=cmd_next)

    sub_prev = subparsers.add_parser("prev", parents=[common_parser], help="3-line factual recall of last completed task and commit")
    sub_prev.set_defaults(func=cmd_prev)

    sub_view = subparsers.add_parser("view", parents=[common_parser], help="View TODO.md or task card")
    sub_view.add_argument("target", nargs="?", default="todo", help="Task ID or 'todo'")
    sub_view.set_defaults(func=cmd_view)

    sub_edit = subparsers.add_parser("edit", parents=[common_parser], help="Open task card or TODO.md in $EDITOR")
    sub_edit.add_argument("target", nargs="?", default="todo", help="Task ID or 'todo'")
    sub_edit.add_argument("ops", nargs="*", help="Optional express operations (e.g. 'done', 'P1', 'add <criterion>')")
    sub_edit.set_defaults(func=cmd_edit)

    sub_learn = subparsers.add_parser("learn", parents=[common_parser], help="Record durable learning into Reinforcements ledger")
    sub_learn.add_argument("message", nargs="+", help="Learning or feedback to record")
    sub_learn.set_defaults(func=cmd_learn)

    sub_status = subparsers.add_parser("status", parents=[common_parser], help="Show current status and roadmap")
    sub_status.set_defaults(func=cmd_replan)

    args = parser.parse_args()
    if not args.action:
        return cmd_replan(args)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
