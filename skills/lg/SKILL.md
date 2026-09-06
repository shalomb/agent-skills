---
name: lg
description: Quick alias for /lazygit to launch lazygit in a blocking tmux popup. Short command alias for lazygit.
---

# Lazygit Shortcut (/lg)

<!-- generated:alias-skill -->
When invoked, load and execute the **`lazygit`** skill:
1. Follow all instructions and guidelines in [`lazygit`](../lazygit/SKILL.md).
2. FAST PATH: Immediately execute the command on the first turn: `uv run {SKILLS_DIR}/lazygit/scripts/lazygit_popup.py [args]`.
3. If tmux is active, this automatically opens an interactive lazygit popup and blocks until the user exits lazygit.
4. IMPORTANT: If Antigravity sends this command to the background while the user is inside lazygit, DO NOT poll or monitor it (no manage_task, no ps aux, no reading task logs). Simply inform the user the popup is open and STOP calling tools. The system will automatically wake you when the user finishes reviewing.
5. Support forwarding panel subcommands (status, branch, log, stash) or flags (e.g. -f <path>) to lazygit.
6. On exit, summarize any working tree changes made during the review session.
