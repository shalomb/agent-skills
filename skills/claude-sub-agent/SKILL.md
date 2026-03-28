---
name: claude-sub-agent
description: Launch Claude Code CLI as a headless sub-agent in a tmux pane, monitor its stream-json JSONL output, and poll for completion. Use when delegating a well-defined coding task (bug fix, feature, refactor) to a Claude agent subprocess with live observability. Triggers include "run claude agent", "delegate to claude", "claude sub-agent", or any request to run claude headlessly and monitor it.
---

# Claude Sub-Agent Skill

Launch `claude` as a headless sub-agent in a tmux pane with live monitoring. Depends on the `tmux` skill for pane interaction.

## When to use

- Delegating a scoped task to Claude Code running autonomously
- Parallel execution alongside other sub-agents (copilot-sub-agent, gemini-sub-agent, pi-sub-agent)
- Tasks where per-turn cost tracking (`total_cost_usd`) or token budgeting (`--max-budget-usd`) matters

## Output format

Claude has **two output modes** for headless use:

### `--output-format json` (single object, after completion)
Returns one JSON blob when the agent finishes. Best for simple one-shot tasks.
```json
{
  "type": "result",
  "subtype": "success",
  "result": "...",
  "session_id": "uuid",
  "total_cost_usd": 0.029,
  "usage": {
    "input_tokens": 3,
    "cache_creation_input_tokens": 22749,
    "cache_read_input_tokens": 0,
    "output_tokens": 61
  },
  "duration_ms": 1687,
  "num_turns": 1
}
```

### `--output-format stream-json` (JSONL, streaming) ← use for monitoring
Streams events as they happen. Key event types:
- Assistant message chunks (`type: "assistant"`)
- Tool use events (`type: "tool_use"`, `type: "tool_result"`)
- Final result (`type: "result"`) — **completion signal**

Completion signal: `"type":"result"` line in the stream.

## Non-interactive invocation

### Lean / headless invocation

```bash
cat /tmp/task-prompt.md | claude \
  --print \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --no-session-persistence \
  --strict-mcp-config \
  --disable-slash-commands \
  --setting-sources "" \
  --max-turns 20 \
  > /tmp/claude-output.jsonl 2>&1
```

**What each flag does:**

| Flag | Why |
|---|---|
| `--print` / `-p` | Non-interactive, exit after response |
| `--dangerously-skip-permissions` | Bypass all permission prompts — required for headless (trusted env only) |
| `--output-format stream-json` | JSONL stream for monitoring; use `json` for simple one-shot tasks |
| `--no-session-persistence` | Don't write session to disk — ephemeral, no leftover state |
| `--strict-mcp-config` | Ignore all MCP servers except explicitly passed ones — don't inherit user's MCP config |
| `--disable-slash-commands` | Don't load skills from disk — reduces startup scan overhead |
| `--setting-sources ""` | Don't load user/project/local settings files — clean slate, ~20% fewer cached tokens |
| `--max-turns <n>` | Safety cap on agentic turns; prevents runaway loops |

The `--setting-sources ""` flag is particularly effective: it reduces context from ~22k cached tokens to ~18k by not loading user settings that inject extra system prompt content.

Other useful flags:
- `--model sonnet` / `opus` / `haiku` — model selection
- `--max-budget-usd <amount>` — spend cap per run
- `--allowedTools "Bash,Edit,Read,Write"` — restrict to minimal tool set if task is scoped
- `--system-prompt "$(cat file)"` — persona injection (see Agent/persona section)

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
  "cd /path/to/repo && cat /tmp/task-prompt.md | claude -p --output-format stream-json --dangerously-skip-permissions > /tmp/claude-output.jsonl 2>&1 &" Enter
sleep 3
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py /tmp/claude-output.jsonl" Enter
```

### 4. Poll for completion

```bash
python3 ~/.pi/agent/skills/claude-sub-agent/scripts/poll.py "$TARGET" --interval 30
```

### 5. Check result and cost

```bash
tmux send-keys -t "$TARGET" C-c   # kill monitor

