# Lazygit Tmux Popup Guide

This guide details how lazygit integrates with tmux popups for seamless in-session git reviews.

## Architecture

When invoked via `/lazygit` or `/lg`, the launcher:
1. Detects the current git repository root and checked-out branch.
2. Formats a popup title displaying `Lazygit: <repo_name> (<branch>)`.
3. Calls `tmux display-popup`:
   - `-E`: Closes the popup immediately when lazygit exits (`q` or `Esc`).
   - `-d <repo_dir>`: Binds the working directory directly to the agent's active repository.
   - `-w 90% -h 90%`: Opens a large, focused modal overlay without disrupting current panes.
   - `-T <title>`: Displays a border header with repository and branch context.

## Common Keybindings in Lazygit

| Key | Action |
|---|---|
| `1`, `2`, `3`, `4`, `5` | Switch panels (Status, Files, Branches, Commits, Stash) |
| `[`, `]` | Navigate tabs within active panel |
| `Space` | Stage / unstage file or hunk |
| `Enter` | Focus diff / drill down into file or commit |
| `c` | Commit staged changes (opens commit message prompt) |
| `A` | Amend previous commit |
| `d` | Discard changes in selected file / hunk |
| `z` | Undo last operation |
| `P` / `p` | Push / Pull |
| `b` | Checkout branch |
| `q` | Quit lazygit and close popup |

## Subcommand Panel Targeting

You can launch directly into specific panels:

```bash
# Open directly focused on commit history
/lazygit log

# Open directly focused on branches
/lazygit branch

# Open directly focused on files / working tree status
/lazygit status

# Open filtered to changes in a specific file or directory
/lazygit -f src/todo_navigator/cli.py
```

## Non-Tmux & Headless Fallback

- **Interactive Terminal:** When run in a normal terminal window outside tmux, lazygit opens directly in the foreground.
- **Headless / Agent Subprocess:** When no interactive TTY or tmux session exists, a warning is printed directing the user to start tmux or review using standard `git diff` / `git status`.
