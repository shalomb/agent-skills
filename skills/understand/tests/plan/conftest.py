# pyright: reportMissingImports=false
"""Shared fixtures for discovery planner and docs profile tests (Step 4)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

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
