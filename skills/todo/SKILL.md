---
name: todo
description: Navigate project tasks, inspect roadmap, and view or edit task cards in shadow cache. Short command alias for todo-navigator.
---

# Todo Navigator (/todo)

<!-- generated:alias-skill -->
When invoked, load and execute the **`todo-navigator`** skill:
1. Follow all instructions and guidelines in [`todo-navigator`](../todo-navigator/SKILL.md).
2. FAST PATH: Immediately execute the requested command via `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py <subcommand> [args]` on the very first turn without reading SKILL.md.
3. To list task headings only, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py list [query]`.
4. To inspect the full roadmap, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py status`.
5. To view a specific task card, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py view <id>`.
6. To edit a task card interactively, execute `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py edit <id>`. If tmux is active, this automatically opens an interactive vim popup and blocks until the user exits vim.
7. IMPORTANT: If Antigravity sends this command to the background while the user edits in the popup, DO NOT poll or monitor it (no manage_task, no ps aux, no reading task logs). Simply inform the user the popup is open and STOP calling tools. The system will automatically wake you when the user finishes editing.
8. Support express operations (`done`, `P0-P3`, `add <text>`) via `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py edit <id> <ops>`.
9. To add a task, manage dependencies, or visualize the DAG, run `add`, `dep`, or `graph`.
10. Keep chat responses concise: never dump the full 30+ line markdown card into chat on an edit command.
