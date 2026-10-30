# pyright: reportMissingImports=false
"""Unit tests for Diff Lens (Spec Unit 1 & Step 5)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from understand_lenses.diff import compute_diff_focus


def test_diff_lens_includes_uncommitted_work(git_repo):
    """Diff report includes uncommitted work in the current working tree."""
    new_file = git_repo / "src" / "new.ts"
    new_file.write_text("console.log('uncommitted change');\n", encoding="utf-8")

    focus = compute_diff_focus(git_repo, base_ref="main")

    assert "src/new.ts" in focus.focus_set


def test_diff_lens_excludes_changes_only_on_base_branch(git_repo):
    """Diff report excludes changes made only on the base branch after split point."""
    # Add other.ts in initial commit on main
    other_file = git_repo / "src" / "other.ts"
    other_file.write_text("console.log('original other.ts');\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "add other.ts on main"], cwd=git_repo, check=True)

    # Create feature branch from current commit
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=git_repo, check=True, capture_output=True)

    # Switch back to main and commit modification to other.ts
    subprocess.run(["git", "checkout", "main"], cwd=git_repo, check=True, capture_output=True)
    other_file.write_text("console.log('modified other.ts only on main');\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "change other.ts on main"], cwd=git_repo, check=True)

    # Switch back to feature branch where other.ts was never changed
    subprocess.run(["git", "checkout", "feature"], cwd=git_repo, check=True, capture_output=True)

    # Compute diff against main
    focus = compute_diff_focus(git_repo, base_ref="main")

    assert "src/other.ts" not in focus.focus_set
