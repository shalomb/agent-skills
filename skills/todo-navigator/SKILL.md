---
name: todo-navigator
description: Use when navigating project tasks, selecting next priorities, recalling previous work, replanning with dependency resolution, or managing shadow task cards without repo pollution.
---

# Todo Navigator

Lightweight, zero-repo-pollution task navigator and backlog engine for autonomous AI agents and developers. Master checklists (`TODO.md`) and secondary execution cards (`tasks/<id>.md`) live in a dedicated shadow directory (`~/.cache/agent-skills/todos/<repo_slug>/`), pulling granular acceptance criteria only as the execution cursor reaches each task.

## Key Capabilities

1. **Zero Repo Pollution**: Backlogs and task cards live outside git in `${XDG_CACHE_HOME:-~/.cache}/agent-skills/todos/<repo_slug>/`.
2. **Task Lifecycle Management**: Create tasks (`todo add`), wire dependencies (`todo dep add/rm`), and filter headings (`todo list [query]`).
3. **Topological DAG Waves & Cycle Detection**: Resolves `[depends: id1, id2]` tags, detects circular dependencies, and groups tasks into execution waves.
4. **Lightweight WSJF**: Ranks unblocked tasks by $\text{WSJF} = \frac{\text{Cost of Delay}}{\text{Job Size}}$.
5. **DAG Visualization**: Visualizes dependencies via ASCII tree in terminal or Mermaid flowchart diagrams (`todo graph [--mermaid]`).
6. **Context Recall (`/prev`)**: Instant 3-line factual recap of the last completed item and git commit.
7. **Progressive Disclosure (`/next`)**: Pulls the highest-leverage unblocked task and automatically stages its acceptance card.
8. **Interactive & Express Editing (`/todo edit`)**: Opens candidate card(s) in a blocking tmux popup (`vi file1 file2...`), or applies express edits (`done`, `P0-P3`, `add <criterion>`).

## Quick CLI Reference

```bash
# Heading-only listing (all or smart filtered)
todo list
todo list <query>
todo list --id

# Task creation and dependency wiring
todo add "Task Title" [--prio P0-P3] [--section <heading>] [--after <task-id>] [--depends <id1,id2>]
todo dep add <task-id> <prerequisite-id>
todo dep rm <task-id> <prerequisite-id>

# Visualization
todo graph             # ASCII execution waves tree
todo graph --mermaid   # Mermaid flowchart syntax

# Navigation & Status
todo status            # Status matrix and WSJF rankings
todo next              # Top WSJF unblocked task card
todo prev              # 3-line recent work recall
todo replan            # Topologically sort backlog by WSJF waves

# Inspection & Editing
todo view <query>      # View card (smart partial matching)
todo edit              # Edit master TODO.md in Vim tmux popup
todo edit <query>      # Edit card in Vim (multi-file args in tmux popup)
todo edit <query> done # Express mark done
todo edit <query> add <text> # Express add acceptance criterion
```

## Detailed References

- [CLI Reference & Options](references/cli-reference.md)
- [Task Card Schema & BDD Specification](references/task-card-schema.md)
- [Evaluation Test Cases](evals/evals.json)
