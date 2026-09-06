"""Unit tests for markdown parser and task card generator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from todo_navigator.parser import (
    add_task_to_todo,
    generate_task_id,
    get_repo_slug,
    parse_todo_file,
    parse_todo_line,
    scaffold_task_card,
)


class TestParser(unittest.TestCase):
    def test_generate_task_id(self) -> None:
        self.assertEqual(generate_task_id("Create an Automated Test Harness"), "create-an-automated-test-harness")
        self.assertEqual(generate_task_id("Fix bug #123 in API!"), "fix-bug-123-in-api")
        # Collisions
        existing = ["deploy", "deploy-2"]
        self.assertEqual(generate_task_id("Deploy", existing), "deploy-3")

    def test_get_repo_slug(self) -> None:
        p = Path("/home/user/projects/my-repo")
        slug = get_repo_slug(p)
        self.assertIn("my-repo", slug)
        self.assertNotIn("/", slug)

    def test_parse_todo_line(self) -> None:
        line = "- [ ] Build Core Engine <!-- [id: core-engine] [prio: P1] [depends: setup,init] [wsjf: 4.0/2.0] -->"
        task = parse_todo_line(line)
        self.assertIsNotNone(task)
        assert task is not None
        self.assertEqual(task.id, "core-engine")
        self.assertEqual(task.title, "Build Core Engine")
        self.assertFalse(task.completed)
        self.assertEqual(task.priority, "P1")
        self.assertEqual(task.depends_on, ["setup", "init"])
        self.assertEqual(task.wsjf_cost, 4.0)
        self.assertEqual(task.wsjf_size, 2.0)
        self.assertEqual(task.wsjf_score, 2.0)

    def test_parse_todo_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "TODO.md"
            p.write_text(
                "# Header\n\n- [ ] Task 1 <!-- [id: t1] -->\n- [x] Task 2 <!-- [id: t2] -->\n\n## Footer",
                encoding="utf-8",
            )
            pre, tasks, post = parse_todo_file(p)
            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0].id, "t1")
            self.assertFalse(tasks[0].completed)
            self.assertEqual(tasks[1].id, "t2")
            self.assertTrue(tasks[1].completed)

    def test_scaffold_task_card(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            card_path = Path(td) / "tasks" / "test-task.md"
            scaffold_task_card(card_path, "test-task", "Test Task Title")
            self.assertTrue(card_path.exists())
            content = card_path.read_text(encoding="utf-8")
            self.assertIn("# Task: Test Task Title", content)
            self.assertIn("## Acceptance Criteria (BDD)", content)

    def test_add_task_to_todo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            # Create a local TODO.md in repo_root to test active repo TODO
            local_todo = repo_root / "TODO.md"
            local_todo.write_text("# Repo Backlog\n\n", encoding="utf-8")

            task, card_path = add_task_to_todo(
                repo_root=repo_root,
                title="New Feature",
                task_id="new-feature",
                prio="P1",
                depends_on=["dep1"],
                force_shadow=False,
            )
            self.assertEqual(task.id, "new-feature")
            self.assertTrue(card_path.exists())

            # Verify it parses back from local_todo
            _, tasks, _ = parse_todo_file(local_todo)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].id, "new-feature")
            self.assertEqual(tasks[0].depends_on, ["dep1"])


if __name__ == "__main__":
    unittest.main()
