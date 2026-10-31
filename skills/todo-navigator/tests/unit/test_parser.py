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

    def test_generate_task_id_caps_length(self) -> None:
        long_title = "Fix link: docs/tutorials/01-getting-started.md -> docs/getting-started.md"
        slug = generate_task_id(long_title)
        self.assertLessEqual(len(slug), 45)
        self.assertTrue(slug.startswith("fix-link-docstutorials01"))

    def test_parse_todo_file_sections(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "TODO.md"
            p.write_text(
                "# Title\n\n"
                "## 🔴 CRITICAL (Blockers)\n"
                "- [ ] Task 1 <!-- [id: t1] -->\n\n"
                "## 🟡 HIGH\n"
                "- [ ] Task 2 <!-- [id: t2] -->\n",
                encoding="utf-8",
            )
            _, tasks, _ = parse_todo_file(p)
            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0].section, "🔴 CRITICAL (Blockers)")
            self.assertEqual(tasks[1].section, "🟡 HIGH")

    def test_add_task_under_section(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            local_todo = repo_root / "TODO.md"
            local_todo.write_text(
                "# Title\n\n"
                "## 🔴 CRITICAL\n"
                "- [ ] Existing Critical <!-- [id: c1] -->\n\n"
                "## 🟡 HIGH\n"
                "- [ ] Existing High <!-- [id: h1] -->\n",
                encoding="utf-8",
            )
            add_task_to_todo(
                repo_root=repo_root,
                title="New Critical Bug",
                section="CRITICAL",
                force_shadow=False,
            )
            _, tasks, _ = parse_todo_file(local_todo)
            self.assertEqual(len(tasks), 3)
            # Should be placed in CRITICAL section before HIGH section
            self.assertEqual(tasks[1].title, "New Critical Bug")
            self.assertEqual(tasks[1].section, "🔴 CRITICAL")

    def test_parse_todo_file_h2_with_h3_subsections(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "TODO.md"
            p.write_text(
                "# Title\n\n## 🔴 CRITICAL\n\n### 1. Subheading\n- [ ] Task in subsection <!-- [id: t1] -->\n",
                encoding="utf-8",
            )
            _, tasks, _ = parse_todo_file(p)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].section, "🔴 CRITICAL")

    def test_add_task_creates_missing_section_with_single_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            todo = repo_root / "TODO.md"
            todo.write_text("# Backlog\n\n- [ ] Old <!-- [id: old] -->\n", encoding="utf-8")
            task, _ = add_task_to_todo(repo_root, title="Brand New", section="URGENT")
            lines = todo.read_text(encoding="utf-8").splitlines()
            self.assertEqual(sum("[id: brand-new]" in ln for ln in lines), 1)
            self.assertEqual(lines.index("## URGENT") + 1, next(i for i, ln in enumerate(lines) if "brand-new" in ln))
            self.assertEqual(task.section, "URGENT")

    def test_add_task_without_existing_tasks_appends_at_end(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            todo = repo_root / "TODO.md"
            todo.write_text("# Backlog\n\nNotes here.\n", encoding="utf-8")
            add_task_to_todo(repo_root, title="First One")
            lines = todo.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[:3], ["# Backlog", "", "Notes here."])
            self.assertIn("[id: first-one]", lines[-1])

    def test_add_task_inserts_after_last_task_at_index_one(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            todo = repo_root / "TODO.md"
            todo.write_text("# Backlog\n- [ ] Old <!-- [id: old] -->\n\nFooter\n", encoding="utf-8")
            add_task_to_todo(repo_root, title="Newer")
            lines = todo.read_text(encoding="utf-8").splitlines()
            self.assertIn("[id: old]", lines[1])
            self.assertIn("[id: newer]", lines[2])

    def test_add_task_after_id_inserts_once_directly_after_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            todo = repo_root / "TODO.md"
            todo.write_text(
                "# Backlog\n- [ ] A <!-- [id: a] -->\n- [ ] B <!-- [id: b] -->\n",
                encoding="utf-8",
            )
            task, _ = add_task_to_todo(repo_root, title="Middle", after_id="a")
            lines = todo.read_text(encoding="utf-8").splitlines()
            self.assertEqual(sum("[id: middle]" in ln for ln in lines), 1)
            self.assertIn("[id: a]", lines[1])
            self.assertIn("[id: middle]", lines[2])
            self.assertIn("[id: b]", lines[3])
            self.assertIn("a", task.depends_on)


if __name__ == "__main__":
    unittest.main()
