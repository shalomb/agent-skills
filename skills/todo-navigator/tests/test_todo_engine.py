#!/usr/bin/env python3
"""Unit tests for skills/todo-navigator/scripts/todo_engine.py."""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add todo_engine to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import todo_engine


class TestTodoEngineMatching(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.shadow_dir = self.repo_root / ".cache" / "todos"
        self.tasks_dir = self.shadow_dir / "tasks"
        self.tasks_dir.mkdir(parents=True)

        # Create sample TODO.md
        self.todo_path = self.shadow_dir / "TODO.md"
        self.todo_path.write_text(
            "# Backlog\n\n"
            "- [ ] Core engine refactor <!-- [id: core-engine] [prio: P1] -->\n"
            "- [ ] Launch editor integration <!-- [id: editor-launch] [prio: P2] -->\n"
            "- [ ] Create an automated test harness <!-- [id: create-an-automated-test-harness] [prio: P1] -->\n",
            encoding="utf-8",
        )

        # Create sample task cards
        (self.tasks_dir / "core-engine.md").write_text(
            "# Core Engine Card\n", encoding="utf-8"
        )
        (self.tasks_dir / "editor-launch.md").write_text(
            "# Editor Launch Card\n", encoding="utf-8"
        )
        (self.tasks_dir / "create-an-automated-test-harness.md").write_text(
            "# Test Harness Card\n", encoding="utf-8"
        )

        self.patcher_root = patch(
            "todo_engine.get_repo_root", return_value=self.repo_root
        )
        self.patcher_shadow = patch(
            "todo_engine.get_shadow_dir", return_value=self.shadow_dir
        )
        self.patcher_root.start()
        self.patcher_shadow.start()

    def tearDown(self) -> None:
        self.patcher_shadow.stop()
        self.patcher_root.stop()
        self.temp_dir.cleanup()

    def test_exact_match(self) -> None:
        matches = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "core-engine", force_shadow=True
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "core-engine")
        self.assertEqual(matches[0][1].name, "core-engine.md")

    def test_backlog_match(self) -> None:
        matches = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "todo", force_shadow=True
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "todo")
        self.assertEqual(matches[0][1], self.todo_path)

    def test_partial_substring_match(self) -> None:
        # 'test-harness' should match 'create-an-automated-test-harness'
        matches = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "test-harness", force_shadow=True
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "create-an-automated-test-harness")

        # 'harness' should also match
        matches_short = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "harness", force_shadow=True
        )
        self.assertEqual(len(matches_short), 1)
        self.assertEqual(matches_short[0][0], "create-an-automated-test-harness")

    def test_token_match(self) -> None:
        # Match separated tokens: 'automated harness'
        matches = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "automated harness", force_shadow=True
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "create-an-automated-test-harness")

    def test_multiple_matches(self) -> None:
        # 'e' matches all three tasks
        matches = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "e", force_shadow=True
        )
        self.assertEqual(len(matches), 3)
        matched_ids = [m[0] for m in matches]
        self.assertIn("core-engine", matched_ids)
        self.assertIn("editor-launch", matched_ids)
        self.assertIn("create-an-automated-test-harness", matched_ids)

    def test_no_matches(self) -> None:
        matches = todo_engine.find_matching_targets(
            self.repo_root, self.shadow_dir, "nonexistent-task-xyz", force_shadow=True
        )
        self.assertEqual(len(matches), 0)

    def test_get_all_task_ids(self) -> None:
        task_ids = todo_engine.get_all_task_ids(
            self.repo_root, self.shadow_dir, force_shadow=True
        )
        self.assertEqual(
            task_ids,
            ["core-engine", "create-an-automated-test-harness", "editor-launch"],
        )


class TestTodoEngineCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.shadow_dir = self.repo_root / ".cache" / "todos"
        self.tasks_dir = self.shadow_dir / "tasks"
        self.tasks_dir.mkdir(parents=True)

        self.todo_path = self.shadow_dir / "TODO.md"
        self.todo_path.write_text(
            "# Backlog\n\n"
            "- [ ] Core engine refactor <!-- [id: core-engine] [prio: P1] -->\n"
            "- [ ] Create an automated test harness <!-- [id: create-an-automated-test-harness] [prio: P1] -->\n",
            encoding="utf-8",
        )

        (self.tasks_dir / "core-engine.md").write_text(
            "# Core Engine Card\nContent A\n", encoding="utf-8"
        )
        (self.tasks_dir / "create-an-automated-test-harness.md").write_text(
            "# Test Harness Card\nContent B\n", encoding="utf-8"
        )

        self.patcher_root = patch(
            "todo_engine.get_repo_root", return_value=self.repo_root
        )
        self.patcher_shadow = patch(
            "todo_engine.get_shadow_dir", return_value=self.shadow_dir
        )
        self.patcher_root.start()
        self.patcher_shadow.start()

    def tearDown(self) -> None:
        self.patcher_shadow.stop()
        self.patcher_root.stop()
        self.temp_dir.cleanup()

    def test_cmd_view_single_match(self) -> None:
        args = argparse.Namespace(target="harness", shadow=True)
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = todo_engine.cmd_view(args)
            self.assertEqual(ret, 0)
            output = fake_out.getvalue()
            self.assertIn("Viewing: [create-an-automated-test-harness.md]", output)
            self.assertIn("Content B", output)

    def test_cmd_view_multiple_matches(self) -> None:
        args = argparse.Namespace(target="e", shadow=True)
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = todo_engine.cmd_view(args)
            self.assertEqual(ret, 0)
            output = fake_out.getvalue()
            self.assertIn("Found 2 task cards matching 'e'", output)
            self.assertIn("[1/2] core-engine.md", output)
            self.assertIn("[2/2] create-an-automated-test-harness.md", output)
            self.assertIn("Content A", output)
            self.assertIn("Content B", output)

    def test_cmd_view_zero_matches(self) -> None:
        args = argparse.Namespace(target="nonexistent", shadow=True)
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = todo_engine.cmd_view(args)
            self.assertEqual(ret, 1)
            output = fake_out.getvalue()
            self.assertIn("No task card matching 'nonexistent' found", output)
            self.assertIn("Available tasks:", output)
            self.assertIn("core-engine", output)

    def test_cmd_edit_express_operations(self) -> None:
        # Add criterion via partial match 'harness'
        args = argparse.Namespace(
            target="harness", ops=["add", "Verify", "coverage"], shadow=True
        )
        with patch("sys.stdout", new=io.StringIO()):
            ret = todo_engine.cmd_edit(args)
        self.assertEqual(ret, 0)

        card_content = (
            self.tasks_dir / "create-an-automated-test-harness.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- [ ] Verify coverage", card_content)

        # Mark done via partial match 'engine'
        args_done = argparse.Namespace(target="engine", ops=["done"], shadow=True)
        with patch("sys.stdout", new=io.StringIO()):
            ret_done = todo_engine.cmd_edit(args_done)
        self.assertEqual(ret_done, 0)

        todo_content = self.todo_path.read_text(encoding="utf-8")
        self.assertIn("- [x] Core engine refactor", todo_content)

    @patch("subprocess.run")
    def test_cmd_edit_interactive_multi_file(self, mock_run: patch) -> None:
        mock_run.return_value.returncode = 0

        args = argparse.Namespace(target="e", ops=[], shadow=True, no_popup=True)
        with (
            patch.dict(
                "os.environ", {"EDITOR": "vi", "TERM": "xterm-256color"}, clear=False
            ),
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout", new=io.StringIO()),
        ):
            ret = todo_engine.cmd_edit(args)
            self.assertEqual(ret, 0)
            called_cmd = mock_run.call_args[0][0]
            self.assertEqual(called_cmd[0], "vi")
            self.assertIn(str(self.tasks_dir / "core-engine.md"), called_cmd)
            self.assertIn(
                str(self.tasks_dir / "create-an-automated-test-harness.md"), called_cmd
            )


if __name__ == "__main__":
    unittest.main()
