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

# Multi-agent coordination (claims are tags on the task line, file-locked)
todo claim [id]        # Claim id, or the next ready task nobody holds; prints the card
todo done <id> --commit HEAD   # Tick it, record time + commit, clear the claim
todo release <id>      # Give a claim back (--force for someone else's)
todo brief [--json]    # One-line summary: open, claimed by others, yours, next ready

# Wave scheduling for parallel builders (deterministic, no LLM)
todo add "Title" --scope src/x.py,tests/test_x.py   # declare every path the task touches, tests included
todo batch [--max 3] [--json] [--claim] [--no-resources]
#   Picks <=3 ready tasks (WSJF order) with pairwise-disjoint scopes; explains each skip.
#   Dirs end in "/", globs allowed. A task with no scope runs alone. In-flight claims hold their scope and a slot.
#   Cap = min(--max, 1 per 2 GB free RAM, nproc/2); 1 when load1 >= 70% of nproc. --claim claims as <owner>/<id>.
```

## Agent protocol (any agent, any harness)

1. Set `TODO_OWNER` to something unique per agent (`pi:<session>`, `mux:<worktree>`); otherwise it defaults to `user@host:<ppid>`.
2. Before starting work in a repo with a backlog, run `todo brief`. If the request matches an open task, `todo claim <id>`; if the user says "next" or "go", `todo claim` with no id.
3. Never work a task claimed by someone else (`[wip: other]`); claims older than 4 h count as stale and can be taken over.
4. Implement against the card's acceptance criteria. After the commit that satisfies them: `todo done <id> --commit HEAD`. Keep backlog ids out of commit messages, branch names and PRs: the backlog is private bookkeeping and shared repos must not depend on it; the link lives only in the task line (`[commit: <sha>]`).
5. If you stop without finishing: `todo release <id>`.
6. Never tick checkboxes by editing TODO.md directly; use the CLI so claims, locking and timestamps stay consistent.

## Detailed References

- [CLI Reference & Options](references/cli-reference.md)
- [Task Card Schema & BDD Specification](references/task-card-schema.md)
- [Evaluation Test Cases](evals/evals.json)
