# Creating Windows and Panes

**Every window you create MUST be named** with a very terse label (`-n`).  Unnamed windows show up as bare numbers (`3:bash`), and the user then has to hunt through them to find the one an agent opened.

```bash
# Detached (don't steal focus), named, and print the target to use with tmux-exec.sh
tmux new-window -d -n tf-plan -P -F '#{window_index}.#{pane_index}'
```

- **Name**: 1-2 words, lowercase, hyphenated, at most ~10 chars, describing the *purpose*, not the tool — `tf-plan`, `gdb`, `api-logs`, `repl`, `tests`.  Not `window`, `new`, `agent`, `bash`, or a number.
- **Detached** (`-d`) so the user's focus stays where it is.
- **Capture the target** with `-P -F` and use it for later `tmux-exec.sh` / `tmux-read.sh` calls.
- Reuse an existing window of the same name (check `tmux-list.sh`) rather than opening a duplicate.
- If the name reverts, tmux's auto-rename is overriding it: `tmux set-option -w -t <target> automatic-rename off`.
- If you split an existing window instead, never rename the user's windows; only name ones you created.
- Close windows you created when done (`tmux kill-window -t <target>`), unless the user wants them kept.
