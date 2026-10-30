# pyright: reportMissingImports=false
"""Shared fixtures for /understand runs and command tests (Step 3)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure understanding scripts and todo-navigator are importable
ROOT = Path(__file__).resolve().parents[4]
UNDERSTAND = Path(__file__).resolve().parents[2]
SCRIPTS = UNDERSTAND / "scripts"
TODO_NAV_SRC = ROOT / "skills" / "todo-navigator" / "src"

for p in (SCRIPTS, TODO_NAV_SRC):
    p_str = str(p.resolve())
    if p_str not in sys.path:
        sys.path.insert(0, p_str)


@pytest.fixture
def temp_cache(tmp_path, monkeypatch):
    """Sets a clean XDG_CACHE_HOME so shadow directories are isolated."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_dir))
    return cache_dir


@pytest.fixture
def git_repo(tmp_path):
    """Creates a temporary git repository with initial commit."""
    repo = tmp_path / "sample-repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)

    src = repo / "src"
    src.mkdir()
    (src / "app.ts").write_text("console.log('hello world');\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo, check=True)
    return repo


@pytest.fixture
def non_git_dir(tmp_path):
    """Creates a temporary directory that is NOT a git repository."""
    dir_path = tmp_path / "non-git-dir"
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "README.md").write_text("# Project Readme\n")
    sub = dir_path / "docs"
    sub.mkdir()
    (sub / "guide.md").write_text("# Guide\n")
    return dir_path
