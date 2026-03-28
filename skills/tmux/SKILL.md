---
name: tmux
description: "Remote control tmux sessions for interactive CLIs (python, gdb, etc.) by sending keystrokes and scraping pane output."
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

## 1. Execute (`scripts/tmux-exec.sh`)

Primary tool.  Sends a command, waits for completion, returns output + exit code.

### Shell Mode (default)
```bash
./scripts/tmux-exec.sh "1.0" "ls -la"
```

### Interactive Mode (`-w PATTERN`)
Sends keys and waits for a regex (e.g. a REPL prompt):
```bash
./scripts/tmux-exec.sh -w '>>> ' "1.0" "print('hello')"
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

## 2. Read (`scripts/tmux-read.sh`)

Read-only scrape of the last command's output.  Warns if the pane is busy.

```bash
./scripts/tmux-read.sh "1.0"
```

| Flag | Default | Meaning |
|------|---------|---------|
| `-n LINES` | 2000 | History depth. |
| `-S PATH` | — | Custom tmux socket. |

## 3. List (`scripts/tmux-list.sh`)

JSON inventory of all panes.  Current session is listed first and marked.
Shows `"busy": true/false` per pane with command and elapsed time.

```bash
./scripts/tmux-list.sh
```

Use this to find idle panes before executing commands.

## Interactive Tool Notes

### Python REPL
Always set `PYTHON_BASIC_REPL=1` — the fancy readline REPL breaks send-keys:
```bash
./scripts/tmux-exec.sh "1.0" 'PYTHON_BASIC_REPL=1 python3 -q'
./scripts/tmux-exec.sh -w '>>> ' "1.0" "print('hello')"
```

### Debuggers
Default to `lldb` (unless user says gdb).  Disable paging before sending commands.

### Long output
Redirect to a file to avoid tmux scrollback limits:
```bash
./scripts/tmux-exec.sh "1.0" 'long-command > /tmp/out.txt 2>&1'
./scripts/tmux-exec.sh "1.0" 'cat /tmp/out.txt'
```

## Error Handling

1. `tmux-read.sh` — inspect what's in the pane
2. `tmux-list.sh` — confirm target exists, check busy state
3. Test with `echo test` first
4. For complex issues read `references/error-handling-and-debugging.md`
