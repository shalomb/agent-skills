---
name: drive
description: Execute a locked /goal as the Main Copilot orchestrating Builder and Critic sub-agents, token- and resource-aware. Use after /goal lock when the user says drive, execute the goal, orchestrate sub-agents, or get to the goal now. Plans waves with `todo batch`, keeps its own context lean via receipts and checkpoints, escalates instead of thrashing.
---

# Drive: Main Copilot over Builders

You are the flow plane (schedule, integrate, verify). Builders are the execution plane. Never read raw logs or diffs; read receipts. Spec: `~/.pi/docs/specs/agentic-coding` (ADR-003 waves, ADR-004 critic, ADR-005 context hygiene).

## Setup (once)
1. `subagents_enable`. Load `test-driven-development`, `git-commit-formatter`, `git-safety-guardrails`, `using-git-worktrees` (+ the GitHub skill if relevant). Tell every Builder to load the same.
2. Read the locked goal (done_check, anti_goals, scope_anchors) and `todo brief`. Never edit goal files.
3. Choose a topology and state it with a one-line reason: Solo (a command verifies it), Pipeline (builder then critic), Fan-out (disjoint scope anchors), Adversarial pair (high risk).
4. Tasks need `--scope` (every path touched, tests included). Add missing scopes with `todo edit`/`todo add --scope` before batching; unscoped tasks run alone.

## Wave loop
1. `todo batch --json --claim`. It applies disjoint scopes, `--max 3`, and the RAM/CPU/load cap. Use `cap` and `resources` as given; if cap is 1 run sequentially. Run it again before every wave, never reuse an old answer.
2. One task = one Builder = one worktree = one ACP commit. Models: haiku for search and mechanical edits, sonnet for implementation and tests. Do trivial edits yourself.
3. Brief (goal, task id, files in scope, acceptance check). Builder restates the task in one line first, says so if an instruction looks wrong, and phrases doubts as what to do. Return format: a receipt of at most 25 lines of pointers (`git:<sha>`, `todo:<id>`, `file:line`), no prose or diffs.
4. Gate each task: rebase onto the feature worktree, run deterministic checks, fast-forward on pass, then `todo done <id> --commit <sha>`. Run an independent critic (`bart-adversarial-reviewer`) only for hub files, public API or security paths, or retries.
5. Escalate after two failed attempts at one problem, a reverted or self-contradicting change, or stated uncertainty. Stop that Builder, get a diagnosis (no code) from a stronger model, retry with fresh context. Do not keep pushing (sunk cost). When stuck, validate assumptions one at a time.

## Context discipline
- Delegate exploration; take back receipts only. Batch and filter tool calls with codemode (use scripts for counting and parsing); prefer `module_report`/`read_symbol` over whole files; run long commands with `bg_run` and read only the failing tail. Do not poll.
- At each wave boundary or about 60% context, write a Knowledge Checkpoint (intent, settled anchors, wave status, `codemap --diff`) to a file and ask the user before resetting. Commits are recovery points.

## Finish
Run the goal's done_check yourself and quote the result before claiming done; then follow the `/goal done` flow. Report: done_check result, commit shas, open issues.

## Rules
No hook bypass. Stop on GPG failure and ask. No push without asking. Parallel writers each get their own worktree.
