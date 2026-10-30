# pyright: reportMissingImports=false
"""Unit tests for repository slug derivation and git root detection."""

from pathlib import Path
import pytest
from understand_runs.slug import get_repo_root, get_repo_slug, is_git_repo
import todo_navigator.parser as todo_parser


def test_get_repo_slug_matches_todo_navigator():
    test_paths = [
        Path("/media/psf/Home/projects/my-project"),
        Path("/var/tmp/a--b---c"),
        Path("/home/user/code/repo_name"),
        Path("/"),
    ]
    for path in test_paths:
        expected = todo_parser.get_repo_slug(path)
        actual = get_repo_slug(path)
        assert actual == expected, f"Failed for path {path}: {actual} != {expected}"


def test_get_repo_slug_custom_path():
    p = Path("/home/user/projects/sample-app")
    slug = get_repo_slug(p)
    assert slug == "home-user-projects-sample-app"


def test_get_repo_slug_empty_or_root():
    p = Path("/")
    # str(p.resolve()).strip("/") is empty -> falls back to "default-repo"
    assert get_repo_slug(p) == "default-repo"


def test_is_git_repo_and_get_repo_root(git_repo, non_git_dir):
    assert is_git_repo(git_repo) is True
    assert get_repo_root(git_repo) == git_repo.resolve()

    assert is_git_repo(non_git_dir) is False
    assert get_repo_root(non_git_dir) == non_git_dir.resolve()
