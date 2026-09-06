---
name: todo
description: Navigate project tasks, inspect roadmap, and view or edit task cards in shadow cache. Short command alias for todo-navigator.
---

# Todo Navigator (/todo)

<!-- generated:alias-skill -->
When invoked, load and execute the **`todo-navigator`** skill:
1. Follow all instructions and guidelines in [`todo-navigator`](../todo-navigator/SKILL.md).
2. Inspect the project roadmap using `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py status`.
3. To view a specific task card, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py view <id>`.
4. To edit a task card: support express operations (`done`, `P0-P3`, `add <text>`) via `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py edit <id> <ops>`.
5. For interactive editing, stage the task card as an artifact in `<appDataDir>/brain/<conversation-id>/task-<id>.md` with UserFacing: true, and direct the user to run `/artifact` or click the link.
6. Keep chat responses concise: never dump the full 30+ line markdown card into chat on an edit command.
