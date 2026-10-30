# pyright: reportMissingImports=false
"""Unit tests for PR Lens (Spec Unit 1 & Step 5)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from understand_lenses.pr import (
    cleanup_pr_worktree,
    create_pr_worktree,
    fetch_pr_metadata,
    get_pr_worktree_path,
    pr_worktree_context,
)


def test_pr_metadata_fetches_gh_json(tmp_path):
    """fetch_pr_metadata runs `gh pr view` with expected json fields."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout='{"title": "Test PR", "body": "Desc", "files": [{"path": "src/app.ts"}], "baseRefOid": "b1", "headRefOid": "h1"}'
        )
        data = fetch_pr_metadata(tmp_path, 123)
        assert data["title"] == "Test PR"
        assert data["headRefOid"] == "h1"

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["gh", "pr", "view", "123", "--json", "title,body,files,baseRefOid,headRefOid"]


def test_pr_worktree_lifecycle_creates_and_always_cleans_up(git_repo, temp_cache):
    """Worktree is created detached, does not change main branch, and is removed on failure."""
    # Create PR commit on branch pr-branch
    subprocess.run(["git", "checkout", "-b", "pr-branch"], cwd=git_repo, check=True, capture_output=True)
    app_ts = git_repo / "src" / "app.ts"
    app_ts.write_text("console.log('from pr branch');\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "change in pr"], cwd=git_repo, check=True)
    pr_head_oid = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git_repo, text=True).strip()

    # Switch back to main
    subprocess.run(["git", "checkout", "main"], cwd=git_repo, check=True, capture_output=True)

    # 1. Normal success lifecycle
    wt_path = get_pr_worktree_path(git_repo, 123, base_dir=temp_cache)
    with pr_worktree_context(git_repo, 123, pr_head_oid, base_dir=temp_cache) as wt:
        assert wt.is_dir()
        # Verify user is still on main in git_repo
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=git_repo, text=True).strip()
        assert branch == "main"
        # Code in wt shows PR head
        assert (wt / "src" / "app.ts").read_text(encoding="utf-8") == "console.log('from pr branch');\n"

    # After block: worktree must be removed
    worktrees_out = subprocess.check_output(["git", "worktree", "list"], cwd=git_repo, text=True)
    assert "pr-123" not in worktrees_out
    assert not wt_path.exists()

    # 2. Failure lifecycle: exception raised inside context
    failed_wt_path = get_pr_worktree_path(git_repo, 123, base_dir=temp_cache)
    with pytest.raises(RuntimeError):
        with pr_worktree_context(git_repo, 123, pr_head_oid, base_dir=temp_cache) as failed_wt:
            assert failed_wt.is_dir()
            raise RuntimeError("discovery failed")

    worktrees_out_failed = subprocess.check_output(["git", "worktree", "list"], cwd=git_repo, text=True)
    assert "pr-123" not in worktrees_out_failed
    assert not failed_wt_path.exists()
