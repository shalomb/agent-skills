# pyright: reportMissingImports=false
"""Architecture tests for understand lenses (Spec Architecture tests)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from pathlib import Path

from understand_lenses.pr import create_pr_worktree, fetch_pr_metadata


def test_pr_lens_architecture_uses_gh_pr_view_and_detached_worktree(tmp_path):
    """Architecture rule: Pr lens uses `gh pr view` and a detached worktree (`git worktree add --detach`)."""
    # 1. gh pr view check
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout='{"title": "PR", "files": []}')
        fetch_pr_metadata(tmp_path, "456")
        cmd = mock_run.call_args[0][0]
        assert cmd[:3] == ["gh", "pr", "view"]

    # 2. git worktree add --detach check
    with patch("subprocess.run") as mock_git:
        mock_git.return_value = MagicMock(returncode=0)
        target_wt = tmp_path / "wt" / "pr-456"
        create_pr_worktree(tmp_path, target_wt, "commit-sha-123")
        calls = [c[0][0] for c in mock_git.call_args_list]
        detach_calls = [c for c in calls if c[:3] == ["git", "worktree", "add"] and "--detach" in c]
        assert len(detach_calls) > 0, f"Expected git worktree add --detach call, got {calls}"
