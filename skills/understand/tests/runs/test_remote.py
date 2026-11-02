# pyright: reportMissingImports=false
"""Unit tests for remote git web URL resolution and dual navigation link generation (ADR-0005)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from understand_runs.remote import (  # noqa: E402
    RemoteInfo,
    build_file_link,
    format_file_citation,
    parse_remote_url,
    resolve_remote_web_url,
)


class TestRemoteUrlParsing:
    """Tests parsing of various git remote URL formats (SSH, HTTPS, GitLab)."""

    def test_parse_ssh_github_url(self):
        url = "git@github.com:example-org/my-repo.git"
        info = parse_remote_url(url, commit="a1b2c3d")
        assert info is not None
        assert info.web_base == "https://github.com/example-org/my-repo"
        assert info.commit == "a1b2c3d"
        assert info.host == "github"

    def test_parse_ssh_github_url_without_git_suffix(self):
        url = "git@github.com:example-org/my-repo"
        info = parse_remote_url(url)
        assert info is not None
        assert info.web_base == "https://github.com/example-org/my-repo"
        assert info.commit is None
        assert info.host == "github"

    def test_parse_ssh_scheme_url(self):
        url = "ssh://git@github.com/example-org/my-repo.git"
        info = parse_remote_url(url, commit="head123")
        assert info is not None
        assert info.web_base == "https://github.com/example-org/my-repo"
        assert info.commit == "head123"
        assert info.host == "github"

    def test_parse_https_github_url(self):
        url = "https://github.com/example-org/my-repo.git"
        info = parse_remote_url(url, commit="c0ffee")
        assert info is not None
        assert info.web_base == "https://github.com/example-org/my-repo"
        assert info.commit == "c0ffee"
        assert info.host == "github"

    def test_parse_https_github_url_with_auth(self):
        url = "https://oauth2:token123@github.com/example-org/my-repo.git"
        info = parse_remote_url(url)
        assert info is not None
        assert info.web_base == "https://github.com/example-org/my-repo"
        assert info.host == "github"

    def test_parse_ssh_gitlab_url(self):
        url = "git@gitlab.com:example-org/subgroup/my-repo.git"
        info = parse_remote_url(url, commit="deadbeef")
        assert info is not None
        assert info.web_base == "https://gitlab.com/example-org/subgroup/my-repo"
        assert info.commit == "deadbeef"
        assert info.host == "gitlab"

    def test_parse_https_gitlab_url(self):
        url = "https://gitlab.com/example-org/my-repo.git"
        info = parse_remote_url(url, commit="fedcba")
        assert info is not None
        assert info.web_base == "https://gitlab.com/example-org/my-repo"
        assert info.commit == "fedcba"
        assert info.host == "gitlab"

    def test_parse_invalid_url_returns_none(self):
        assert parse_remote_url("") is None
        assert parse_remote_url("not-a-url") is None
        assert parse_remote_url("   ") is None


class TestBuildFileLink:
    """Tests canonical commit-pinned web URLs generation."""

    def test_build_github_file_link_with_line_and_commit(self):
        info = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="a1b2c3d", host="github")
        link = build_file_link(info, "src/app.py", 42)
        assert link == "https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py#L42"

    def test_build_github_file_link_without_line(self):
        info = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="a1b2c3d", host="github")
        link = build_file_link(info, "src/app.py")
        assert link == "https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py"

    def test_build_github_file_link_defaults_commit_to_head_when_none(self):
        info = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit=None, host="github")
        link = build_file_link(info, "src/app.py", 10)
        assert link == "https://github.com/example-org/my-repo/blob/HEAD/src/app.py#L10"

    def test_build_gitlab_file_link_structure(self):
        info = RemoteInfo(web_base="https://gitlab.com/example-org/my-repo", commit="123456", host="gitlab")
        link = build_file_link(info, "src/core.py", 77)
        assert link == "https://gitlab.com/example-org/my-repo/-/blob/123456/src/core.py#L77"

    def test_build_gitlab_file_link_without_line(self):
        info = RemoteInfo(web_base="https://gitlab.com/example-org/my-repo", commit="123456", host="gitlab")
        link = build_file_link(info, "src/core.py")
        assert link == "https://gitlab.com/example-org/my-repo/-/blob/123456/src/core.py"

    def test_build_file_link_cleans_leading_slash_and_dot(self):
        info = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="a1b2c3d", host="github")
        assert build_file_link(info, "./src/app.py", 5) == "https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py#L5"
        assert build_file_link(info, "/src/app.py", 5) == "https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py#L5"

    def test_build_file_link_with_none_remote_returns_none(self):
        assert build_file_link(None, "src/app.py", 42) is None
        assert build_file_link(None, "src/app.py") is None


class TestResolveRemoteWebUrl:
    """Tests git remote origin inspection and graceful fallbacks."""

    def test_resolve_remote_web_url_from_git_command(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                if cmd == ["git", "remote", "get-url", "origin"]:
                    return MagicMock(returncode=0, stdout="git@github.com:example-org/my-repo.git\n")
                if cmd == ["git", "rev-parse", "HEAD"]:
                    return MagicMock(returncode=0, stdout="a1b2c3d\n")
                return MagicMock(returncode=1, stdout="")

            mock_run.side_effect = side_effect
            info = resolve_remote_web_url(tmp_path)
            assert info is not None
            assert info.web_base == "https://github.com/example-org/my-repo"
            assert info.commit == "a1b2c3d"
            assert info.host == "github"

    def test_resolve_remote_web_url_pinned_commit_overrides_git_rev_parse(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/example-org/my-repo.git\n")
            info = resolve_remote_web_url(tmp_path, commit="explicit-commit")
            assert info is not None
            assert info.commit == "explicit-commit"

    def test_resolve_remote_web_url_missing_remote_returns_none(self, tmp_path: Path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            info = resolve_remote_web_url(tmp_path)
            assert info is None

    def test_resolve_remote_web_url_nonexistent_path_returns_none(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist"
        assert resolve_remote_web_url(nonexistent) is None

    def test_resolve_remote_web_url_from_git_config_fallback(self, tmp_path: Path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config_content = (
            '[core]\n'
            '    repositoryformatversion = 0\n'
            '[remote "origin"]\n'
            '    url = git@gitlab.com:org/repo.git\n'
            '    fetch = +refs/heads/*:refs/remotes/origin/*\n'
        )
        (git_dir / "config").write_text(config_content, encoding="utf-8")

        with patch("subprocess.run") as mock_run:
            # subprocess git remote fails, so config file fallback triggers
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            info = resolve_remote_web_url(tmp_path, commit="sha987")
            assert info is not None
            assert info.web_base == "https://gitlab.com/org/repo"
            assert info.commit == "sha987"
            assert info.host == "gitlab"


class TestFormatFileCitation:
    """Tests dual navigation citation formatting in Markdown."""

    def test_citation_with_remote_info_and_line(self):
        remote = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="a1b2c3d", host="github")
        citation = format_file_citation("src/app.py", 42, remote_info=remote)
        assert citation == "[`src/app.py`](src/src/app.py.html#L42) [view online ↗](https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py#L42)"

    def test_citation_with_remote_info_without_line(self):
        remote = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="a1b2c3d", host="github")
        citation = format_file_citation("src/app.py", remote_info=remote)
        assert citation == "[`src/app.py`](src/src/app.py.html) [view online ↗](https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py)"

    def test_citation_without_remote_info(self):
        citation = format_file_citation("src/app.py", 42, remote_info=None)
        assert citation == "[`src/app.py`](src/src/app.py.html#L42)"
        assert "view online" not in citation

    def test_citation_with_custom_label(self):
        remote = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="a1b2c3d", host="github")
        citation = format_file_citation("src/app.py", 42, remote_info=remote, label="Application Entry")
        assert citation == "[Application Entry](src/src/app.py.html#L42) [view online ↗](https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py#L42)"
