> Scripts: `$SKILL_SCRIPTS` = `$(dirname <path-to-SKILL.md>)/scripts`. See `SKILL.md`.

# Interactive Tool Notes

### Python REPL
Always set `PYTHON_BASIC_REPL=1` — the fancy readline REPL breaks send-keys.
Launch with `-d` so the pane isn't left marked busy:
```bash
$SKILL_SCRIPTS/tmux-exec.sh -d -t 20 -w '>>> ' "1.0" 'PYTHON_BASIC_REPL=1 python3 -q'
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
