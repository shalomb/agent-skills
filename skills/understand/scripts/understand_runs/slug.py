"""Derives repo slug matching todo-navigator, and detects repository roots."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def is_git_repo(path: Path | None = None) -> bool:
    """Returns True if the path lies within a git worktree."""
    target = (path or Path.cwd()).resolve()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except (subprocess.SubprocessError, OSError):
        return False


def get_repo_root(cwd: Path | None = None) -> Path:
    """Finds the root of the current git repository, or falls back to cwd."""
    target = (cwd or Path.cwd()).resolve()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return Path(res.stdout.strip()).resolve()
    except (subprocess.SubprocessError, OSError):
        pass
    return target


def get_repo_slug(repo_root: Path) -> str:
    """Derives a safe filesystem directory slug for the repository matching todo-navigator."""
    raw = (
        str(repo_root.resolve())
        .strip("/")
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
    )
    return re.sub(r"-+", "-", raw) or "default-repo"
