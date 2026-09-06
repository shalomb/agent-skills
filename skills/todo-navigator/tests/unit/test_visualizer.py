"""Unit tests for visualizer functions."""

from __future__ import annotations

import unittest

from todo_navigator.models import Task
from todo_navigator.visualizer import (
    format_task_heading,
    render_ascii_tree,
    render_mermaid_graph,
)


class TestVisualizer(unittest.TestCase):
    def test_format_task_heading(self) -> None:
        t = Task(id="core", title="Core Engine", priority="P1", wsjf_cost=2.0, wsjf_size=1.0)
        heading = format_task_heading(t)
        self.assertIn("[ ]", heading)
        self.assertIn("[P1]", heading)
        self.assertIn("[core]", heading)
        self.assertIn("Core Engine", heading)
        self.assertIn("WSJF: 2.0", heading)

    def test_render_ascii_tree(self) -> None:
        tasks = [
            Task(id="setup", title="Setup", completed=True),
            Task(id="build", title="Build", depends_on=["setup"]),
        ]
        tree = render_ascii_tree(tasks)
        self.assertIn("Execution Waves", tree)
        self.assertIn("Wave 1", tree)
        self.assertIn("build", tree)
        self.assertIn("Completed Tasks", tree)
        self.assertIn("setup", tree)

    def test_render_mermaid_graph(self) -> None:
        tasks = [
            Task(id="t1", title="Task 1", completed=True),
            Task(id="t2", title="Task 2", depends_on=["t1"]),
        ]
        mermaid = render_mermaid_graph(tasks)
        self.assertIn("```mermaid", mermaid)
        self.assertIn("graph TD", mermaid)
        self.assertIn("t1 --> t2", mermaid)
        self.assertIn("class t1 done", mermaid)


if __name__ == "__main__":
    unittest.main()
