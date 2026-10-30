# pyright: reportMissingImports=false
"""Unit tests for understand_runs report execution and command parsing."""

from pathlib import Path
import pytest
from understand_runs.runner import (
    GitRequiredError,
    Lens,
    make_report,
    parse_command,
)


def test_parse_command_aliases_and_subcommands():
    # Full lens
    assert parse_command("/understand") == Lens("full")
    assert parse_command("/understand ") == Lens("full")

    # Topic lens
    assert parse_command("/understand onboarding") == Lens("topic", "onboarding")

    # PR lens and alias
    assert parse_command("/understand pr 123") == Lens("pr", "123")
    assert parse_command("/understand-pr 123") == Lens("pr", "123")
    assert parse_command("/understand-pr 123") == parse_command("/understand pr 123")

    # Diff lens and alias
    assert parse_command("/understand diff main") == Lens("diff", "main")
    assert parse_command("/understand-diff main") == Lens("diff", "main")
    assert parse_command("/understand-diff main") == parse_command("/understand diff main")


def test_make_report_emits_phases(temp_cache, git_repo):
    phases = []
    result = make_report(git_repo, Lens("full"), on_phase=phases.append)
    assert phases == ["plan", "discover", "converge", "render"]
    assert result.run_dir.exists()
    assert (result.run_dir / "report.html").exists()
    assert "parallels" in result.urls
    assert "tailnet" in result.urls


def test_non_git_dir_pr_and_diff_fail(non_git_dir):
    with pytest.raises(GitRequiredError) as exc_info:
        make_report(non_git_dir, Lens("pr", "1"))
    assert "needs a git repository" in str(exc_info.value).lower()

    with pytest.raises(GitRequiredError) as exc_diff:
        make_report(non_git_dir, Lens("diff", "main"))
    assert "needs a git repository" in str(exc_diff.value).lower()


def test_non_git_dir_full_and_topic_succeed(temp_cache, non_git_dir):
    full_res = make_report(non_git_dir, Lens("full"))
    assert full_res.run_dir.exists()
    report_html = (full_res.run_dir / "report.html").read_text(encoding="utf-8")
    assert "README.md" in report_html or "docs" in report_html

    topic_res = make_report(non_git_dir, Lens("topic", "onboarding"))
    assert topic_res.run_dir.exists()
    topic_html = (topic_res.run_dir / "report.html").read_text(encoding="utf-8")
    assert "onboarding" in topic_html.lower()
    assert "git history" not in topic_html.lower()


def test_run_leaves_uncommitted_work_as_it_was(temp_cache, git_repo):
    app_ts = git_repo / "src" / "app.ts"
    uncommitted_content = "// modified uncommitted content\nconsole.log('in-flight change');\n"
    app_ts.write_text(uncommitted_content)

    make_report(git_repo, Lens("full"))

    assert app_ts.read_text() == uncommitted_content
