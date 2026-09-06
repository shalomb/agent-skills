"""BDD Scenario tests for Todo Navigator CLI workflows.

Applies Specification by Example / BDD patterns to verify end-to-end capabilities.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from todo_navigator.cli import (
    main,
)


class TestTodoBDDScenarios(unittest.TestCase):
    """BDD Scenarios testing end-to-end CLI operations."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.todo_file = self.repo_root / "TODO.md"
        self.todo_file.write_text("# Test Backlog\n\n", encoding="utf-8")

        self.patcher_root = patch("todo_navigator.parser.get_repo_root", return_value=self.repo_root)
        self.patcher_root_cli = patch("todo_navigator.cli.get_repo_root", return_value=self.repo_root)
        self.patcher_root.start()
        self.patcher_root_cli.start()

    def tearDown(self) -> None:
        self.patcher_root_cli.stop()
        self.patcher_root.stop()
        self.temp_dir.cleanup()

    def test_scenario_add_and_list_tasks(self) -> None:
        """Scenario: User adds tasks and views headings list.

        Given a clean project backlog
        When the user adds task 'Build Core Engine' with priority P1
        And the user adds task 'Implement Editor' with priority P2 after 'build-core-engine'
        Then 'todo list' lists both task headings with their priority and status
        And 'todo list core' lists only 'Build Core Engine'
        """
        # Step 1: Add task 1
        with patch("sys.stdout", new=io.StringIO()) as out1:
            ret1 = main(["add", "Build Core Engine", "--prio", "P1"])
            self.assertEqual(ret1, 0)
            self.assertIn("Added task [build-core-engine]", out1.getvalue())

        # Step 2: Add task 2 depending on task 1
        with patch("sys.stdout", new=io.StringIO()) as out2:
            ret2 = main(["add", "Implement Editor", "--prio", "P2", "--after", "build-core-engine"])
            self.assertEqual(ret2, 0)
            self.assertIn("Added task [implement-editor]", out2.getvalue())

        # Step 3: todo list (all)
        with patch("sys.stdout", new=io.StringIO()) as out_list:
            ret_list = main(["list"])
            self.assertEqual(ret_list, 0)
            lines = out_list.getvalue().strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn("[P1] [build-core-engine] Build Core Engine", lines[0])
            self.assertIn("[P2] [implement-editor] Implement Editor", lines[1])

        # Step 4: todo list with partial filter 'core'
        with patch("sys.stdout", new=io.StringIO()) as out_filter:
            ret_filter = main(["list", "core"])
            self.assertEqual(ret_filter, 0)
            lines_filter = out_filter.getvalue().strip().splitlines()
            self.assertEqual(len(lines_filter), 1)
            self.assertIn("build-core-engine", lines_filter[0])

    def test_scenario_manage_dependencies_and_prevent_cycles(self) -> None:
        """Scenario: User wires dependencies and prevents circular deadlocks.

        Given two independent tasks 'Task A' and 'Task B'
        When the user adds a dependency making 'Task B' depend on 'Task A'
        Then 'Task B' lists 'after: a'
        And when the user attempts to make 'Task A' depend on 'Task B'
        Then the command fails and warns of a circular cycle
        """
        main(["add", "Task A", "--id", "task-a"])
        main(["add", "Task B", "--id", "task-b"])

        # Add valid dep
        with patch("sys.stdout", new=io.StringIO()) as out_dep:
            ret_dep = main(["dep", "add", "task-b", "task-a"])
            self.assertEqual(ret_dep, 0)
            self.assertIn("now depends on 'task-a'", out_dep.getvalue())

        # Verify in list
        with patch("sys.stdout", new=io.StringIO()) as out_list:
            main(["list", "task-b"])
            self.assertIn("after: task-a", out_list.getvalue())

        # Add cycle: task-a depends on task-b
        with patch("sys.stdout", new=io.StringIO()) as out_cycle:
            ret_cycle = main(["dep", "add", "task-a", "task-b"])
            self.assertEqual(ret_cycle, 1)
            self.assertIn("circular cycle detected", out_cycle.getvalue())

    def test_scenario_express_edit_and_status_advance(self) -> None:
        """Scenario: User performs express edits to update criteria and mark tasks done.

        Given task 'create-an-automated-test-harness'
        When the user runs 'todo edit harness add Run unit tests via uv'
        Then the acceptance criteria are updated on disk
        And when the user runs 'todo edit harness done'
        Then the task is checked off in TODO.md
        And 'todo status' reports 100% progress
        """
        main(["add", "Create an automated test harness", "--id", "create-an-automated-test-harness"])

        # Add criterion via partial match 'harness'
        with patch("sys.stdout", new=io.StringIO()) as out_add_crit:
            ret_crit = main(["edit", "harness", "add", "Run unit tests via uv"])
            self.assertEqual(ret_crit, 0)
            self.assertIn("Added criterion", out_add_crit.getvalue())

        # Mark done via partial match 'harness'
        with patch("sys.stdout", new=io.StringIO()) as out_done:
            ret_done = main(["edit", "harness", "done"])
            self.assertEqual(ret_done, 0)
            self.assertIn("Marked task [create-an-automated-test-harness] as completed", out_done.getvalue())

        # Status check
        with patch("sys.stdout", new=io.StringIO()) as out_status:
            ret_status = main(["status"])
            self.assertEqual(ret_status, 0)
            self.assertIn("1/1 completed (100%)", out_status.getvalue())

    def test_scenario_graph_visualization(self) -> None:
        """Scenario: User generates ASCII tree and Mermaid diagram of DAG.

        Given a sequence of dependent tasks
        When the user runs 'todo graph'
        Then an ASCII tree with execution waves is rendered
        And when the user runs 'todo graph --mermaid'
        Then a valid Mermaid flowchart is rendered
        """
        main(["add", "Task Root", "--id", "root"])
        main(["add", "Task Child", "--id", "child", "--after", "root"])

        with patch("sys.stdout", new=io.StringIO()) as out_tree:
            ret_tree = main(["graph"])
            self.assertEqual(ret_tree, 0)
            self.assertIn("Execution Waves", out_tree.getvalue())
            self.assertIn("Wave 1", out_tree.getvalue())

        with patch("sys.stdout", new=io.StringIO()) as out_mermaid:
            ret_mermaid = main(["graph", "--mermaid"])
            self.assertEqual(ret_mermaid, 0)
            self.assertIn("```mermaid", out_mermaid.getvalue())
            self.assertIn("root --> child", out_mermaid.getvalue())


if __name__ == "__main__":
    unittest.main()
