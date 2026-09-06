"""Unit tests for domain models."""

from __future__ import annotations

import unittest

from todo_navigator.models import Task


class TestTaskModel(unittest.TestCase):
    def test_wsjf_score_calculation(self) -> None:
        t1 = Task(id="t1", title="Task 1", wsjf_cost=2.0, wsjf_size=1.0)
        self.assertEqual(t1.wsjf_score, 2.0)

        t2 = Task(id="t2", title="Task 2", wsjf_cost=5.0, wsjf_size=2.0)
        self.assertEqual(t2.wsjf_score, 2.5)

        t3 = Task(id="t3", title="Task 3", wsjf_cost=1.0, wsjf_size=0.0)
        self.assertEqual(t3.wsjf_score, 10.0)  # max(size, 0.1)

    def test_to_markdown_line(self) -> None:
        t = Task(
            id="auth-jwt",
            title="Implement JWT Authentication",
            completed=False,
            priority="P1",
            depends_on=["db-setup"],
            wsjf_cost=3.0,
            wsjf_size=2.0,
        )
        line = t.to_markdown_line()
        self.assertEqual(
            line,
            "- [ ] Implement JWT Authentication <!-- [id: auth-jwt] [prio: P1] [depends: db-setup] [wsjf: 3.0/2.0] -->",
        )

    def test_to_markdown_line_completed(self) -> None:
        t = Task(id="setup", title="Setup Environment", completed=True, priority="P0")
        line = t.to_markdown_line()
        self.assertEqual(line, "- [x] Setup Environment <!-- [id: setup] [prio: P0] -->")

    def test_task_section_field(self) -> None:
        t = Task(id="t1", title="Task 1", section="🔴 CRITICAL")
        self.assertEqual(t.section, "🔴 CRITICAL")


if __name__ == "__main__":
    unittest.main()
