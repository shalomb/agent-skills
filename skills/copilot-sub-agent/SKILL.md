---
name: copilot-sub-agent
description: Launch GitHub Copilot CLI as a headless sub-agent in a tmux pane, monitor its JSONL output stream, and poll for completion. Use when delegating a well-defined coding task (bug fix, feature, refactor) to a Copilot agent subprocess with live observability. Triggers include "run copilot agent", "delegate to copilot", "copilot sub-agent", or any request to run copilot headlessly and monitor it.
---

# Copilot Sub-Agent Skill

Launch `copilot` as a headless sub-agent in a tmux pane with live JSONL monitoring. Depends on the `tmux` skill for pane interaction.

## When to use

- Delegating a scoped task to GitHub Copilot CLI running autonomously
- Parallel execution alongside other sub-agents (gemini-sub-agent, claude-sub-agent, pi-sub-agent)
- Any situation where you want to observe a Copilot agent working without blocking your session

## Output format

Copilot streams **JSONL** (same schema as pi). Key event types:
- `session` — startup, contains `id`, `timestamp`
- `agent_start` / `agent_end` — lifecycle boundaries; `agent_end` = done
- `tool_execution_start` / `tool_execution_end` — tool calls with `toolName`, `args`, `result`
- `message_end` — assistant turn complete, contains final text

Completion signal: `"type":"agent_end"` line in the JSONL stream.

## Non-interactive invocation

### Lean / headless invocation

```bash
COPILOT_API_URL="https://api.business.githubcopilot.com" \
copilot \
  --yolo \
  --no-auto-update \
  --disable-builtin-mcps \
  --no-custom-instructions \
  --no-ask-user \
  -p @/tmp/task-prompt.md \
  > /tmp/copilot-output.jsonl 2>&1
```

**What each flag does:**

| Flag | Why |
|---|---|
| `COPILOT_API_URL` | **Critical for Business/Enterprise** — see startup hang section below |
| `--yolo` | Auto-approve all tool calls — required for headless |
| `--no-auto-update` | Skip update check on startup |
| `--disable-builtin-mcps` | Don't load `github-mcp-server` — removes GitHub MCP tools from context |
| `--no-custom-instructions` | Skip scanning `AGENTS.md` / `.github/copilot-instructions.md` |
| `--no-ask-user` | Remove the `ask_user` tool — prevents agent stalling waiting for input |
| `-p @file` | Non-interactive, read prompt from file and exit |

### ⚠️ The ~2-minute startup hang: root cause and fix

The CLI first tries `api.githubcopilot.com` (personal account endpoint). On **Copilot Business or Enterprise accounts** this endpoint drops TCP connections, causing a 10-second connect timeout retried with exponential backoff across 4 attempts before falling through to the correct endpoint:

```
Attempt 1: 10s timeout + 5s delay   = 15s
Attempt 2: 10s timeout + 10s delay  = 20s
Attempt 3: 10s timeout + 20s delay  = 30s
Attempt 4: 10s timeout + 40s delay  = 50s
Total:                              ~115s
```

**Fix** — force the correct endpoint via `COPILOT_API_URL`:

```bash
# Copilot Business or Enterprise:
export COPILOT_API_URL="https://api.business.githubcopilot.com"

# GHE.com data-residency accounts:
export COPILOT_API_URL="https://copilot-api.{tenant}.ghe.com"

# Personal/individual accounts (default, no env var needed)
```

With this set, startup drops from ~2 minutes to ~7 seconds. Add to your shell profile.

**Diagnose**: check `~/.config/.copilot/logs/process-*.log`:
```
ConnectTimeoutError: Connect Timeout Error (attempted address: api.githubcopilot.com:443)
Retrying request to GitHub API in 5 seconds. Attempt 1/5
```
If you see this, you need `COPILOT_API_URL`.

### Agent frontmatter format

Agent `.md` files in `~/.config/copilot/agents/` must use copilot's format — plain pi-style files will log `custom agent markdown frontmatter is malformed` and be silently ignored. See the Agent/persona section for the correct `.agent.md` format.

