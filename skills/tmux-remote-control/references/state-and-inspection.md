> Scripts: `$SKILL_SCRIPTS` = `$(dirname <path-to-SKILL.md>)/scripts`. See `SKILL.md`.

# Clear Stuck State (`scripts/tmux-clear-state.sh`)

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

# Read (`scripts/tmux-read.sh`)

Read-only scrape of the last command's output.  Warns if the pane is busy.

```bash
$SKILL_SCRIPTS/tmux-read.sh "1.0"
```

| Flag | Default | Meaning |
|------|---------|---------|
| `-n LINES` | 2000 | History depth. |
| `-S PATH` | — | Custom tmux socket. |

# List (`scripts/tmux-list.sh`)

JSON inventory of all panes.  Current session is listed first and marked.
Shows `"busy": true/false` per pane with command and elapsed time.

```bash
$SKILL_SCRIPTS/tmux-list.sh
```

Use this to find idle panes before executing commands.
