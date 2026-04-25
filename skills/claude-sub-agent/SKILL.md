---
name: claude-sub-agent
description: Launch Claude Code CLI as a headless sub-agent in a tmux pane, monitor its stream-json JSONL output, and poll for completion. Use when delegating a well-defined coding task (bug fix, feature, refactor) to a Claude agent subprocess with live observability. Triggers include "run claude agent", "delegate to claude", "claude sub-agent", or any request to run claude headlessly and monitor it.
---

# Claude Sub-Agent Skill

Launch `claude` as a headless sub-agent in a tmux pane with live JSONL monitoring. Depends on the `tmux` skill for pane interaction.

## When to use

- Delegating a scoped task to Claude CLI running autonomously
- Parallel execution alongside other sub-agents (gemini-sub-agent, pi-sub-agent)
- Running Ralph or Bart loops where each iteration is a separate claude process
- Tasks where cost tracking (`total_cost_usd`) per agent run matters

## Output format

Claude CLI streams **newline-delimited JSON** via `--output-format stream-json`. Key event types:

| Type | Meaning |
|------|---------|
| `system` / `subtype: init` | Startup: `session_id`, `model`, tools list |
| `assistant` | Model turn: `message.content` array with `tool_use` and `text` blocks |
| `user` | Tool result: `tool_use_result.content[].text` |
| `result` | **Completion signal**: `subtype`, `is_error`, `total_cost_usd`, `duration_ms`, `num_turns` |

Tool calls live inside `assistant.message.content[]` as `{"type":"tool_use","name":"Bash","input":{"command":"..."}}`.

Completion signal:
```json
{"type":"result","subtype":"success","is_error":false,"total_cost_usd":0.039,"duration_ms":11300,"num_turns":2,"result":"..."}
```

## Non-interactive invocation

### Lean / headless flags

```bash
claude \
  --print \
  --output-format stream-json \
  --dangerously-skip-permissions \
  --no-session-persistence \
  -p @/tmp/task-prompt.md \
  > /tmp/claude-output.jsonl 2>&1
```

| Flag | Why |
|------|-----|
| `--print` | Non-interactive: process prompt and exit |
| `--output-format stream-json` | JSONL stream for monitoring; completion signalled by `"type":"result"` |
| `--dangerously-skip-permissions` | Auto-approve all tool calls — required for headless use in trusted sandboxes |
| `--no-session-persistence` | Ephemeral — no session written to disk, no prior context loaded |
| `-p @file` | Load prompt from file (avoids shell quoting issues) |

Additional useful flags:
- `--model sonnet` / `--model opus` / `--model haiku` — model selection
- `--system-prompt @file` — replace system prompt (e.g. for persona injection)
- `--append-system-prompt @file` — append persona on top of default prompt
- `--max-budget-usd 1.00` — hard spending cap for the run
- `--tools "Bash,Edit,Read,Write"` — restrict available tools
- `--bare` — minimal mode: skip hooks, LSP, CLAUDE.md discovery, plugins (fastest cold start)

### Bare mode (fastest, for simple tasks)

```bash
claude --print --output-format stream-json \
  --dangerously-skip-permissions \
  --no-session-persistence \
  --bare \
  -p @/tmp/task-prompt.md \
  > /tmp/claude-output.jsonl 2>&1
```

`--bare` skips CLAUDE.md auto-discovery, extensions, MCP, plugins, and keychain reads. Use when the worktree has no CLAUDE.md persona you need loaded.

## Workflow

### 1. Write the task prompt to a file

```bash
cat > /tmp/task-prompt.md << 'EOF'
Your task description here.
EOF
```

### 2. Identify a free tmux pane

```bash
bash ~/.pi/agent/skills/tmux/scripts/tmux-list.sh
```

### 3. Launch claude + monitor in the pane

