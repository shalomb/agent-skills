# pyright: reportMissingImports=false
"""Diff lens: merge-base analysis against working tree with uncommitted work (Spec Unit 1 & Step 5)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .models import LensFocus


def get_merge_base(repo_path: Path, base_ref: str, head_ref: str = "HEAD") -> str:
    """Computes merge-base between base_ref and head_ref."""
    res = subprocess.run(
        ["git", "merge-base", base_ref, head_ref],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def compute_diff_focus(repo_path: Path, base_ref: str) -> LensFocus:
    """Computes diff focus comparing merge-base(base_ref, HEAD) against working tree."""
    merge_base = get_merge_base(repo_path, base_ref, "HEAD")

    # 1. Tracked changes relative to merge base (including staged and unstaged working tree changes)
    diff_res = subprocess.run(
        ["git", "diff", "--name-only", merge_base],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    diff_files = [f.strip() for f in diff_res.stdout.splitlines() if f.strip()]

    # 2. Untracked uncommitted files in working tree
    untracked_res = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked_files = [f.strip() for f in untracked_res.stdout.splitlines() if f.strip()]

    focus_files = set(diff_files) | set(untracked_files)

    # 3. All tracked and untracked files in the working tree
    all_res = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked_all = [f.strip() for f in all_res.stdout.splitlines() if f.strip()]
    all_files = sorted(set(tracked_all) | set(untracked_files))

    return LensFocus(
        lens_type="diff",
        focus_set=focus_files,
        seed_nodes=focus_files,
        all_files=all_files,
        metadata={"base_ref": base_ref, "merge_base": merge_base},
    )
