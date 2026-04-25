---
name: agent-mux
description: >
  Use this skill to orchestrate multiple parallel sub-agents (Ralph/Bart) across
  isolated git worktrees to burn down a TODO.md backlog. Trigger this when asked to
  implement multiple independent features simultaneously, dispatch a "wave of agents",
  or perform "multi-agent orchestration". This handles complex dependency analysis,
  model spread, and feedback accumulation, which standard dispatch skills cannot.
---

# agent-mux — Multi-Agent Orchestrator

Compose `ralph`, `bart`, `gemini-sub-agent`, `pi-sub-agent`, and
`dispatching-parallel-agents` skills into a wave-based build+review pipeline
across git worktrees.

**Read these skills first — agent-mux builds on them, not instead of them:**
- `ralph` — TDD build loop
- `bart` — adversarial review loop
- `claude-sub-agent` — launching + monitoring Claude CLI agents
- `gemini-sub-agent` — launching + monitoring gemini agents
- `pi-sub-agent` — launching + monitoring pi agents
- `dispatching-parallel-agents` — independent task dispatch principles

## What agent-mux adds

The unique value not covered by the above skills:

1. **Dependency analysis** — which TODO items touch shared files and must be sequenced
2. **Wave ordering** — groups of independent items dispatched in parallel waves
3. **Model spread** — which model for which task character
4. **Ralph→Bart rejection loop** — feedback corral into planning branch `FEEDBACK.md`
5. **Hard-won pitfalls** — specific failure modes discovered in practice

---

## Orchestrator role and boundaries

The orchestrator's job is **routing, not implementing**.

| Orchestrator DOES | Orchestrator does NOT do |
|---|---|
| Run `dispatch.py` commands | Write code or tests |
| Read agent verdicts | Fix failing tests directly |
| Apply state transitions | Commit or push code |
| Triage Bart rejections into TODO entries | Rebase branches manually |
| Decide wave ordering | Investigate root causes inline |
| Update TODO.md status | Open PRs |

If you find yourself running `git`, `uv run pytest`, or editing source files — **stop**.
Write a TODO entry and dispatch an agent instead.

**Ralph owns:** implementing, testing, committing, pushing, opening PRs, rebasing onto main.
**Bart owns:** reviewing diff, running tests, posting comments, merging or rejecting.
**Orchestrator owns:** dispatch decisions, state tracking, triage of verdicts, wave sequencing.

## Step 1 — Dependency Analysis

Before creating worktrees, identify which TODO items touch the same source files.
Items touching shared hub files (e.g. `cli/utils.py`, `cli/main.py`, `api/client.py`)
**must go in the same branch or be sequenced**, not parallelised.

```bash
# Find which source files each TODO item would touch
# Then check fan-out: files imported by 3+ others are hubs
grep -rn "from terrapyne.cli.utils\|from .utils" src/
```

Group items into **waves**:
- Wave 0: independent S-effort items with no shared files (quick wins, unblock CI)
- Wave 1: parallel independent features (one worktree each)
- Wave 2: items that depend on Wave 1 landing to main first

See `references/dependency-analysis.md` for a worked example.

---

## Step 2 — Create Worktrees

```bash
git worktree add .worktrees/<name> -b <branch> origin/main
cd .worktrees/<name> && <setup-command>  # uv sync, npm install, etc.
```

Rules:
- Always base off `origin/main` — never off another feature branch
- Verify `.worktrees/` is gitignored: `git check-ignore -q .worktrees && echo ok`
- One worktree per independent feature — never share worktrees between agents

---

## Step 3 — Model Spread

| Task character | Model | Via |
|---|---|---|
| Focused feature, new API/CLI commands | `haiku` | claude-sub-agent |
| Bug fixes, correctness-sensitive changes | `sonnet` | claude-sub-agent |
| Large refactor, structural surgery, complex reasoning | `gemini-3-flash-preview` | gemini-sub-agent |
| Bart review (all) | `gemini-3-flash-preview` | gemini-sub-agent |
| Fallback when Gemini quota exhausted | `sonnet` | claude-sub-agent |
| Re-run after rejection | same model as original | consistency |