```bash
TARGET="{session}:{window}.{pane}"

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && claude --print --output-format stream-json --dangerously-skip-permissions --no-session-persistence -p @/tmp/task-prompt.md > /tmp/claude-output.jsonl 2>&1 &" Enter
sleep 5
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py /tmp/claude-output.jsonl" Enter
```

### 4. Poll for completion

```bash
python3 ~/.pi/agent/skills/claude-sub-agent/scripts/poll.py "$TARGET" --interval 30
```

### 5. Verify results

```bash
tmux send-keys -t "$TARGET" C-c   # kill monitor
git log --oneline -5
uv run pytest tests/ -x -q        # or project test command
```

## Full copy-paste pattern

```bash
cat > /tmp/task-prompt.md << 'EOF'
Your task here.
EOF

TARGET="{session}:{window}.{pane}"

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && claude --print --output-format stream-json --dangerously-skip-permissions --no-session-persistence -p @/tmp/task-prompt.md > /tmp/claude-output.jsonl 2>&1 &" Enter
sleep 5
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py /tmp/claude-output.jsonl" Enter

python3 ~/.pi/agent/skills/claude-sub-agent/scripts/poll.py "$TARGET" --interval 30

tmux send-keys -t "$TARGET" C-c
git log --oneline -5
```

## Agent / persona injection

```bash
# Append a persona on top of claude's default system prompt
claude --print --output-format stream-json \
  --dangerously-skip-permissions --no-session-persistence \
  --append-system-prompt @.pi/agents/bart.md \
  -p @/tmp/task.md \
  > /tmp/claude-output.jsonl 2>&1 &
```

In tmux:
```bash
tmux send-keys -t "$TARGET" \
  "cd /repo && claude --print --output-format stream-json --dangerously-skip-permissions --no-session-persistence --append-system-prompt @.pi/agents/bart.md -p @/tmp/task.md > /tmp/claude-output.jsonl 2>&1 &" Enter
```

Unlike Gemini (which uses `GEMINI.md`), Claude supports `--system-prompt` and `--append-system-prompt` flags directly — no CWD file needed.

## Model selection

```bash
claude --model haiku   # fastest, cheapest (claude-haiku-4-5)
claude --model sonnet  # balanced (claude-sonnet-4-6) — default
claude --model opus    # most capable (claude-opus-4-5)
```

## Cost control

```bash
# Hard cap — agent stops if budget exceeded
claude --print --output-format stream-json \
  --dangerously-skip-permissions \
  --max-budget-usd 0.50 \
  -p @/tmp/task.md \
  > /tmp/claude-output.jsonl 2>&1
```

Final cost is in the `result` line:
```bash
grep '"type":"result"' /tmp/claude-output.jsonl | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print(f'Cost: \${d[\"total_cost_usd\"]:.4f}  Duration: {d[\"duration_ms\"]/1000:.1f}s  Turns: {d[\"num_turns\"]}')
"
```

## Troubleshooting

**Prompt mangled by shell quoting**: Always use `-p @/tmp/file.md` — never inline long prompts.

**Permission prompts blocking headless run**: Ensure `--dangerously-skip-permissions` is set. Without it, claude pauses for approval.

**`--bare` missing CLAUDE.md context**: If your repo's `CLAUDE.md` has important guardrails, omit `--bare` or use `--append-system-prompt @CLAUDE.md` explicitly.

**Agent runs forever**: Check if stuck in a retry loop:
```bash
tail -3 /tmp/claude-output.jsonl | python3 -c "import json,sys; [print(json.loads(l).get('type','?')) for l in sys.stdin]"
```

**Parse the result stats**:
```bash
python3 -c "
import json
for line in open('/tmp/claude-output.jsonl'):
    d = json.loads(line)
    if d.get('type') == 'result':
        print('Status:', d['subtype'], '| Error:', d['is_error'])
        print('Cost: \$' + str(d['total_cost_usd']))
        print('Duration:', d['duration_ms'] / 1000, 's')
        print('Turns:', d['num_turns'])
"
```
