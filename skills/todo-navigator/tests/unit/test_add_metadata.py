"""`todo add` task metadata (created, goal), run as a subprocess against a temp repo."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from todo_navigator.parser import parse_todo_line

SRC = Path(__file__).resolve().parents[2] / "src"


class AddMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo = tmp / "repo"
        self.cache = tmp / "cache"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        (self.repo / "TODO.md").write_text("# Backlog\n", encoding="utf-8")
        self.env = {
            **os.environ,
            "PYTHONPATH": str(SRC),
            "XDG_CACHE_HOME": str(self.cache),
            "XDG_RUNTIME_DIR": str(tmp / "run"),
        }

    def todo(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "todo_navigator.cli", *args],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def todo_text(self) -> str:
        return (self.repo / "TODO.md").read_text(encoding="utf-8")

    def test_add_stamps_created_in_iso_8601_utc(self) -> None:
        r = self.todo("add", "Ship it", "--id", "ship-it")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(self.todo_text(), r"\[created: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\]")

    def test_created_survives_a_parse_and_serialise_round_trip(self) -> None:
        self.todo("add", "Ship it", "--id", "ship-it")
        line = next(ln for ln in self.todo_text().splitlines() if "ship-it" in ln)
        task = parse_todo_line(line)
        assert task is not None
        self.assertTrue(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", task.created), task.created)
        self.assertEqual(task.to_markdown_line(), line)

    def test_goal_and_done_at_survive_a_round_trip(self) -> None:
        line = (
            "- [x] T <!-- [id: t] [prio: P2] [created: 2026-11-01T10:00:00Z] "
            "[goal: g-feat-x] [done: 2026-11-02T09:00Z] -->"
        )
        task = parse_todo_line(line)
        assert task is not None
        self.assertEqual(task.created, "2026-11-01T10:00:00Z")
        self.assertEqual(task.goal, "g-feat-x")
        self.assertEqual(task.done_at, "2026-11-02T09:00Z")
        self.assertEqual(task.to_markdown_line(), line)


if __name__ == "__main__":
    unittest.main()
