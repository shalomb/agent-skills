"""Unit tests for dependency graph, cycle detection, and WSJF sorting."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from todo_navigator.dag import (
    add_dependency,
    compute_waves,
    detect_cycle,
    find_matching_targets,
    remove_dependency,
    replan_todo_file,
    sort_tasks_wsjf,
)
from todo_navigator.models import Task

SECTIONED_TODO = (
    "# Backlog\n"
    "\n"
    "## CRITICAL\n"
    "- [ ] Fix crash <!-- [id: fix-crash] [prio: P0] -->\n"
    "\n"
    "## LATER\n"
    "- [ ] Add export <!-- [id: add-export] [prio: P2] -->\n"
    "\n"
    "Footer notes.\n"
)


class TestDAG(unittest.TestCase):
    def test_detect_cycle_none(self) -> None:
        tasks = [
            Task(id="a", title="A"),
            Task(id="b", title="B", depends_on=["a"]),
            Task(id="c", title="C", depends_on=["b"]),
        ]
        self.assertIsNone(detect_cycle(tasks))

    def test_detect_cycle_found(self) -> None:
        tasks = [
            Task(id="a", title="A", depends_on=["c"]),
            Task(id="b", title="B", depends_on=["a"]),
            Task(id="c", title="C", depends_on=["b"]),
        ]
        cycle = detect_cycle(tasks)
        self.assertIsNotNone(cycle)

    def test_compute_waves(self) -> None:
        tasks = [
            Task(id="init", title="Init", completed=True),
            Task(id="auth", title="Auth", depends_on=["init"], wsjf_cost=2.0),
            Task(id="db", title="Database", depends_on=["init"], wsjf_cost=5.0),
            Task(id="api", title="API", depends_on=["auth", "db"], wsjf_cost=3.0),
        ]
        waves = compute_waves(tasks)
        self.assertEqual(len(waves), 2)
        # Wave 1 should contain db (wsjf=5.0) then auth (wsjf=2.0)
        self.assertEqual([t.id for t in waves[0]], ["db", "auth"])
        # Wave 2 should contain api
        self.assertEqual([t.id for t in waves[1]], ["api"])

    def test_sort_tasks_wsjf(self) -> None:
        tasks = [
            Task(id="done-task", title="Done", completed=True),
            Task(id="low", title="Low", wsjf_cost=1.0),
            Task(id="high", title="High", wsjf_cost=10.0),
        ]
        sorted_tasks = sort_tasks_wsjf(tasks)
        self.assertEqual([t.id for t in sorted_tasks], ["done-task", "high", "low"])

    def test_add_and_remove_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            todo_file = repo_root / "TODO.md"
            todo_file.write_text(
                "# Backlog\n\n- [ ] Task A <!-- [id: a] -->\n- [ ] Task B <!-- [id: b] -->\n",
                encoding="utf-8",
            )

            # Add valid dependency: B depends on A
            ok, msg = add_dependency(repo_root, "b", "a")
            self.assertTrue(ok)
            self.assertIn("now depends on 'a'", msg)

            # Attempt circular dependency: A depends on B -> should reject!
            ok_cycle, msg_cycle = add_dependency(repo_root, "a", "b")
            self.assertFalse(ok_cycle)
            self.assertIn("circular cycle detected", msg_cycle)

            # Remove dependency
            ok_rm, msg_rm = remove_dependency(repo_root, "b", "a")
            self.assertTrue(ok_rm)
            self.assertIn("no longer depends on 'a'", msg_rm)

    def test_dependency_edits_keep_tasks_in_their_sections(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            todo_file = repo_root / "TODO.md"
            todo_file.write_text(SECTIONED_TODO, encoding="utf-8")

            add_dependency(repo_root, "add-export", "fix-crash")
            remove_dependency(repo_root, "add-export", "fix-crash")

            self.assertEqual(todo_file.read_text(encoding="utf-8"), SECTIONED_TODO)

    def test_replan_reorders_within_sections_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            todo_file = Path(td) / "TODO.md"
            todo_file.write_text(
                "# Backlog\n"
                "\n"
                "## CRITICAL\n"
                "- [ ] Fix crash <!-- [id: fix-crash] [prio: P0] -->\n"
                "\n"
                "## LATER\n"
                "- [ ] Low <!-- [id: low] [prio: P2] -->\n"
                "- [ ] High <!-- [id: high] [prio: P2] [wsjf: 9.0/1.0] -->\n",
                encoding="utf-8",
            )

            replan_todo_file(todo_file)

            self.assertEqual(
                todo_file.read_text(encoding="utf-8"),
                "# Backlog\n"
                "\n"
                "## CRITICAL\n"
                "- [ ] Fix crash <!-- [id: fix-crash] [prio: P0] -->\n"
                "\n"
                "## LATER\n"
                "- [ ] High <!-- [id: high] [prio: P2] [wsjf: 9.0/1.0] -->\n"
                "- [ ] Low <!-- [id: low] [prio: P2] -->\n",
            )

    def test_find_matching_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            shadow_dir = repo_root / "shadow"
            tasks_dir = shadow_dir / "tasks"
            tasks_dir.mkdir(parents=True)

            (tasks_dir / "create-an-automated-test-harness.md").write_text("# Card", encoding="utf-8")
            (tasks_dir / "core-engine.md").write_text("# Card", encoding="utf-8")

            # Substring match
            m1 = find_matching_targets(repo_root, shadow_dir, "test-harness")
            self.assertEqual(len(m1), 1)
            self.assertEqual(m1[0][0], "create-an-automated-test-harness")

            # Token match
            m2 = find_matching_targets(repo_root, shadow_dir, "automated harness")
            self.assertEqual(len(m2), 1)
            self.assertEqual(m2[0][0], "create-an-automated-test-harness")

            # Multi match
            m3 = find_matching_targets(repo_root, shadow_dir, "e")
            self.assertEqual(len(m3), 2)


if __name__ == "__main__":
    unittest.main()
