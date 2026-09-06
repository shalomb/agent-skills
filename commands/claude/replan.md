---
description: Bootstrap task backlog or replan outstanding tasks with topological DAG sorting and WSJF waves
---

You are tasked with: Bootstrap task backlog or replan outstanding tasks with topological DAG sorting and WSJF waves.

Follow the instructions in the `todo-navigator` skill:
1. Run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py replan`.
2. If the backlog is empty, bootstrap initial tasks and goal from git context and specifications.
3. Highlight critical path bottlenecks (tasks blocking downstream items) and execution waves.

User request:
$ARGUMENTS
