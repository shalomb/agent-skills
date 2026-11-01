"""Read-only access to /goal files: `<store>/goals/<branch_slug>.md`.

Only `/goal` writes these files; todo reads the `id` and `status` front-matter keys.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Optional

from todo_navigator.parser import get_shadow_dir


def current_branch(repo_root: Path) -> Optional[str]:
    """Current branch name, or None on a detached HEAD or outside git."""
    res = subprocess.run(
        ["git", "-C", str(repo_root), "symbolic-ref", "--short", "-q", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return res.stdout.strip() or None if res.returncode == 0 else None


def read_front_matter(path: Path) -> Dict[str, str]:
    """Top-level `key: value` pairs of a leading `---` front-matter block (nested keys are ignored)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: Dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line or line[0] in " \t#" or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.split(" #", 1)[0].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return {}


def current_goal(repo_root: Path) -> Optional[Dict[str, str]]:
    """{"id", "status"} of the goal file for the current branch, or None when there is none."""
    branch = current_branch(repo_root)
    if not branch:
        return None
    goal_file = get_shadow_dir(repo_root) / "goals" / f"{branch.replace('/', '-')}.md"
    if not goal_file.is_file():
        return None
    fields = read_front_matter(goal_file)
    if not fields.get("id"):
        return None
    return {"id": fields["id"], "status": fields.get("status", "")}


def active_goal_id(repo_root: Path) -> str:
    """Id of the current branch's goal when its status is `active`, else ''."""
    goal = current_goal(repo_root)
    return goal["id"] if goal and goal["status"] == "active" else ""
