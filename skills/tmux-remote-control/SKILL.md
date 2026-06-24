---
name: tmux-remote-control
description: "Remote control tmux sessions for interactive CLIs by sending keystrokes and scraping output. Use when you need to interact with a long-running process, REPL, or debugger. Triggers on: 'tmux', 'send keys', 'interact with pane', 'gdb', 'python repl'."
---

# Tmux Skill

Simple, reliable tmux orchestration.  Defaults to the **current session** the agent is running in.

## Critical Rules

1. **Current session by default.**  All scripts auto-resolve the current tmux session via `$TMUX`.  Do NOT target other sessions unless the user explicitly names one.
2. **Never create or destroy sessions** unless explicitly instructed.
3. **Never switch to a random session.**  If you need a pane, create a new window in the _current_ session (`tmux new-window`) rather than hijacking another session.
4. **Never target the agent's own pane.**  `tmux-exec.sh` refuses if you try (detected via `$TMUX_PANE`).
5. **Respect busy panes.**  `tmux-exec.sh` tracks running commands.  If a pane is busy it will refuse with details (command, elapsed time).  Do not send `C-c` unless the user asks — instead wait and retry, or use a different pane.
6. **No default timeout.**  `tmux-exec.sh` waits until the command finishes.  Only pass `-t` when you have a good reason and understand that timeout ≠ cancellation — the command keeps running.
7. **Verify before acting.**  Use `tmux-list.sh` to confirm targets exist (it also shows busy state).

## Pane Targeting

**Format**: `{session}:{window}.{pane}` or `{window}.{pane}` (current session implied)

| Target | Meaning |
|--------|---------|
| `1.0` | Window 1, Pane 0 — **current session** (preferred) |
| `code:0.0` | Window 0, Pane 0 in session "code" (only if user asks) |

## Script Location

All scripts live in the `scripts/` directory **alongside this SKILL.md file**.
The canonical source is `~/shalomb/agent-skills/skills/tmux/scripts/`, hardlinked
into each agent's skill directory (e.g. `{SKILLS_DIR}/tmux-remote-control/scripts/`,
`~/.claude/skills/tmux/scripts/`).

The skill file's own location tells you where the scripts are. When this skill is
loaded, note the path it was read from and derive the script directory from it:
```
<skill-file-path>  →  $(dirname <skill-file-path>)/scripts/
```
For example, if this file was read from `{SKILLS_DIR}/tmux-remote-control/SKILL.md`,
the scripts are at `{SKILLS_DIR}/tmux-remote-control/scripts/`.

**Never use `./scripts/`** — that resolves against the agent's current working
directory (the project repo), not the skill directory.

## 1. Execute (`scripts/tmux-exec.sh`)

Primary tool.  Sends a command, waits for completion, returns output + exit code.

### Shell Mode (default)
```bash
# SKILL_SCRIPTS = $(dirname <path-to-this-SKILL.md>)/scripts
$SKILL_SCRIPTS/tmux-exec.sh "1.0" "ls -la"
```

### Interactive Mode (`-w PATTERN`)
Sends keys and waits for a regex (e.g. a REPL prompt):
```bash
$SKILL_SCRIPTS/tmux-exec.sh -w '>>> ' "1.0" "print('hello')"
```

### Options
| Flag | Default | Meaning |
|------|---------|---------|
| `-t SEC` | none (wait forever) | Timeout.  On expiry the command is **still running** and the pane is marked busy. |
| `-w PATTERN` | — | Interactive mode: wait for regex instead of exit-code markers. |
| `-S PATH` | — | Custom tmux socket. |

### Busy-pane protection

If a previous command is still running (e.g. after a timeout), the script detects this from its state file before proceeding:
- **Command finished** → state is cleared, new command proceeds.
- **Command still running** → error with command name, elapsed time, and recovery options.

## 2. Clear Stuck State (`scripts/tmux-clear-state.sh`)

Use when a pane's command was killed, OOM-ed, or hung and `tmux-exec.sh` refuses
with "pane is busy" even though nothing is running.

```bash
# List all panes with recorded busy state (plus orphaned temp files)
$SKILL_SCRIPTS/tmux-clear-state.sh

# Clear state for a specific pane (current session)
$SKILL_SCRIPTS/tmux-clear-state.sh 1.0

# Clear state for a fully-qualified target
$SKILL_SCRIPTS/tmux-clear-state.sh myses:2.1

# Clear ALL stale state: dead panes + orphaned temp files
$SKILL_SCRIPTS/tmux-clear-state.sh --all

# Clear only orphaned out/ec temp files
$SKILL_SCRIPTS/tmux-clear-state.sh --orphans

# Dry-run: show what would be removed
$SKILL_SCRIPTS/tmux-clear-state.sh --dry-run --all
```

What it clears per pane:
- **State file** (`<STATE_DIR>/<pane_num>`) — the "busy" record
- **Lock file** (`<STATE_DIR>/<pane_num>.lock`) — the flock guard
- **Temp files** (`out.*`, `ec.*`) referenced in the state file

`--all` additionally removes orphaned `out.*`/`ec.*` files not referenced by any state.

## 3. Read (`scripts/tmux-read.sh`)

Read-only scrape of the last command's output.  Warns if the pane is busy.

```bash
$SKILL_SCRIPTS/tmux-read.sh "1.0"
```

| Flag | Default | Meaning |
|------|---------|---------|
| `-n LINES` | 2000 | History depth. |
| `-S PATH` | — | Custom tmux socket. |

## 4. List (`scripts/tmux-list.sh`)

JSON inventory of all panes.  Current session is listed first and marked.
Shows `"busy": true/false` per pane with command and elapsed time.

```bash
$SKILL_SCRIPTS/tmux-list.sh
```

Use this to find idle panes before executing commands.

## Interactive Tool Notes

### Python REPL
Always set `PYTHON_BASIC_REPL=1` — the fancy readline REPL breaks send-keys:
```bash
$SKILL_SCRIPTS/tmux-exec.sh "1.0" 'PYTHON_BASIC_REPL=1 python3 -q'
$SKILL_SCRIPTS/tmux-exec.sh -w '>>> ' "1.0" "print('hello')"
```

### Debuggers
Default to `lldb` (unless user says gdb).  Disable paging before sending commands.

### Long output
Redirect to a file to avoid tmux scrollback limits:
```bash
$SKILL_SCRIPTS/tmux-exec.sh "1.0" 'long-command > /tmp/out.txt 2>&1'
$SKILL_SCRIPTS/tmux-exec.sh "1.0" 'cat /tmp/out.txt'
```

## Error Handling

1. `$SKILL_SCRIPTS/tmux-read.sh` — inspect what's in the pane
2. `$SKILL_SCRIPTS/tmux-list.sh` — confirm target exists, check busy state
3. Test with `echo test` first
4. For complex issues read `references/error-handling-and-debugging.md`