Claude CLI invocation for headless use:
```bash
claude --print --output-format stream-json \
  --dangerously-skip-permissions \
  --no-session-persistence \
  --model haiku \
  -p @/tmp/ralph-<feature>.md \
  > /tmp/claude-<feature>.jsonl 2>&1 &
```
Monitor: `python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py /tmp/claude-<feature>.jsonl`
Poll:    `python3 ~/.pi/agent/skills/claude-sub-agent/scripts/poll.py "$TARGET" --interval 30`

See `references/model-spread.md` for the rationale.

---

## Step 4 — Write Agent Artifacts

**Use `dispatch.py` — do not write prompts or launch scripts by hand.**

```bash
DISPATCH=~/.pi/agent/skills/agent-mux/scripts/dispatch.py

# Ralph: implement a task
python3 $DISPATCH --repo /path/to/repo ralph <TASK_ID> --pane <session:window.pane>

# Bart: review a PR
python3 $DISPATCH --repo /path/to/repo bart <TASK_ID> --pr <N> --pane <session:window.pane>

# Show state
python3 $DISPATCH --repo /path/to/repo status

# List TODO items
python3 $DISPATCH --repo /path/to/repo list
```

`dispatch.py` automatically:
- Reads the task detail section from TODO.md and uses it verbatim as the prompt
- Creates the worktree off `origin/main` (`fix/<task-id>` branch)
- Selects model from `AGENT_CONFIG` in the script (edit once, applies everywhere)
- Writes `/tmp/ralph-<id>.md` (or `bart-<id>.md`) and `/tmp/launch-<agent>-<id>.sh`
- Sends the launch script to the tmux pane
- Updates dispatch state (`.worktrees/planning/.dispatch-state.json`)

For persona injection and model overrides, edit `AGENT_CONFIG` at the top of `dispatch.py`.
See `scripts/dispatch.py` for the full config and template details.

---

## Step 5 — Launch Agents

**Always write a shell script. Never inline long commands in tmux send-keys.**

### Claude sub-agent (preferred for focused features, quota-safe)

```bash
cat > /tmp/launch-<feature>.sh << 'SCRIPT'
#!/bin/bash
cd /path/to/worktree
> /tmp/claude-<feature>.jsonl
claude --print --output-format stream-json \
  --dangerously-skip-permissions \
  --no-session-persistence \
  --model haiku \
  -p @/tmp/ralph-<feature>.md \
  >> /tmp/claude-<feature>.jsonl 2>&1 &
echo "PID: $!"
python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py \
  /tmp/claude-<feature>.jsonl
SCRIPT
chmod +x /tmp/launch-<feature>.sh
tmux send-keys -t "$TARGET" "bash /tmp/launch-<feature>.sh" Enter
```

### Gemini sub-agent (large refactors, complex reasoning)

```bash
cat > /tmp/launch-<feature>.sh << 'SCRIPT'
#!/bin/bash
cd /path/to/worktree
> /tmp/gemini-<feature>.jsonl
gemini -y --output-format stream-json --model gemini-3-flash-preview \
  -p @/tmp/ralph-<feature>.md \
  >> /tmp/gemini-<feature>.jsonl 2>&1 &
echo "PID: $!"
python3 ~/.pi/agent/skills/gemini-sub-agent/scripts/monitor.py \
  /tmp/gemini-<feature>.jsonl
SCRIPT
chmod +x /tmp/launch-<feature>.sh
tmux send-keys -t "$TARGET" "bash /tmp/launch-<feature>.sh" Enter
```

For pi agents, same background-then-monitor pattern with `pi-monitor.py`.

See `claude-sub-agent`, `gemini-sub-agent`, and `pi-sub-agent` skills for full invocation flags.

---

## Step 6 — Bart Review Loop

After Ralph opens a PR, launch Bart as a Claude sub-agent using the `bart` skill.
Bart handles both evidence gathering and the merge/reject decision.