# Extract result + cost
python3 -c "
import json
for line in open('/tmp/claude-output.jsonl'):
    line = line.strip()
    if not line: continue
    d = json.loads(line)
    if d.get('type') == 'result':
        print('Status:', d.get('subtype'))
        print('Cost USD:', d.get('total_cost_usd'))
        print('Turns:', d.get('num_turns'))
        print('Tokens in/out:', d.get('usage', {}).get('input_tokens'), '/', d.get('usage', {}).get('output_tokens'))
"
git log --oneline -5
```

## Full copy-paste pattern

```bash
cat > /tmp/task-prompt.md << 'EOF'
Your task here.
EOF

TARGET="{session}:{window}.{pane}"

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && cat /tmp/task-prompt.md | claude -p --output-format stream-json --dangerously-skip-permissions --no-session-persistence --strict-mcp-config --disable-slash-commands --setting-sources '' --max-turns 20 > /tmp/claude-output.jsonl 2>&1 &" Enter
sleep 3
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py /tmp/claude-output.jsonl" Enter

python3 ~/.pi/agent/skills/claude-sub-agent/scripts/poll.py "$TARGET" --interval 30

tmux send-keys -t "$TARGET" C-c
git log --oneline -5
```

## Agent / persona injection

Claude has two mechanisms — inline JSON agents and direct system prompt override:

### Option A: `--agents` + `--agent` (inline, ephemeral)

```bash
# Define agents inline as JSON, then select one with --agent
claude \
  --agents '{"bart":{"description":"Adversarial reviewer","prompt":"You are Bart. Find bugs."}}' \
  --agent bart \
  -p "$(cat /tmp/task.md)" --dangerously-skip-permissions
```

This is stateless — the agent definition exists only for that invocation.

### Option B: `--system-prompt "$(cat file)"` (file-based)

```bash
# Load a .md persona file as the full system prompt
claude \
  --system-prompt "$(cat .pi/agents/bart.md)" \
  -p "$(cat /tmp/task.md)" --dangerously-skip-permissions
```

Use `--system-prompt` to fully replace the default prompt, or `--append-system-prompt` to add to it.

```bash
# Append persona on top of the default coding assistant prompt
claude \
  --append-system-prompt "$(cat .pi/agents/bart.md)" \
  -p "review this code" --dangerously-skip-permissions
```

> **Note**: Unlike pi, claude does NOT resolve `@file` syntax in `--system-prompt`. Use `$(cat file)` instead.

## Model selection

```bash
claude -p "task" --model haiku --dangerously-skip-permissions   # fast/cheap
claude -p "task" --model sonnet --dangerously-skip-permissions  # default
claude -p "task" --model opus --dangerously-skip-permissions    # most capable
```

## Tool scoping

```bash
# Read-only (safe analysis tasks)
claude -p "task" --allowedTools "Read,Bash(git:*)" --dangerously-skip-permissions

# Code editing only (no shell)
claude -p "task" --allowedTools "Read,Edit,Write" --dangerously-skip-permissions

# Full access
claude -p "task" --dangerously-skip-permissions
```

## Budget and turn caps

```bash
# Cap spend
claude -p "task" --max-budget-usd 0.10 --dangerously-skip-permissions

# Cap turns (prevents runaway loops)
claude -p "task" --max-turns 10 --dangerously-skip-permissions
```

## Session resumption

```bash
# Continue the most recent session
claude -c -p "follow up question" --dangerously-skip-permissions

# Resume specific session
claude -r "session-uuid" -p "continue from here" --dangerously-skip-permissions
```

## Troubleshooting

**Permission prompts block headless run**: Ensure `--dangerously-skip-permissions` is set. Only use in sandboxed/trusted environments.

**Output is empty**: Check if the process exited with an error — inspect stderr:
```bash
grep -v '^{' /tmp/claude-output.jsonl | head -20
```

**Stuck with no `result` line**: Check turn count; `--max-turns` may have silently capped it.

**Parse cost from single-JSON mode**:
```bash
claude -p "task" --output-format json --dangerously-skip-permissions | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['total_cost_usd'])"
```
