---
description: Launch lazygit terminal UI in a blocking tmux popup to review, stage, and inspect git changes in the current agent repository and branch
---

You are tasked with: Launch lazygit terminal UI in a blocking tmux popup to review, stage, and inspect git changes in the current agent repository and branch.

Follow the instructions in the `lazygit` skill:
1. FAST PATH: Immediately execute the command on the first turn: `uv run {SKILLS_DIR}/lazygit/scripts/lazygit_popup.py [args]`.
2. If tmux is active, this automatically opens an interactive lazygit popup and blocks until the user exits lazygit.
3. IMPORTANT: If Antigravity sends this command to the background while the user is inside lazygit, DO NOT poll or monitor it (no manage_task, no ps aux, no reading task logs). Simply inform the user the popup is open and STOP calling tools. The system will automatically wake you when the user finishes reviewing.
4. Support forwarding panel subcommands (status, branch, log, stash) or flags (e.g. -f <path>) to lazygit.
5. On exit, summarize any working tree changes made during the review session.

User request:
$ARGUMENTS
