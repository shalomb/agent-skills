"""Editor launcher, Tmux popup manager, express edits, and artifact staging."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def stage_card_as_artifact(target: str, target_path: Path, art_path: Optional[Path] = None) -> Optional[Path]:
    """Stages a task card or TODO.md into Antigravity artifact directory."""
    if not art_path:
        brain_root = Path.home() / ".gemini" / "antigravity-cli" / "brain"
        if not brain_root.exists():
            return None
        recent_convs = sorted(brain_root.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not recent_convs:
            return None
        conv_dir = recent_convs[0]
        if not conv_dir.is_dir():
            return None
        if target.lower() in ("todo", "backlog"):
            art_name = "TODO.md"
        else:
            art_name = f"task-{target}.md"
        art_path = conv_dir / art_name

    try:
        art_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            shutil.copy2(target_path, art_path)
            return art_path
    except Exception:
        pass
    return None


def handle_express_edit(
    repo_root: Path,
    todo_file: Path,
    shadow_dir: Path,
    target: str,
    target_path: Path,
    ops: List[str],
) -> int:
    """Executes non-interactive express modifications to task cards or TODO.md."""
    first_op = ops[0].lower()

    # 1. Mark as completed
    if first_op in ("done", "complete", "completed", "check"):
        if not todo_file.exists():
            print("❌ TODO.md not found.")
            return 1
        content = todo_file.read_text(encoding="utf-8")
        pattern = rf"(-\s*\[)\s*(\]\s*.*\[id:\s*{re.escape(target)}\])"
        if re.search(pattern, content):
            new_content = re.sub(pattern, r"\g<1>x\g<2>", content, count=1)
            todo_file.write_text(new_content, encoding="utf-8")
            print(f"✅ Marked task [{target}] as completed in [{todo_file.name}](file://{todo_file}).")
            return 0
        else:
            print(f"⚠️ Could not find task with [id: {target}] in [{todo_file.name}](file://{todo_file}).")
            return 1

    # 2. Mark as pending / undone
    if first_op in ("undone", "todo", "uncheck", "reopen"):
        if not todo_file.exists():
            print("❌ TODO.md not found.")
            return 1
        content = todo_file.read_text(encoding="utf-8")
        pattern = rf"(-\s*\[)[xX](\]\s*.*\[id:\s*{re.escape(target)}\])"
        if re.search(pattern, content):
            new_content = re.sub(pattern, r"\g<1> \g<2>", content, count=1)
            todo_file.write_text(new_content, encoding="utf-8")
            print(f"✅ Reopened task [{target}] in [{todo_file.name}](file://{todo_file}).")
            return 0
        else:
            print(f"⚠️ Could not find completed task with [id: {target}] in [{todo_file.name}](file://{todo_file}).")
            return 1

    # 3. Update priority (P0, P1, P2, P3)
    if first_op in ("p0", "p1", "p2", "p3"):
        new_prio = first_op.upper()
        if not todo_file.exists():
            print("❌ TODO.md not found.")
            return 1
        content = todo_file.read_text(encoding="utf-8")
        pattern = rf"(\[id:\s*{re.escape(target)}\]\s*\[prio:\s*)([a-zA-Z0-9_-]+)(\])"
        alt_pattern = rf"(\[prio:\s*)([a-zA-Z0-9_-]+)(\]\s*\[id:\s*{re.escape(target)}\])"

        if re.search(pattern, content):
            new_content = re.sub(pattern, rf"\g<1>{new_prio}\g<3>", content, count=1)
        elif re.search(alt_pattern, content):
            new_content = re.sub(alt_pattern, rf"\g<1>{new_prio}\g<3>", content, count=1)
        else:
            print(f"⚠️ Could not find [prio] tag for task [{target}] in [{todo_file.name}](file://{todo_file}).")
            return 1

        todo_file.write_text(new_content, encoding="utf-8")
        print(f"✅ Updated priority for [{target}] to {new_prio} in [{todo_file.name}](file://{todo_file}).")
        return 0

    # 4. Add acceptance criterion to task card
    if first_op == "add":
        criterion_text = " ".join(ops[1:]).strip()
        if not criterion_text:
            print("❌ Error: 'add' requires description text, e.g., /todo edit <target> add Validates token")
            return 1

        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                f"# Task: {target}\n**Parent:** [TODO.md](../TODO.md)\n**ID:** `{target}`\n\n"
                f"## Acceptance Criteria (BDD)\n- [ ] {criterion_text}\n\n## Target Codebase Artifacts\n\n## Notes\n",
                encoding="utf-8",
            )
            print(f"✅ Created [{target_path.name}](file://{target_path}) with criterion:")
            print(f"   - [ ] {criterion_text}")
            return 0

        card_content = target_path.read_text(encoding="utf-8")
        section_pattern = r"(##\s*Acceptance Criteria[^\n]*\n)"
        if re.search(section_pattern, card_content, flags=re.IGNORECASE):
            new_card_content = re.sub(
                section_pattern,
                rf"\g<1>- [ ] {criterion_text}\n",
                card_content,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            new_card_content = card_content + f"\n\n## Acceptance Criteria (BDD)\n- [ ] {criterion_text}\n"

        target_path.write_text(new_card_content, encoding="utf-8")
        print(f"✅ Added criterion to [{target_path.name}](file://{target_path}):")
        print(f"   - [ ] {criterion_text}")
        return 0

    print(f"⚠️ Unrecognized express edit operation: '{first_op}'")
    print("   Supported express ops: done, undone, P0, P1, P2, P3, add <criterion>")
    return 1


def launch_editor(
    repo_root: Path,
    matches: List[Tuple[str, Path]],
    editor: Optional[str] = None,
    no_popup: bool = False,
) -> int:
    """Launches editor in interactive terminal, tmux popup, or falls back gracefully."""
    ed = editor or os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    file_args = [str(cpath) for _, cpath in matches]
    is_interactive = sys.stdin.isatty() and os.environ.get("TERM", "") != "dumb"

    if is_interactive:
        if len(matches) > 1:
            print(f"🚀 Launching editor with {len(matches)} files: {ed} {' '.join(file_args)}")
            print("   (Navigate between files in vim using ':next' and ':prev')")
        else:
            print(f"🚀 Launching editor: {ed} '{file_args[0]}'")
        try:
            res = subprocess.run([ed] + file_args)
            if res.returncode != 0:
                print(f"⚠️ Editor exited with status {res.returncode}.")
            return res.returncode
        except Exception as e:
            print(f"⚠️ Failed to launch editor '{ed}': {e}")
            return 1

    # Tmux popup check
    tmux_socket = os.environ.get("TMUX")
    if tmux_socket and not no_popup:
        if len(matches) == 1:
            title = f" Todo Navigator: {matches[0][0]} "
        else:
            title = f" Todo Navigator: {len(matches)} files (:next / :prev) "

        try:
            cmd = [
                "tmux",
                "display-popup",
                "-E",
                "-d",
                str(repo_root),
                "-w",
                "85%",
                "-h",
                "85%",
                "-T",
                title,
                ed,
            ] + file_args
            res = subprocess.run(cmd)
            if res.returncode == 0:
                links = ", ".join(f"[{p.name}](file://{p})" for _, p in matches)
                print(f"✅ Completed editing {len(matches)} card(s): {links}.")
                for cid, cpath in matches:
                    stage_card_as_artifact(cid, cpath)
                return 0
            else:
                print(f"⚠️ Editor in popup exited with status {res.returncode}")
        except Exception as e:
            print(f"⚠️ Failed to launch tmux popup: {e}")

    # Non-interactive fallback
    for cid, cpath in matches:
        staged = stage_card_as_artifact(cid, cpath)
        print(f"✏️ Task Card: [{cpath.name}](file://{cpath})")
        if staged:
            print(f"• Staged Artifact: [{staged.name}](file://{staged})")
            print("• Run '/artifact' to review, or press 'ctrl+g' in the TUI to edit in vim.")
        else:
            print(f"• Path: {cpath}")
    return 0
