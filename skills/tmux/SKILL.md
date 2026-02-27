---
name: tmux
description: Execute commands and read output from specific tmux panes. Use this to orchestrate shell commands or monitor interactive tools (Python, GDB) in a user-provided tmux environment.
---

# Tmux Skill

Simple, reliable tmux orchestration. Use this skill to interact with a specific tmux pane provided by the user.

## 1. Execute and Sync (`scripts/tmux-exec.sh`)

This is the primary tool for all interaction. It handles both shell commands and interactive REPLs.

### Shell Mode (Default)
Executes a command, waits for it to finish, and returns clean output and the exit code.
```bash
# Usage: ./scripts/tmux-exec.sh <target> <command>
# Returns: The command's output. Exit code matches the command.
./scripts/tmux-exec.sh "my-session:0.0" "ls -la"
```

### Interactive Mode (`-w pattern`)
Sends keys and waits for a specific regex pattern to appear (e.g., a prompt).
```bash
# Usage: ./scripts/tmux-exec.sh -w <regex> <target> <command>
# Returns: Nothing (success/fail via exit code).
./scripts/tmux-exec.sh -w "^>>> " "python-session" "print('hello')"
```

## 2. Read and Scrape (`scripts/tmux-read.sh`)

Use this to see what is happening in a pane without sending any input.

```bash
# Usage: ./scripts/tmux-read.sh <target>
./scripts/tmux-read.sh "my-session:0.0"
```

It uses intelligent prompt detection to return only the output of the *last* command, or the most recent block of text.

## 3. List Environment (`scripts/tmux-list.sh`)

Returns a JSON array of all sessions, windows, and panes to help you understand the context.

## Rules
1.  **Be Explicit**: Always use the target (session:window.pane) provided by the user.
2.  **Verify First**: Use `tmux-list.sh` to confirm targets exist before acting.
3.  **No Magic**: Do not create or destroy sessions unless explicitly instructed.
