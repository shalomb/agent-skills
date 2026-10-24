---
name: tmux-remote-control
description: "Remote control tmux sessions for interactive CLIs by sending keystrokes and scraping output. Use when you need to interact with a long-running process, REPL, or debugger. Triggers on: 'tmux', 'send keys', 'interact with pane', 'gdb', 'python repl'."
---

# Tmux Skill

Simple, reliable tmux orchestration.  Defaults to the **current session** the agent is running in.

## Critical Rules

1. **Current session by default.**  All scripts auto-resolve the current tmux session via `$TMUX`.  Do NOT target other sessions unless the user explicitly names one.
2. **Never create or destroy sessions** unless explicitly instructed.
3. **Never switch to a random session.**  If you need a pane, create a **named** window or pane in the _current_ session (see [Windows and panes](#windows-and-panes)) rather than hijacking another session.
4. **Never target the agent's own pane.**  `tmux-exec.sh` refuses if you try (detected via `$TMUX_PANE`).
5. **Respect busy panes.**  If a pane is busy, `tmux-exec.sh` refuses with details.  Do not send `C-c` unless the user asks — wait and retry, or use a different pane.
6. **No default timeout.**  `tmux-exec.sh` waits until the command finishes.  Timeout ≠ cancellation — the command keeps running.
7. **Verify before acting.**  Use `tmux-list.sh` to confirm targets exist (it also shows busy state).
8. **`tmux-exec.sh` runs in a subshell.**  Env changes (`export`, `source creds`, `eval $(...)`) do not persist in the pane — see `references/exec.md`.

## Windows and panes

Everything you create must be **named** with a very terse, purpose-describing label (`tf-plan`, `gdb`, `api-logs`) — bare numbers make the user hunt.  Create detached, capture the printed target, reuse an existing one of the same name, and close what you created when done.  Details, naming rules and the creation commands: `references/windows-and-panes.md`.

## Pane targeting

**Format**: `{session}:{window}.{pane}` or `{window}.{pane}` (current session implied)

| Target | Meaning |
|--------|---------|
| `1.0` | Window 1, Pane 0 — **current session** (preferred) |
| `code:0.0` | Window 0, Pane 0 in session "code" (only if user asks) |

## Scripts

Scripts live in `scripts/` **alongside this SKILL.md**.  Derive the directory from where you read this file — never use `./scripts/` (that resolves against the project repo, not the skill):

```
SKILL_SCRIPTS=$(dirname <skill-file-path>)/scripts
```

| Script | Use it to | Read |
|--------|-----------|------|
| `tmux-exec.sh [-d] [-w PAT] [-t SEC] TARGET CMD` | Run a command (or drive a REPL) and get output + exit code | `references/exec.md` |
| `tmux-read.sh TARGET` | Scrape a pane's last output (read-only) | `references/state-and-inspection.md` |
| `tmux-list.sh` | JSON inventory of panes with busy/idle state | `references/state-and-inspection.md` |
| `tmux-clear-state.sh` | Clear a stale "pane is busy" record | `references/state-and-inspection.md` |
| `tmux-dispatch.sh [-w SEC] TARGET BRIEF` | Hand a task to a *peer agent* in another pane | `references/dispatch.md`, `references/orchestrating-peer-agents.md` |

Quick start:
```bash
$SKILL_SCRIPTS/tmux-list.sh                      # find an idle pane
$SKILL_SCRIPTS/tmux-exec.sh "1.0" "ls -la"       # run a command
$SKILL_SCRIPTS/tmux-read.sh "1.0"                # re-read its output
```

## Read more when…

- Launching a REPL/debugger, or tuning `-w`/`-d`/`-t` → `references/exec.md`, `references/interactive-tools.md` (Python REPL needs `PYTHON_BASIC_REPL=1`; use `-d`)
- A pane is stuck "busy" → `references/state-and-inspection.md`
- Delegating to another agent pane → `references/dispatch.md`
- Anything fails or looks wrong → `references/error-handling-and-debugging.md` (first: `tmux-read.sh`, `tmux-list.sh`, try `echo test`)
