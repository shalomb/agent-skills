# pyright: reportMissingImports=false
"""Unit tests for runner integration with lenses (Step 5)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from understand_runs.runner import Lens, run_report


def test_run_report_with_lens_topic(temp_cache, non_git_dir):
    """run_report accepts --lens topic and executes topic lens."""
    result = run_report(non_git_dir, lens="--lens topic onboarding")
    assert result.lens == Lens("topic", "onboarding")
    assert (result.run_dir / "report.html").exists()


def test_run_report_with_lens_diff(temp_cache, git_repo):
    """run_report accepts --lens diff and executes diff lens with focus set."""
    new_file = git_repo / "src" / "new.ts"
    new_file.write_text("console.log('uncommitted');\n", encoding="utf-8")

    result = run_report(git_repo, lens="--lens diff main")
    assert result.lens == Lens("diff", "main")
    assert "src/new.ts" in result.focus_set
    assert (result.run_dir / "report.html").exists()


def test_run_report_with_lens_pr(temp_cache, git_repo):
    """run_report accepts --lens pr and executes pr lens in detached worktree."""
    # Commit change on pr branch
    subprocess.run(["git", "checkout", "-b", "pr-test-branch"], cwd=git_repo, check=True, capture_output=True)
    (git_repo / "src" / "app.ts").write_text("console.log('pr branch version');\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "pr commit"], cwd=git_repo, check=True)
    head_oid = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=git_repo, text=True).strip()
    subprocess.run(["git", "checkout", "main"], cwd=git_repo, check=True, capture_output=True)

    with patch("understand_lenses.pr.fetch_pr_metadata") as mock_fetch:
        mock_fetch.return_value = {
            "title": "PR 123",
            "body": "Test body",
            "files": [{"path": "src/app.ts"}],
            "baseRefOid": "b1",
            "headRefOid": head_oid,
        }
        result = run_report(git_repo, lens="--lens pr 123")
        assert result.lens == Lens("pr", "123")
        assert "src/app.ts" in result.focus_set

        # Verify main branch stayed active in git_repo
        active_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=git_repo, text=True).strip()
        assert active_branch == "main"