```bash
cat > /tmp/bart-<feature>.md << 'EOF'
# Bart review — PR #<N>

## Working directory
You are in /path/to/worktree. Do NOT cd elsewhere for any command.

## Context
- PR: #<N> on <owner>/<repo>
- Branch: <branch>
- Task: <copy one-line description from TODO.md>
- Pre-existing failures to ignore: <list from baseline run, or "none">

## Your job
Use the `bart` skill. Review PR #<N> in PR review mode:
1. Read the diff: `gh pr diff <N>`
2. Run the tests
3. Apply the adversarial checklist
4. Post inline comments for BLOCKERs
5. Write verdict to /tmp/bart-verdict-<feature>.md
6. If APPROVED: merge with `gh pr merge <N> --squash --delete-branch`
   If REJECTED: leave open, write issues, do NOT merge
EOF
```

Launch via claude-sub-agent with bart persona appended:
```bash
cat > /tmp/launch-bart-<feature>.sh << 'SCRIPT'
#!/bin/bash
cd /path/to/worktree
> /tmp/claude-bart-<feature>.jsonl
claude --print --output-format stream-json \
  --dangerously-skip-permissions \
  --no-session-persistence \
  --model sonnet \
  --append-system-prompt @~/.pi/agents/bart.md \
  -p @/tmp/bart-<feature>.md \
  >> /tmp/claude-bart-<feature>.jsonl 2>&1 &
echo "PID: $!"
python3 ~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py \
  /tmp/claude-bart-<feature>.jsonl
SCRIPT
chmod +x /tmp/launch-bart-<feature>.sh
tmux send-keys -t "$TARGET" "bash /tmp/launch-bart-<feature>.sh" Enter
```

### Orchestrator actions on verdict

| Outcome | Bart action | Orchestrator action |
|---|---|---|
| APPROVED | Posts inline comments (if any MINOR), merges PR | Accumulate MINOR notes to FEEDBACK.md |
| REJECTED | Posts BLOCKER comments, writes verdict, does NOT merge | Triage; write targeted ralph-v2 prompt; relaunch Ralph |

---

## Step 7 — Feedback Accumulation

After all Barts in a wave finish, accumulate into the **planning branch** `FEEDBACK.md`:

```bash
bash /tmp/accumulate-feedback.sh
```

Triage before writing next wave prompts:
- **Critical rejections** → write targeted `ralph-<feature>-v<N>.md`, re-run Ralph
- **Systemic patterns** (same observation across 3+ PRs) → add to next wave guardrails
- **Non-critical one-offs** → acknowledge in FEEDBACK.md, defer

**Never commit feedback files to feature branches or main.**
`planning/FEEDBACK.md` is the only accumulator — committed to the planning branch only.

---

## Supervisor Mode

For large backlogs (6+ branches), run a continuous supervisor loop:

1. Write `/tmp/supervisor-poll.sh` — checks all JSONL files for completion
2. Poll every ~5 min: `watch -n 300 bash /tmp/supervisor-poll.sh`
3. On Ralph completion → launch Bart immediately on the same pane
4. On Bart APPROVED → run `accumulate-feedback.sh`, update `supervisor-state.md`
5. On Bart REJECTED → triage issues, write targeted `ralph-<feature>-v<N>.md`, relaunch Ralph
6. Wave 2 branches launch as Wave 1 panes free up
7. Update `agent-mux` skill with new learnings after each wave

### Adaptive polling — use supervisor-watch.py

Never use `sleep N && check` loops. Use `references/supervisor-watch.py` instead:

```bash
# Edit AGENTS list at top of script to match current wave
python3 ~/.pi/agent/skills/agent-mux/references/supervisor-watch.py
```

Adaptive sleep principle:
- **Young agent** (just started, file growing fast) → poll every 5s
- **Mature agent** (file growing slowly) → back off toward 60s
- **Stalled agent** (file not growing for >120s) → flag immediately, don't wait
- **Terminal event** (`agent_end` or `result` line) → wake immediately, report
- **Sleep interval** = `min(poll_interval for all active agents)` — the most urgent agent drives the cadence

To add/remove agents from the watch list, edit the `AGENTS = [...]` block at the top of the script. Copy the script to `/tmp/` and edit there — don't modify the skill copy.

### Supervisor state file

Keep `/tmp/supervisor-state.md` updated:
```markdown
| Branch | PR | Ralph | Bart | Action |
|---|---|---|---|---|
| fix/quick-wins | #32 | v2 running | REJECTED v1 | waiting |
```

