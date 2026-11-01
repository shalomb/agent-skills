# pyright: reportMissingImports=false
"""Unit tests for understand_runs CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

from understand_runs.cli import main


def test_cli_outputs_phases_and_json(temp_cache, git_repo, capsys):
    code = main(["--cwd", str(git_repo), "--json", "full"])
    assert code == 0

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()

    # Verify PHASE output lines
    assert "PHASE:plan" in lines
    assert "PHASE:discover" in lines
    assert "PHASE:converge" in lines
    assert "PHASE:render" in lines

    # Verify JSON payload at the end
    json_line = lines[-1]
    data = json.loads(json_line)
    assert "run_dir" in data
    assert (Path(data["run_dir"]) / "report.html").exists()
    assert data["lens"] == {"type": "full", "target": None}
    assert "parallels" in data["urls"]
    assert "tailnet" in data["urls"]


def test_cli_requires_git_for_pr_lens(temp_cache, non_git_dir, capsys):
    code = main(["--cwd", str(non_git_dir), "pr", "123"])
    assert code == 2

    captured = capsys.readouterr()
    assert "ERROR:" in captured.err
    assert "needs a git repository" in captured.err.lower()
