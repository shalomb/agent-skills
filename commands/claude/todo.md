---
description: Navigate project tasks, inspect roadmap, and view or edit task cards in shadow cache
---

You are tasked with: Navigate project tasks, inspect roadmap, and view or edit task cards in shadow cache.

Follow the instructions in the `todo-navigator` skill:
1. FAST PATH: Immediately execute the requested command via `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py <subcommand> [args]` on the very first turn without reading SKILL.md.
2. To list task headings only, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py list [query]`.
3. To inspect the full roadmap, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py status`.
4. To view a specific task card, run `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py view <id>`.
5. To edit a task card interactively, execute `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py edit <id>`. If tmux is active, this automatically opens an interactive vim popup and blocks until the user exits vim.
6. IMPORTANT: If Antigravity sends this command to the background while the user edits in the popup, DO NOT poll or monitor it (no manage_task, no ps aux, no reading task logs). Simply inform the user the popup is open and STOP calling tools. The system will automatically wake you when the user finishes editing.
7. Support express operations (`done`, `P0-P3`, `add <text>`) via `uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py edit <id> <ops>`.
8. To add a task, manage dependencies, or visualize the DAG, run `add`, `dep`, or `graph`.
9. Keep chat responses concise: never dump the full 30+ line markdown card into chat on an edit command.

User request:
$ARGUMENTS
