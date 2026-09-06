---
name: replan
description: Bootstrap task backlog or replan outstanding tasks with topological DAG sorting and WSJF waves. Short command alias for todo-navigator.
---

# Todo Replanner & Bootstrapper (/replan)

<!-- generated:alias-skill -->
When invoked, load and execute the **`todo-navigator`** skill:
1. Follow all instructions and guidelines in [`todo-navigator`](../todo-navigator/SKILL.md).
2. Run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py replan`.
3. If the backlog is empty, bootstrap initial tasks and goal from git context and specifications.
4. Highlight critical path bottlenecks (tasks blocking downstream items) and execution waves.
