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


def get_main_worktree_root(repo_root: Path) -> Path:
    """Root of the main checkout, so every linked worktree of a repo maps to the same store.

    Falls back to repo_root outside git and when the common git dir is not a `.git`
    directory (submodules, bare repos), where its parent is not a worktree root.
    """
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            common_dir = (repo_root / res.stdout.strip()).resolve()
            if common_dir.name == ".git":
                return common_dir.parent
    except OSError:
        pass
    return repo_root.resolve()


def get_repo_slug(repo_root: Path) -> str:
    """Derives a safe filesystem directory slug for the repository (shared by its worktrees), matching todo-navigator."""
    raw = (
        str(get_main_worktree_root(repo_root))
        .strip("/")
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
    )
    return re.sub(r"-+", "-", raw) or "default-repo"
