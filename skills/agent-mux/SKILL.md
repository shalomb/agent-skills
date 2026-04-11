---
name: agent-mux
description: >
  Orchestrate multiple parallel sub-agents across git worktrees to burn down a
  TODO.md backlog. Handles dependency analysis, wave ordering, mixed model spread,
  Ralph/Bart loops, and feedback accumulation into a planning branch FEEDBACK.md.
  Use when implementing multiple independent features in parallel with TDD build
  agents and adversarial review agents.
  Triggers: "parallel agents", "burn down TODO", "multi-agent orchestration",
  "agent-mux", "wave of agents", "dispatch ralph and bart", "parallel worktrees".
---

# agent-mux — Multi-Agent Orchestrator

Compose `ralph`, `bart`, `gemini-sub-agent`, `pi-sub-agent`, and
`dispatching-parallel-agents` skills into a wave-based build+review pipeline
across git worktrees.

**Read these skills first — agent-mux builds on them, not instead of them:**
- `ralph` — TDD build loop
- `bart` — adversarial review loop
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
| Focused feature, new API/CLI commands | `anthropic/claude-haiku-4-5` | pi sub-agent |
| Large refactor, structural surgery, complex reasoning | `gemini-3-flash-preview` | gemini -y -p @file |
| Bart review (all) | `gemini-3-flash-preview` | gemini -y -p @file |
| Re-run after rejection | same model as original | consistency |

See `references/model-spread.md` for the rationale.

---

## Step 4 — Write Agent Artifacts

For each feature, write:
- `<worktree>/GEMINI.md` — persona loaded by gemini from CWD (guardrails + persona)
- `/tmp/ralph-<feature>.md` — scoped task prompt (pi agents read via `-p @file`)
- `/tmp/bart-<feature>.md` — review prompt written after Ralph opens PR

Use existing persona files from the `ralph` and `bart` skills as the base.
Prepend with project-specific guardrails. See `references/guardrails-template.md`.

---

## Step 5 — Launch Agents

**Always write a shell script. Never inline long commands in tmux send-keys.**

```bash
# Pattern for BOTH gemini and pi agents
cat > /tmp/launch-<feature>.sh << 'SCRIPT'
#!/bin/bash
cd /path/to/worktree
# gemini: background it so monitor can run in same pane
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

For pi agents, same pattern — background with `&`, then launch `pi-monitor.py`.

See `gemini-sub-agent` and `pi-sub-agent` skills for full invocation flags.

---

## Step 6 — Bart Review Loop

After Ralph opens a PR:

```bash
# Swap persona
cat guardrails.md bart-persona.md > <worktree>/GEMINI.md

# Write launch script (same backgrounded pattern as Step 5)
# Direct Bart to read the PR, run tests, decide approve/reject
```

Bart's decision:

| Outcome | Bart action | Orchestrator action |
|---|---|---|
| APPROVED | Merges PR (`gh pr merge --squash --delete-branch`) | Accumulate non-critical to FEEDBACK.md |
| REJECTED | Writes issues file, does NOT merge | Triage, write targeted Ralph v2 prompt, re-run |

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
- Switch all pending agents to `pi --models anthropic/claude-haiku-4-5`
- Update launch scripts from `gemini -y` to `pi --models haiku` pattern
- Gemini quota resets — check back before Wave 2

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
