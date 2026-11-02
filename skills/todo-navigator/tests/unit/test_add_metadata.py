"""`todo add` task metadata (created, goal), run as a subprocess against a temp repo."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from todo_navigator.editor import handle_express_edit
from todo_navigator.parser import get_shadow_dir, parse_todo_line

SRC = Path(__file__).resolve().parents[2] / "src"


class CliHarness(unittest.TestCase):
    """Temp git repo plus an isolated XDG_CACHE_HOME; no tests of its own."""

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


class AddMetadataTest(CliHarness):
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


GOAL_FILE = """---
id: g-feat-export
branch: feat/export
status: {status}            # draft | active | closed | dropped
outcome: "Users can export a backlog as CSV"
done_check:
  kind: command
  commands:
    - make test-unit
created_at: 2026-11-01T10:00:00Z
---

## Anti-goals
- status: active
"""


class GoalHarness(CliHarness):
    """CliHarness on branch feat/export with a helper to write that branch's goal file."""

    def setUp(self) -> None:
        super().setUp()
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "feat/export"], check=True)

    def write_goal(self, status: str, branch_slug: str = "feat-export") -> None:
        with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.cache)}):
            goals = get_shadow_dir(self.repo) / "goals"
        goals.mkdir(parents=True, exist_ok=True)
        (goals / f"{branch_slug}.md").write_text(GOAL_FILE.format(status=status), encoding="utf-8")


class AddGoalLinkTest(GoalHarness):
    def added_line(self) -> str:
        return next(ln for ln in self.todo_text().splitlines() if "[id: t1]" in ln)

    def test_add_links_the_active_goal_of_the_current_branch(self) -> None:
        self.write_goal("active")
        self.assertEqual(self.todo("add", "T", "--id", "t1").returncode, 0)
        self.assertIn("[goal: g-feat-export]", self.added_line())

    def test_add_does_not_link_a_goal_that_is_not_active(self) -> None:
        self.write_goal("draft")
        self.todo("add", "T", "--id", "t1")
        self.assertNotIn("[goal:", self.added_line())

    def test_add_does_not_link_without_a_goal_file(self) -> None:
        self.todo("add", "T", "--id", "t1")
        self.assertNotIn("[goal:", self.added_line())

    def test_add_ignores_the_goal_of_another_branch(self) -> None:
        self.write_goal("active", branch_slug="feat-other")
        self.todo("add", "T", "--id", "t1")
        self.assertNotIn("[goal:", self.added_line())

    def test_explicit_goal_overrides_the_active_goal(self) -> None:
        self.write_goal("active")
        self.todo("add", "T", "--id", "t1", "--goal", "g-other")
        self.assertIn("[goal: g-other]", self.added_line())
        self.assertNotIn("g-feat-export", self.added_line())

    def test_goal_none_suppresses_the_link(self) -> None:
        self.write_goal("active")
        self.todo("add", "T", "--id", "t1", "--goal", "none")
        self.assertNotIn("[goal:", self.added_line())

    def test_detached_head_gets_no_goal_link(self) -> None:
        self.write_goal("active")
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t"}
        env["GIT_COMMITTER_EMAIL"] = "t@example.com"
        git = ["git", "-C", str(self.repo), "-c", "commit.gpgsign=false"]
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "c"], check=True, env={**os.environ, **env})
        subprocess.run([*git, "checkout", "-q", "--detach"], check=True)
        self.todo("add", "T", "--id", "t1")
        self.assertNotIn("[goal:", self.added_line())


