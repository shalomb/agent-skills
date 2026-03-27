---
name: pi-sub-agent
description: Launch a pi coding agent as a sub-process in a tmux pane, monitor its progress via JSONL streaming, and report results. Use when you need to delegate a well-defined task (bug fix, feature, refactor) to a separate agent instance with live observability. Triggers include "launch agent", "delegate to sub-agent", "run this in another agent", "Ralph loop", "TDD in a sub-agent", or any request to run pi in a tmux pane and monitor it.
---

# Pi Sub-Agent Skill

Launch pi coding agents in tmux panes with live monitoring. Depends on the `tmux` skill for pane interaction.

## When to use

- Delegating a well-scoped task (bug fix, feature build, refactor) to a fresh agent
- Running a TALAR or Ralph Wiggum loop where each iteration is a separate agent
- Parallel execution of independent tasks in different panes
- Any situation where you want to observe an agent working without blocking your session

## Workflow

### 1. Write the task prompt to a file

Always use a file — never inline long prompts in shell commands (quoting breaks).

```bash
cat > /tmp/task-prompt.md << 'EOF'
Your task description here.
Read TODO.md items X, Y for context.
...
EOF
```

### 2. Identify a free tmux pane

Use the tmux skill to find a pane:
```bash
bash ~/.pi/agent/skills/tmux/scripts/tmux-list.sh
```

Pick a pane in your current session with `cmd=bash` that isn't running anything.

### 3. Launch pi in the pane

```bash
tmux send-keys -t "{session}:{window}.{pane}" \
  'cd /path/to/repo && pi --models "github-copilot/claude-sonnet-4.6" --no-session --mode json -p @/tmp/task-prompt.md > /tmp/task-output.jsonl 2>&1 &' Enter
```

Key flags:
- `--no-session` — ephemeral, no persistent state (stateless per Ralph Wiggum pattern)
- `--mode json` — JSONL streaming output for monitoring
- `-p @file` — non-interactive, process prompt and exit
- `> file.jsonl 2>&1 &` — background with captured output

### 4. Launch the monitor

```bash
tmux send-keys -t "{session}:{window}.{pane}" \
  "python3 {skill_dir}/scripts/pi-monitor.py /tmp/task-output.jsonl" Enter
```

The monitor shows: tool calls, files edited, commits, test results, errors, and completion status. Refreshes every 2 seconds.

### 5. Poll for completion

```bash
for i in $(seq 1 40); do
  sleep 30
  status=$(bash ~/.pi/agent/skills/tmux/scripts/tmux-read.sh "{session}:{window}.{pane}" 2>&1)
  done=$(echo "$status" | grep -c "✅ DONE")
  tools=$(echo "$status" | grep "Tool calls:" | grep -oP '\d+' | tail -1)
  echo "[$(date +%H:%M:%S)] tools=$tools"
  if [ "$done" -gt 0 ]; then
    echo "=== AGENT FINISHED ==="
    echo "$status"
    break
  fi
done
```

### 6. Verify results

After the agent finishes:
```bash
# Kill monitor
tmux send-keys -t "{session}:{window}.{pane}" C-c

# Check commits
git log --oneline -5

# Run tests
just test  # or pytest, etc.
```

## Common patterns

### TALAR iteration (Test → Analyze → Learn → Adjust → Retest)

Each iteration is a separate pi launch:

```
Iteration 1: Write prompt → Launch pi → Monitor → Verify → Analyze gaps
Iteration 2: Write refined prompt → Launch pi → Monitor → Verify → Analyze
...
```

The prompt file changes each iteration based on what the previous one revealed.

### Ralph Wiggum (stateless TDD)

Use `--no-session` so each invocation starts fresh. The prompt specifies
red-green-refactor for each bug/feature. The agent commits atomically.

### Parallel workers

Launch in different panes with different prompt files:
```bash
# Pane 0.0: bug fixes
tmux send-keys -t "session:0.0" 'pi ... -p @/tmp/bugfix-prompt.md > /tmp/bugfix.jsonl 2>&1 &' Enter

# Pane 2.1: feature work
tmux send-keys -t "session:2.1" 'pi ... -p @/tmp/feature-prompt.md > /tmp/feature.jsonl 2>&1 &' Enter
```

Monitor each with a separate `pi-monitor.py` instance.

## Troubleshooting

**Prompt gets mangled by shell quoting**: Always use `@/tmp/file.md` — never inline.

**Agent runs forever**: Check if it's stuck in a retry loop. Read the JSONL:
```bash
tail -5 /tmp/task-output.jsonl | python3 -c "import json,sys; [print(json.loads(l).get('type','?')) for l in sys.stdin]"
```

**Monitor shows "RUNNING" but file stopped growing**: The agent may have errored silently. Check:
```bash
stat -c%s /tmp/task-output.jsonl  # note size
sleep 10
stat -c%s /tmp/task-output.jsonl  # compare
```

**Wrong pane**: Always use `tmux-list.sh` first. Use your own session, not a random one.
