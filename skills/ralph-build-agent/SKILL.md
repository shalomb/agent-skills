---
name: ralph-build-agent
description: >
  Build Agent — burns down a TODO.md task list end to end, unattended. Use when
  there is an existing TODO.md to execute: reads it as the plan, implements each
  task, updates task status on completion, creates an Atomic Commit Protocol
  (ACP) commit per task, then progresses to the next until the list is done.
  Implementation uses red-green-refactor TDD with INVEST decomposition, a Farley
  per-test checklist, and Conventional Commits. Not for one-off changes with no
  task list — for those use `test-driven-development`. Triggers on: 'ralph',
  'build agent', 'burn down the TODO', 'work through TODO.md', 'execute the
  backlog'.
metadata:
  version: 1.1.0
  tags:
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
3. Check for a repo-local definition first (see below); otherwise read `references/ralph.md` for the full
   persona, TDD rules, Farley checklist, and execution flow.
4. Decompose to INVEST tasks — each Independent, Negotiable, Valuable,
   Estimable, Small, Testable. Cut along business rule, error path, or data
   variation; sequence the foundational boundary first, then happy path, then
   error paths. Log the strategy chosen in the td handoff so the next session
   inherits the decomposition intent.
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
- `references/ralph.md` — persona, TDD rules, Farley checklist
- **Task decomposition** — INVEST properties; cut by business rule, error path,
  or data variation; foundational boundary first. Record the strategy in each
  td handoff.
- **ACP — Atomic Commit Protocol**: one task = one atomic commit. Full spec:
  `skills/git-commit-formatter/references/acp-spec.md`, or use the
  `git-commit-formatter` skill.
- `skills/farley-tdd/docs/reference/farley-index.md` — per-test quality checklist

## Repo-local definitions take precedence

Before adopting the persona, check whether this repository defines its own
Ralph agent:

```bash
{SKILLS_DIR}/_common/scripts/find-repo-agents.sh ralph
```

Searches `.github/`, `.claude/`, `.gemini/` and `.agents/` for both `agents/*.md`
definitions and repo-local `skills/*/SKILL.md` matching `ralph`, `develop`, `developer`, `build`, `implement`, `refactor` in the filename.

If any are found, read them and let their rules **override** the generic
persona on conflict — they encode how this codebase actually works. If none
are found, use `references/ralph.md` alone.

## Triggers
- "ralph"
- "build agent"
- "TODO burndown"
- "burn down the TODO"
- "implement the TODO"
- "work through TODO.md"
- "execute the backlog"
- "implement each task"
- "work through the tasks"

### Not this skill

| If the user wants to… | Use |
| :-------------------- | :-- |
| Write one feature or fix test-first | `test-driven-development` |
| Audit an existing test suite | `farley-tdd` |
| Format a commit / understand ACP | `git-commit-formatter` |
| Run several agents across worktrees | `agent-mux` |

## Execution
Run the Springfield Go agent for the current task:
```bash
just ralph
```
Alternatively, for a specific task:
```bash
just agent ralph "Your task description here"
```