### Quota management

Gemini has a per-session quota. If you get `exhausted capacity` errors:
- Switch pending gemini agents to `claude-sub-agent` with `--model haiku`
- Update launch scripts: replace `gemini -y --output-format stream-json` with
  `claude --print --output-format stream-json --dangerously-skip-permissions --no-session-persistence --model haiku`
- Monitor with `claude-sub-agent/scripts/monitor.py` instead of `gemini-sub-agent/scripts/monitor.py`
- Gemini quota resets — switch back before Wave 2 if preferred

## Pitfalls (hard-won, not obvious)

### gemini /tmp/ is not writable
Gemini runs in a sandboxed context and can only write to `~/.gemini/tmp/<worktree-name>/`.
Tell Bart to write issues there, not `/tmp/`.
Accumulate from `~/.gemini/tmp/<wt>/bart-issues-*.md`.

### tmux send-keys truncates long commands
Any command > ~200 chars sent via `tmux send-keys` gets silently cut.
Always write to a script file first, then `tmux send-keys "bash /tmp/script.sh" Enter`.

### Monitor blocks if gemini runs in foreground
If you send `gemini ... > file &` and then the monitor command in the same pane,
but the script runs gemini in foreground, the pane is blocked.
Always background gemini (`&`) before launching the monitor in the script.

### gemini model names
Only `gemini-2.5-flash` and `gemini-2.5-pro` work via API key.
`gemini-3-flash-preview` works via the `gemini` CLI with user auth (OAuth).
Test first: `echo "hi" | gemini -y -p "say hello" --model <name>` before wiring into agents.

### Bart `gh pr merge` fails with "main is already used by worktree"
When Bart runs from a worktree, `gh pr merge --delete-branch` tries to checkout `main`
locally to fast-forward — but `main` is locked by the primary worktree.
Fix in Bart prompt: tell Bart to use `gh pr merge --squash` without `--delete-branch`,
or pass `--repo owner/repo` explicitly. Remote branch deletion still works.
Add to Bart prompt: `gh pr merge <N> --squash --repo <owner>/<repo>` (omit `--delete-branch`).

### `gh pr review --comment` vs `gh pr comment`
`gh pr review --comment "text"` posts an inline diff comment and requires `--file` + `--line`.
For a standalone PR summary comment, use `gh pr comment <N> --body-file /tmp/verdict.md`.
Bart often confuses these. The bart skill documents the correct syntax; ensure the prompt
tells Bart to write verdict to a file first, then use `--body-file`.

### Verdict filename case
Bart sometimes writes `/tmp/bart-verdict-B2.md` (uppercase) instead of the lowercase convention.
`dispatch.py triage` now checks both cases automatically.

### Pre-existing failures
Always run `uv run pytest tests/ -x -q` on `origin/main` before any wave.
Note which tests fail. Bart must not flag pre-existing failures as new regressions.
Include the list explicitly in every Bart prompt.

### Bart going rogue (acting as Ralph)
Gemini's Bart sometimes starts implementing fixes instead of just reviewing.
Add to Bart persona: `ABSOLUTE RULE: DO NOT write code. DO NOT edit source files.
You are a reviewer only. If you find yourself editing .py files — STOP immediately.`

### Module-level Console() captures at import time
Rich `Console()` captures `sys.stdout`/`sys.stderr` at instantiation.
In tests with `CliRunner`, the real stdout is replaced — module-level consoles miss it.
Fix: instantiate `Console(stderr=True)` inside functions, or use `force_terminal=False`.
This affects `rich_tables.py` and any module with a top-level `console = Console()`.

### paginate_with_meta mock gap
A common systemic failure: `TFCClient.paginate_with_meta` is not mocked in fixtures.
When a refactor changes code paths to call it, previously-passing tests break.
Fix in conftest: `mock_client.paginate_with_meta.return_value = (iter([]), 0)`
Include this in every project-specific guardrails template.

---

## References

- `references/dependency-analysis.md` — worked example of hub-file dependency mapping
- `references/model-spread.md` — model selection rationale
- `references/guardrails-template.md` — standard guardrails to prepend to all prompts
- `references/accumulate-feedback.sh` — session accumulator script
