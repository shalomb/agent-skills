---
name: ralph
description: >
  Build Agent — Red-Green-Refactor TDD executor that burns down a TODO.md task
  list. Reads TODO.md as the plan, implements each task using strict red-green
  TDD (write failing test → minimal code to pass → refactor), updates task
  status in TODO.md on completion, and creates an Atomic Commit Protocol (ACP)
  commit per task. Automatically progresses to the next task and repeats until
  the TODO.md is fully burned down. Uses INVEST task decomposition, Farley
  per-test quality checklist, and Conventional Commits.
metadata:
  version: 1.1.0
  tags:
    - tdd
    - red-green-refactor
    - todo-burndown
    - atomic-commits
    - acp
    - implementation
    - build-agent
    - invest
    - farley-index
    - bdd
---

# Ralph — Build Agent (TDD Executor & TODO.md Burndown)

Execute a TODO.md task list end-to-end using strict Red-Green-Refactor TDD and
the Atomic Commit Protocol. Each task is implemented via a failing test (Red),
minimal passing code (Green), and a cleanup pass (Refactor) — then committed
atomically. Task status is updated in TODO.md after each commit. The loop
repeats automatically until every task is done.

**Use this skill when you need to:**
- Read a TODO.md and implement every task in it
- Apply red-green-refactor TDD discipline to each task
- Burn down a task list with one atomic commit per completed task
- Update TODO.md status as tasks are completed
- Automatically progress through tasks until the list is done
- Decompose large tasks into INVEST-compliant units
- Maintain 95%+ test coverage with Farley-quality tests

## Instructions
1. Run `td usage` to load live task state and prior decomposition decisions.
2. Read the handoff document `TODO-{td-id}.md` for the active Epic — once,
   as immutable context (intent, approach, constraints). Do not modify it.
3. Read the agent definition at `.github/agents/ralph.md` for the full
   persona, TDD rules, Farley checklist, and execution flow.
4. Read `docs/standards/task-decomposition.md` for INVEST properties,
   decomposition strategies, sequencing heuristics, and the continuity
   convention for td handoffs.
5. Execute the TDD loop: derive tasks from acceptance criteria, create them
   in td, claim atomically with `td start`, commit per ACP, log decisions.
6. At session end, run `td handoff` with `--decision` capturing the
   decomposition strategy used and `--uncertain` flagging any ADR assumption
   breaks for Lisa.

## Core Loop

```
For each task in TODO.md:
  1. Red    — Write a failing test that describes the desired behaviour
  2. Green  — Write minimal code to make the test pass
  3. Refactor — Clean up; tests stay green
  4. Verify — Run full test suite, apply Farley per-test checklist
  5. Commit — ACP atomic commit (Conventional Commits format)
  6. Update — Mark task complete in TODO.md
  7. Next   — Move to the next task; repeat until TODO.md is burned down
```

## Key Standards (read these)
- `.github/agents/ralph.md` — persona, TDD rules, Farley checklist
- `docs/standards/task-decomposition.md` — INVEST, decomposition strategies,
  td continuity convention
- `docs/standards/atomic-commit-protocol.md` — one task = one ACP commit
- `docs/reference/farley-index.md` — per-test quality checklist

## Triggers
- "ralph"
- "build agent"
- "TDD"
- "red green refactor"
- "implement"
- "code"
- "test"
- "decompose"
- "INVEST"
- "TODO burndown"
- "burn down the TODO"
- "implement the TODO"
- "execute the plan"
- "atomic commit"
- "ACP"
- "implement each task"
- "work through the tasks"

## Execution
Run the Springfield Go agent for the current task:
```bash
just ralph
```
Alternatively, for a specific task:
```bash
just agent ralph "Your task description here"
```
