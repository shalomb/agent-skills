---
name: lazygit
description: Launch lazygit terminal UI in a blocking tmux popup to review, stage, commit, and manage git changes in the current agent repository and branch. Use when asked to review git diffs, inspect git history, or manage git status interactively.
---

# Lazygit Tmux Reviewer (/lazygit, /lg)

Launch the `lazygit` terminal UI inside a floating, blocking `tmux` popup overlay directly in the agent's current repository and branch.

## Fast Path Instructions for AI Agents

1. **Immediate Execution**: Immediately execute the command on the first turn:
   ```bash
   uv run {SKILLS_DIR}/lazygit/scripts/lazygit_popup.py [args]
   ```
2. **Blocking Popup Protocol**:
   - The command invokes `tmux display-popup -E -d <repo_root> -w 90% -h 90% -T " Lazygit: <repo> (<branch>) " lazygit`.
   - If Antigravity or your agent runtime sends this command to the background while the user is inside lazygit:
     - **DO NOT poll or monitor the process** (no `manage_task`, no `ps aux`, no periodic status checks).
     - Inform the user that the lazygit popup is open in their terminal.
     - **STOP calling tools and end your turn.**
     - The runtime will automatically resume your execution when the user exits lazygit (via `q` or `Esc`).
3. **Arguments & Subcommands**:
   - To open directly into a panel, forward the panel name: `status`, `branch`, `log`, `stash`.
   - To filter by file: `-f <path>`.
4. **Post-Review Status**:
   - On popup exit, the script outputs a summary of any working tree changes made during the review session.

## Quick CLI Reference

```bash
# Open lazygit popup for current repo and branch
lazygit-popup

# Shortcut alias via slash commands
/lazygit
/lg

# Open directly into commit log panel
/lg log

# Open filtered to specific path
/lg -f path/to/file
```

## Detailed References

- [Tmux Popup Guide & Keybindings](references/tmux-popup-guide.md)
