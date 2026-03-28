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
  'cd /path/to/repo && pi --models "github-copilot/claude-sonnet-4.6" --no-session --mode json --no-extensions --no-skills --no-prompt-templates --no-themes -p @/tmp/task-prompt.md > /tmp/task-output.jsonl 2>&1 &' Enter
```

**Lean / headless flags:**

| Flag | Why |
|---|---|
| `--no-session` | Ephemeral — no session written to disk, no prior context loaded |
| `--mode json` | JSONL stream output for monitoring |
| `-p @file` | Non-interactive, process prompt and exit |
| `--no-extensions` | Skip extension discovery and loading — avoids scanning for installed extensions |
| `--no-skills` | Skip skill loading from disk — reduces startup scan |
| `--no-prompt-templates` | Skip prompt template loading |
| `--no-themes` | Skip theme loading |

All four `--no-*` flags combined eliminate disk-scanning startup overhead. Use `--offline` to additionally suppress network calls (e.g. extension update checks):

```bash
pi --no-session --mode json \
   --no-extensions --no-skills --no-prompt-templates --no-themes \
   --offline \
   -p @/tmp/task-prompt.md \
   > /tmp/task-output.jsonl 2>&1 &
```

Other useful flags:
- `--models "provider/model"` — select specific model
- `--tools read,bash,edit,write` — already the default; reduce further with e.g. `read,bash` for read-only tasks
- `--append-system-prompt @file` — inject persona (see Agent/persona section)

### 4. Launch the monitor in the same pane

The pi process runs backgrounded (`&`), so the pane is free for the monitor:

```bash
tmux send-keys -t "{session}:{window}.{pane}" \
  "python3 {skill_dir}/scripts/pi-monitor.py /tmp/task-output.jsonl" Enter
```

The monitor shows a live dashboard: tool calls, files edited, commits, test results, errors, and completion status. Refreshes every 2 seconds. Stops automatically when the agent finishes.

### 5. Poll for completion from your own session

Don't `sleep` with increasing intervals — use `pi-poll.py` which reads the monitor's tmux pane at a fixed interval and reports progress:

```bash
python3 {skill_dir}/scripts/pi-poll.py "{session}:{window}.{pane}" --interval 30
```

This prints one status line every 30 seconds and exits 0 when the agent finishes:
```
[22:13:00] tools=13  files=...
[22:13:30] tools=15  files=test_adversarial_inputs.py
[22:14:00] tools=20  files=bb-feasibility-check.py, generate-handoff-pa
[22:14:30] tools=25  files=bb-feasibility-check.py, check-repo-permissi
✅ Agent finished after 180s (6 polls)
```

Options:
- `--interval 30` — poll every 30 seconds (default)
- `--timeout 1200` — give up after 20 minutes (default)

### 6. Full launch-monitor-poll pattern (copy-paste ready)

```bash
# 1. Write prompt to file
cat > /tmp/task-prompt.md << 'EOF'
Your task description here.
EOF

# 2. Identify target pane (must be in YOUR session)
TARGET="{session}:{window}.{pane}"

# 3. Launch pi + monitor in the target pane
tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && pi --models 'github-copilot/claude-sonnet-4.6' --no-session --mode json --no-extensions --no-skills --no-prompt-templates --no-themes -p @/tmp/task-prompt.md > /tmp/task-output.jsonl 2>&1 &" Enter
sleep 5
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/pi-sub-agent/scripts/pi-monitor.py /tmp/task-output.jsonl" Enter

# 4. Poll from your session (blocks until done or timeout)
python3 ~/.pi/agent/skills/pi-sub-agent/scripts/pi-poll.py "$TARGET" --interval 30

# 5. Kill monitor and verify
tmux send-keys -t "$TARGET" C-c
git log --oneline -5
```

### 7. Verify results

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

## Agent / persona injection

Pi resolves `@file` syntax in `--append-system-prompt`, so you can load persona files directly:

```bash
# Append a persona on top of pi's default coding assistant prompt
pi --no-session --mode json \
   --append-system-prompt @.pi/agents/bart.md \
   -p @/tmp/task-prompt.md \
   > /tmp/pi-output.jsonl 2>&1

# Or replace the system prompt entirely
pi --no-session --mode json \
   --system-prompt @.pi/agents/bart.md \
   -p @/tmp/task-prompt.md \
   > /tmp/pi-output.jsonl 2>&1
```

The `@path` is resolved relative to cwd. Both absolute and relative paths work.

In tmux:
```bash
tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && pi --no-session --mode json --append-system-prompt @.pi/agents/bart.md -p @/tmp/task.md > /tmp/pi-output.jsonl 2>&1 &" Enter
```

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
