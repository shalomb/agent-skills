# Guardrails Template

Copy this into every agent prompt / GEMINI.md as the preamble.
Replace `<project-specific>` sections with project context.

---

## Non-negotiable rules

### TDD — Farley Red-Green-Refactor
1. Write a FAILING test first. Run it. Confirm it fails for the right reason.
2. Write MINIMAL code to pass. No more.
3. Refactor. Tests must stay green.
4. Run full test suite before every commit.
5. Never commit red tests.

### BDD — Adzic Specification by Example
- Every user-visible behaviour gets a `.feature` file
- Scenarios use REAL examples with concrete values
- Format: Given / When / Then
- Never test implementation internals in BDD scenarios
- Bad: `When the user runs the command`
- Good: `When I run tfc state outputs db_endpoint --raw`

### Atomic Commit Protocol (ACP)
- One logical change per commit
- `type(scope): description` (Conventional Commits)
- Code + tests in the SAME commit — never split
- Each commit leaves tests green

### PR rules
- Push branch before PR: `git push -u origin <branch>`
- Fill in every section of the PR template — no prompts left visible
- Never commit directly to main

### Feedback output
- gemini: write to `~/.gemini/tmp/<worktree-name>/` NOT /tmp/
- pi: write to `/tmp/`

## Shell command style — no redundant cd
You are launched from the correct working directory (the script does `cd <worktree>` before starting you).
Never prefix commands with `cd /path/to/worktree &&` — run commands directly.
Bad:  `cd /home/user/project/.worktrees/feature && uv run pytest`
Good: `uv run pytest tests/ -q`
This keeps monitor output clean and readable for humans watching the panes.

## Project-specific context
<project-specific: test runner command, pre-existing failures, key files, etc.>