Other useful flags:
- `--model <model>` — override model (default: claude-sonnet-4.5)
- `--share /tmp/session.md` — export full session as markdown
- `--autopilot` — enable multi-step continuation
- `--max-autopilot-continues <n>` — cap autopilot iterations

For full flag reference, read `references/copilot-cli-reference.md`.

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

### 3. Launch copilot + monitor in the pane

```bash
TARGET="{session}:{window}.{pane}"

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && copilot --yolo -p @/tmp/task-prompt.md > /tmp/copilot-output.jsonl 2>&1 &" Enter
sleep 3
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/copilot-sub-agent/scripts/monitor.py /tmp/copilot-output.jsonl" Enter
```

### 4. Poll for completion

```bash
python3 ~/.pi/agent/skills/copilot-sub-agent/scripts/poll.py "$TARGET" --interval 30
```

### 5. Verify results

```bash
tmux send-keys -t "$TARGET" C-c   # kill monitor
git log --oneline -5
```

## Full copy-paste pattern

```bash
cat > /tmp/task-prompt.md << 'EOF'
Your task here.
EOF

TARGET="{session}:{window}.{pane}"

tmux send-keys -t "$TARGET" \
  "cd /path/to/repo && COPILOT_API_URL=https://api.business.githubcopilot.com copilot --yolo --no-auto-update --disable-builtin-mcps --no-custom-instructions --no-ask-user -p @/tmp/task-prompt.md > /tmp/copilot-output.jsonl 2>&1 &" Enter
sleep 3
tmux send-keys -t "$TARGET" \
  "python3 ~/.pi/agent/skills/copilot-sub-agent/scripts/monitor.py /tmp/copilot-output.jsonl" Enter

python3 ~/.pi/agent/skills/copilot-sub-agent/scripts/poll.py "$TARGET" --interval 30

tmux send-keys -t "$TARGET" C-c
git log --oneline -5
```

## Agent / persona injection

Copilot `--agent` looks up a `{stem}.agent.md` file by its **filename stem** (not its `name:` frontmatter field). Search order:

1. `.github/agents/{stem}.agent.md` — project-level (in repo root)
2. `~/.config/copilot/agents/{stem}.agent.md` — user-level

File format (frontmatter + markdown system prompt):

```markdown
---
name: Bart
description: Adversarial code reviewer
tools: ["read_file", "run_shell_command"]
model: ["claude-sonnet-4.6"]
---

You are Bart Simpson, adversarial reviewer. Find bugs and be snarky.
```

Use it:

```bash
# Install agent file to user config (persists across repos)
cp .pi/agents/bart.md ~/.config/copilot/agents/bart.agent.md

# Or install to project (checked in, team-shared)
cp .pi/agents/bart.md .github/agents/bart.agent.md

# Invoke by stem name
copilot --agent bart --yolo -p @/tmp/task.md
```

> **Note**: The `--agent` flag takes the **filename stem**, not the `name:` frontmatter value. A file named `bart.agent.md` → `--agent bart`.

## Model selection

```bash
copilot --model claude-haiku-4.5 --yolo -p @/tmp/task.md   # fast/cheap
copilot --model claude-sonnet-4.6 --yolo -p @/tmp/task.md  # default
copilot --model claude-opus-4.6 --yolo -p @/tmp/task.md    # most capable
```

## Troubleshooting

**Still slow after setting `COPILOT_API_URL`**: Check the log for other errors:
```bash
tail -20 ~/.config/.copilot/logs/$(ls -t ~/.config/.copilot/logs/ | head -1)
```

**`unknown option '--no-bash-env'`**: This flag is only valid in interactive mode, not with `-p`. Don't use it.

**Agent not found / `No such agent: bart`**: Check the filename stem matches what you pass to `--agent`. A file `bart.agent.md` → `--agent bart`. The `name:` frontmatter field is ignored for lookup.

**`custom agent markdown frontmatter is malformed`**: Pi-format agent files (no `tools:` array, wrong field names) are rejected. Use the `.agent.md` format with `name`, `description`, `tools` fields.

**Prompt gets mangled by shell quoting**: Always use `-p @/tmp/file.md` — never inline the prompt string.
