---
name: gemini-sub-agent
description: Launch Gemini CLI as a headless sub-agent in a tmux pane, monitor its stream-json JSONL output, and poll for completion. Use when delegating a well-defined task to a Gemini agent subprocess with live observability. Triggers include "run gemini agent", "delegate to gemini", "gemini sub-agent", or any request to run gemini headlessly and monitor it.
---

# Gemini Sub-Agent Skill

Launch `gemini` as a headless sub-agent in a tmux pane with live JSONL monitoring. Depends on the `tmux` skill for pane interaction.

## When to use

- Delegating a scoped task to Gemini CLI running autonomously
- Parallel execution alongside other sub-agents (copilot-sub-agent, claude-sub-agent, pi-sub-agent)
- Tasks where Gemini's explicit exit codes (41–53) are useful for error handling in scripts

## Output format

Gemini streams **newline-delimited JSON** via `--output-format stream-json`. Key event types:
- `init` — startup, contains `session_id`, `model`
- `message` with `role: user` — echoes the prompt
- `message` with `role: assistant`, `delta: true` — streaming text chunks
- `result` — **final line**, contains `status`, `stats` (tokens, duration_ms, tool_calls)

Completion signal: `"type":"result"` line in the stream.

```json
{"type":"result","status":"success","stats":{"total_tokens":11386,"input_tokens":10774,"output_tokens":71,"cached":6250,"duration_ms":5815,"tool_calls":0}}
```

Exit codes (unique to Gemini — use these in scripts):
- `0` — success
- `41` — authentication error
- `42` — invalid input
- `44` — sandbox error
- `52` — configuration error
- `53` — turn limit exceeded

## Non-interactive invocation

### Lean / headless invocation

```bash
cat /tmp/task-prompt.md | gemini \
  --yolo \
  --output-format stream-json \
  --model flash \
  > /tmp/gemini-output.jsonl 2>&1
```

**What each flag does:**

| Flag | Why |
|---|---|
| `--yolo` | Auto-approve all tool calls — required for headless |
| `--output-format stream-json` | JSONL stream for monitoring; completion signalled by `"type":"result"` line |
| `--model flash` | Use flash (fast) instead of auto or pro — significantly faster for agentic tasks |

Gemini's startup footprint is controlled by what's in `~/.gemini/settings.json` and `GEMINI.md`. There is no flag to suppress MCP loading — configure `allowed-mcp-server-names` with an empty list if you need to exclude all MCP servers:

```bash
cat /tmp/task-prompt.md | gemini \
  --yolo \
  --output-format stream-json \
  --model flash \
  --allowed-mcp-server-names "" \
  > /tmp/gemini-output.jsonl 2>&1
```

Gemini's baseline system prompt is ~10–11k tokens and is cached by default on warm runs. There are no flags to reduce this further — the lean knob is **model selection** (`flash` vs `pro`) and **avoiding GEMINI.md bloat** when injecting personas.

Other useful flags:
- `--model flash-lite` — fastest/cheapest option
- `--temperature 0` — deterministic output for automation
- `--timeout <ms>` — execution timeout in milliseconds
- `--include-directories /path` — add workspace directories

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

### 3. Launch gemini + monitor in the pane

```bash
TARGET="{session}:{window}.{pane}"

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && cat /tmp/task-prompt.md | gemini --yolo --output-format stream-json > /tmp/gemini-output.jsonl 2>&1 &" Enter
sleep 3
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/gemini-sub-agent/scripts/monitor.py /tmp/gemini-output.jsonl" Enter
```

### 4. Poll for completion

```bash
python3 ~/.pi/agent/skills/gemini-sub-agent/scripts/poll.py "$TARGET" --interval 30
```

### 5. Check exit code and verify

```bash
tmux send-keys -t "$TARGET" C-c   # kill monitor

# Extract exit code from result line
python3 -c "
import json
for line in open('/tmp/gemini-output.jsonl'):
    d = json.loads(line.strip())
    if d.get('type') == 'result':
        print('Status:', d['status'])
        print('Stats:', json.dumps(d['stats'], indent=2))
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
  "cd /path/to/repo && cat /tmp/task-prompt.md | gemini --yolo --output-format stream-json --model flash > /tmp/gemini-output.jsonl 2>&1 &" Enter
sleep 3
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/gemini-sub-agent/scripts/monitor.py /tmp/gemini-output.jsonl" Enter

python3 ~/.pi/agent/skills/gemini-sub-agent/scripts/poll.py "$TARGET" --interval 30

tmux send-keys -t "$TARGET" C-c
git log --oneline -5
```

## Agent / persona injection

Gemini has **no `--system-prompt` CLI flag**. Persona injection works via `GEMINI.md` in the **current working directory** — Gemini automatically loads it as system context before any prompt.

```bash
# Write the persona to GEMINI.md in the working directory
cat .pi/agents/bart.md > /path/to/repo/GEMINI.md

# Run gemini from that directory — it will load GEMINI.md automatically
cd /path/to/repo
cat /tmp/task.md | gemini --yolo --output-format stream-json > /tmp/gemini-output.jsonl 2>&1

# Clean up after (or leave if you want the persona persistent)
rm /path/to/repo/GEMINI.md
```

The `GEMINI.md` file is a plain markdown system prompt — no frontmatter required. Gemini loads it from `$CWD/GEMINI.md` (also checks `~/.gemini/GEMINI.md` as a user-level default).

For headless sub-agent use, write the persona before launching:

```bash
cat > /path/to/repo/GEMINI.md << 'EOF'
You are Bart Simpson, adversarial reviewer. Find bugs. Be snarky.
EOF

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && cat /tmp/task-prompt.md | gemini --yolo --output-format stream-json > /tmp/gemini-output.jsonl 2>&1 &" Enter
```

## Model selection

```bash
gemini "task" --model flash-lite --yolo   # fastest, cheapest
gemini "task" --model flash --yolo        # fast, balanced (default)
gemini "task" --model pro --yolo          # most capable
```

## Script integration (using exit codes)

```bash
cat /tmp/task-prompt.md | gemini --yolo --output-format stream-json > /tmp/out.jsonl 2>&1
case $? in
  0)  echo "Success" ;;
  41) echo "Auth error — check GEMINI_API_KEY" ; exit 1 ;;
  42) echo "Invalid input" ; exit 1 ;;
  52) echo "Config error" ; exit 1 ;;
  53) echo "Turn limit exceeded" ; exit 1 ;;
  *)  echo "Unknown error $?" ; exit 1 ;;
esac
```

## Troubleshooting

**Prompt truncated by shell**: Use `cat /tmp/file | gemini ...` (stdin pipe) for long prompts.

**Stuck with no `result` line**: Check if `--yolo` is set; without it, Gemini pauses for tool approval.

**`tool_calls: 0` but task needed tools**: Gemini may need `--approval-mode yolo` explicitly if `--yolo` alone doesn't propagate.

**Parse the result stats**:
```bash
grep '"type":"result"' /tmp/gemini-output.jsonl | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(json.dumps(d['stats'], indent=2))"
```