class ExpressDoneStampsDoneAtTest(CliHarness):
    def test_edit_done_stamps_done_at_on_the_completed_task(self) -> None:
        (self.repo / "TODO.md").write_text(
            "# Backlog\n\n- [ ] A <!-- [id: a] [prio: P1] -->\n- [ ] B <!-- [id: b] [prio: P2] -->\n",
            encoding="utf-8",
        )
        r = self.todo("edit", "a", "done")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = self.todo_text().splitlines()
        done_line = next(ln for ln in lines if "[id: a]" in ln)
        self.assertTrue(done_line.startswith("- [x]"), done_line)
        self.assertRegex(done_line, r"\[done: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z\]")
        self.assertNotIn("[done:", next(ln for ln in lines if "[id: b]" in ln))

    def test_edit_done_replaces_a_stale_done_at_with_a_fresh_one(self) -> None:
        (self.repo / "TODO.md").write_text(
            "# Backlog\n\n- [ ] A <!-- [id: a] [prio: P1] [done: 2026-01-01T00:00Z] -->\n", encoding="utf-8"
        )
        self.todo("edit", "a", "done")
        self.assertNotIn("2026-01-01T00:00Z", self.todo_text())
        self.assertEqual(self.todo_text().count("[done:"), 1)

    def test_edit_done_appends_a_comment_when_the_line_has_no_metadata_comment(self) -> None:
        # The parser gives such a line an auto id, so the CLI cannot reach it by [id: a]; call the editor directly.
        todo = self.repo / "TODO.md"
        todo.write_text("# Backlog\n\n- [ ] A [id: a]\n- [ ] B <!-- [id: b] -->\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            ret = handle_express_edit(self.repo, todo, self.repo, "a", self.repo / "a.md", ["done"])
        self.assertEqual(ret, 0)
        line = next(ln for ln in todo.read_text(encoding="utf-8").splitlines() if "[id: a]" in ln)
        self.assertTrue(line.startswith("- [x]"), line)
        self.assertRegex(line, r"^- \[x\] A \[id: a\] <!-- \[done: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z\] -->$")


class ReopenClearsCompletionTest(CliHarness):
    def test_done_undone_done_round_trip_stamps_a_fresh_done_time(self) -> None:
        (self.repo / "TODO.md").write_text(
            "# Backlog\n\n- [x] A <!-- [id: a] [prio: P1] [done: 2026-01-01T00:00Z] [commit: abc123] -->\n",
            encoding="utf-8",
        )
        self.assertEqual(self.todo("edit", "a", "undone").returncode, 0)
        reopened = self.todo_text()
        self.assertIn("- [ ] A", reopened)
        self.assertNotIn("[done:", reopened)
        self.assertNotIn("[commit:", reopened)
        self.assertIn("[prio: P1]", reopened)

        self.assertEqual(self.todo("edit", "a", "done").returncode, 0)
        line = next(ln for ln in self.todo_text().splitlines() if "[id: a]" in ln)
        self.assertTrue(line.startswith("- [x]"), line)
        self.assertRegex(line, r"\[done: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z\]")
        self.assertNotIn("2026-01-01T00:00Z", line)

    def test_every_reopen_alias_clears_done_and_commit(self) -> None:
        for alias in ("undone", "todo", "uncheck", "reopen"):
            with self.subTest(alias=alias):
                (self.repo / "TODO.md").write_text(
                    "- [x] A <!-- [id: a] [done: 2026-01-01T00:00Z] [commit: abc123] -->\n", encoding="utf-8"
                )
                self.todo("edit", "a", alias)
                self.assertNotIn("[done:", self.todo_text())
                self.assertNotIn("[commit:", self.todo_text())


class BriefGoalTest(GoalHarness):
    def brief(self) -> dict:
        r = self.todo("brief", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_brief_json_reports_the_goal_of_the_current_branch(self) -> None:
        self.write_goal("active")
        self.assertEqual(self.brief()["goal"], {"id": "g-feat-export", "status": "active"})

    def test_brief_json_reports_a_non_active_goal_with_its_status(self) -> None:
        self.write_goal("draft")
        self.assertEqual(self.brief()["goal"], {"id": "g-feat-export", "status": "draft"})

    def test_brief_json_goal_is_null_without_a_goal_file(self) -> None:
        self.assertIsNone(self.brief()["goal"])
