"""Unit tests for serve-root resolution."""

# pyright: reportMissingImports=false
# (report_server is put on sys.path by conftest.py; the editor cannot see that)
from __future__ import annotations

from pathlib import Path

import pytest

from report_server.paths import resolve_serve_root


def test_a_symlinked_root_resolves_to_its_real_directory(tmp_path: Path):
    real = tmp_path / "host" / "projects"
    real.mkdir(parents=True)
    (tmp_path / "projects").symlink_to(real)
    assert resolve_serve_root(tmp_path / "projects") == real


def test_a_plain_directory_resolves_to_itself(tmp_path: Path):
    assert resolve_serve_root(tmp_path) == tmp_path.resolve()


def test_a_missing_root_is_refused(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        resolve_serve_root(tmp_path / "absent")


def test_a_file_is_not_a_serve_root(tmp_path: Path):
    plain_file = tmp_path / "file"
    plain_file.write_text("x")
    with pytest.raises(NotADirectoryError):
        resolve_serve_root(plain_file)
