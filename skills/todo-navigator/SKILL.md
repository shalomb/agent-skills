---
name: todo-navigator
description: Use when navigating project tasks, selecting next priorities, recalling previous work, replanning with dependency resolution, or managing shadow task cards without repo pollution.
---

# Todo Navigator

## Overview
A lightweight, zero-repo-pollution task navigator. It keeps master checklists (`TODO.md`) and secondary execution context cards (`tasks/<id>.md`) in an external shadow directory (`~/.cache/agent-skills/todos/<repo_slug>/`), using progressive disclosure to pull detailed acceptance criteria only when the execution cursor reaches each task.

## Key Capabilities

1. **Zero Repo Pollution**: By default, backlogs and task cards live outside git in `${XDG_CACHE_HOME:-~/.cache}/agent-skills/todos/<repo_slug>/`. No `.gitignore` clutter, no branch merge conflicts.
2. **Topological DAG Sorting**: Resolves `[depends: id1, id2]` tags, detects dependency cycles, and organizes tasks into execution waves.
3. **Lightweight WSJF**: Ranks unblocked tasks by $\text{WSJF} = \frac{\text{Value / Leverage (1..5)}}{\text{Effort / Size (1..5)}}$.
4. **Context Recall (`/prev`)**: Instant 3-line factual recap of the last completed item and git commit for quick orientation when switching sessions.
5. **Progressive Disclosure (`/next`)**: Pulls the highest-leverage unblocked task and automatically pages in its acceptance criteria card.
6. **TTY-Safe Editor Launching (`/todo edit`)**: Spawns `$EDITOR` in interactive sessions, or provides direct `file://` links in non-interactive agent environments.
7. **Reinforcement Learning (`/todo learn`)**: Appends feedback and discoveries to `## Reinforcements` to guide future tasks.

## Commands Reference

| Slash Command | Full Command | Action |
| :--- | :--- | :--- |
| **`/replan`** | `todo_engine.py replan` | Bootstrap backlog if empty; otherwise resolve DAG, calculate WSJF waves, and display roadmap. |
| **`/next`** | `todo_engine.py next` | Pull highest-priority unblocked task and page in its secondary card. |
| **`/prev`** | `todo_engine.py prev` | 3-line factual summary of last completed item (`- [x]`) and latest git commit. |
| **`/todo`** | `todo_engine.py status` | Show current project task roadmap, completion ratio, and active waves. |
| **`/todo view [id]`** | `todo_engine.py view [id]` | View `TODO.md` or a specific task card in `./tasks/<id>.md`. |
| **`/todo edit [id]`** | `todo_engine.py edit [id]` | Open `TODO.md` or a task card in `$EDITOR` (or surface direct file link). |
| **`/todo learn <msg>`**| `todo_engine.py learn <msg>` | Append durable learning to `## Reinforcements` ledger. |

## Quick Start / Script Invocations

All commands can be invoked via the bundled engine script:

```bash
# Display roadmap and waves
uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py replan

# Pull next unblocked task with its secondary card
uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py next

# Review what was just worked on
uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py prev

# View a task card
uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py view core-engine

# Edit in $EDITOR (TTY-safe)
uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py edit core-engine

# Add durable learning
uv run {SKILLS_DIR}/todo-navigator/scripts/todo_engine.py learn "Check UTC timestamps on tokens to prevent clock skew"
```

## Directory Structure

```text
~/.cache/agent-skills/todos/<repo_slug>/
├── TODO.md                     # Master project task list & reinforcements
└── tasks/                      # Granular task cards
    ├── core-engine.md          # BDD acceptance criteria, target files, scratchpad
    └── slash-commands.md
```

`<repo_slug>` is derived deterministically from the absolute path of the git root (e.g., `home-unop-projects-shalomb-agent-skills`).

## Format Guidelines for `TODO.md`

Tasks follow standard GitHub-flavored Markdown checkboxes with optional tags:

```markdown
# Project Tasks
Target Repository: `/home/user/my-project`

## Goal
Implement and verify feature X.

## Outstanding Tasks
- [x] Initial design and spikes [id: init-design] [P1] [wsjf: 5.0] ([card](./tasks/init-design.md))
- [ ] Core module implementation [id: core-mod] [P1] [wsjf: 4.5] [depends: init-design] ([card](./tasks/core-mod.md))
- [ ] Integration tests [id: int-tests] [P2] [wsjf: 3.0] [depends: core-mod] ([card](./tasks/int-tests.md))

## Reinforcements
- 2026-09-06: Keep TODO.md in shadow directory to avoid git clutter.
```
