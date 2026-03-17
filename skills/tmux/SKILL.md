---
name: tmux
description: Execute commands and read output from specific tmux panes. Use this to orchestrate shell commands or monitor interactive tools (Python, GDB) in a user-provided tmux environment.
---

# Tmux Skill

Simple, reliable tmux orchestration. Use this skill to interact with a specific tmux pane provided by the user.

## Pane Targeting Format

**Target Format**: `{session}:{window}.{pane}` or `{window}.{pane}` (current session implied)

**Components**:
- `{session}`: Session name (e.g., "code", "gmsgq-dad-clouddevsecops-iac-reveng-solution")
  - **Omit for current session shorthand** (e.g., just use `1.0` instead of `session:1.0`)
- `{window}`: Window index (0-based numbering, e.g., 0, 1, 2)
- `{pane}`: Pane index within that window (0-based, e.g., 0, 1, 2)

**Examples**:
- `1.0` = Window 1, Pane 0 in **current session** (shorthand)
- `code:0.0` = Window 0, Pane 0 in session "code" (explicit)
- `gmsgq-dad-clouddevsecops-iac-reveng-solution:4.0` = Window 4, Pane 0 in that session

**Shorthand Clarification**: When a user says "Use tmux pane 1.0", this means:
- Window index: 1
- Pane index: 0 (first/leftmost pane in that window)
- Session: Current/default (automatically resolved)

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

## Error Handling and Debugging

When tmux commands produce unexpected output or fail silently:

1. Use `tmux-read.sh` to inspect what's currently in the pane
2. Test with simple commands first (`echo "test"`)
3. Check pane state with `tmux-list.sh`
4. For complex debugging, read `references/error-handling-and-debugging.md`

Common issues and their solutions are documented in the error handling guide, including:
- Silent failures and no output
- Incomplete or truncated output
- Command not found errors
- Authentication failures in panes
- Timeout handling

## Rules
1.  **Be Explicit**: Always use the target (session:window.pane) provided by the user.
2.  **Verify First**: Use `tmux-list.sh` to confirm targets exist before acting.
3.  **No Magic**: Do not create or destroy sessions unless explicitly instructed.
4.  **Debug Systematically**: Follow the debugging workflow in error-handling-and-debugging.md when commands fail.
