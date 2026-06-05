---
name: kiro-sub-agent
description: >
  Launch Kiro CLI as a headless sub-agent in a tmux pane and monitor its
  completion. Use when delegating a well-defined coding task to a Kiro agent
  subprocess. Triggers include "run kiro agent", "delegate to kiro",
  "kiro sub-agent", or any request to run kiro-cli headlessly.
---

# Kiro Sub-Agent Skill

Launch `kiro-cli chat` as a headless sub-agent in a tmux pane.

## When to use

- Delegating a scoped task to Kiro CLI running autonomously
- Parallel execution alongside other sub-agents (claude, gemini, pi)
- Running Ralph or Bart loops via Kiro instead of Claude CLI
- When you want to use Kiro's tool ecosystem (AWS, code intelligence, etc.)

## Key differences from Claude CLI

| Aspect | Claude CLI | Kiro CLI |
|--------|-----------|----------|
| Structured output | `--output-format stream-json` (JSONL) | None — ANSI terminal output only |
| Non-interactive | `--print` + `--no-session-persistence` | `--no-interactive` |
| Tool trust | `--dangerously-skip-permissions` | `-a` / `--trust-all-tools` |
| Prompt input | `-p @/path/to/file.md` or `-p "text"` | Positional argument `"text"` |
| Model selection | `--model haiku\|sonnet\|opus` | `--model <model>` |
| Completion signal | `{"type":"result"}` in JSONL | Process exit (exit code 0) |
| Cost tracking | `total_cost_usd` in result event | Not available in output |

## Non-interactive invocation

```bash
kiro-cli chat \
  --trust-all-tools \
  --no-interactive \
  --model <model> \
  "Your prompt here"
```

### Reading prompt from file

Kiro CLI doesn't support `@file` syntax. Use command substitution:

```bash
kiro-cli chat -a --no-interactive "$(cat /tmp/task-prompt.md)"
```

Or for very long prompts (argument length limits), use a heredoc wrapper:

```bash
cat > /tmp/launch-kiro.sh << 'SCRIPT'
#!/bin/bash
cd /path/to/worktree
kiro-cli chat -a --no-interactive "$(cat /tmp/ralph-task.md)" \
  > /tmp/kiro-task.log 2>&1
echo "EXIT_CODE: $?"
SCRIPT
chmod +x /tmp/launch-kiro.sh
```

## Monitoring

Since Kiro doesn't produce JSONL, monitoring is process-based:

### Check if still running
```bash
# From tmux pane scraping
tmux capture-pane -t "$PANE" -p | tail -5
```

### Check completion
```bash
# Look for the credits/time line that signals end of response
tmux capture-pane -t "$PANE" -p | grep -q "Credits:.*Time:" && echo "DONE"
```

### Log-based monitoring
```bash
# If output is redirected to a file
tail -f /tmp/kiro-task.log | grep --line-buffered "Credits:"
```

## Launch template (for dispatch.py)

```bash
#!/bin/bash
cd {worktree}
kiro-cli chat -a --no-interactive "$(cat {prompt})" \
  > {logfile} 2>&1
echo "KIRO_EXIT: $?" >> {logfile}
```

## Completion detection

Unlike Claude's JSONL `result` event, detect Kiro completion by:

1. **Process exit** — the `kiro-cli chat` process terminates
2. **Log marker** — look for `Credits:` and `Time:` in output
3. **Exit code file** — append `echo "KIRO_EXIT: $?"` after the command

## Limitations

- No structured output — cannot extract cost, turn count, or tool calls programmatically
- No session persistence control beyond `--no-interactive`
- Prompt size limited by shell argument length (`getconf ARG_MAX`, typically 2MB on Linux)
- ANSI escape codes in output require stripping for clean log analysis
- No `--append-system-prompt` equivalent — persona must be included in the prompt text

## Integration with agent-mux

In `dispatch.py`, Kiro uses a different launch template:

```python
AGENT_CONFIG = {
    "ralph": {
        "runner": "kiro",
        "model": None,  # uses default
        "logfile": "/tmp/kiro-ralph-{id}.log",
    },
}
```

The dispatch script writes the prompt to a file and launches via:
```bash
cd <worktree> && kiro-cli chat -a --no-interactive "$(cat <prompt>)" > <logfile> 2>&1
```
