#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""
dispatch.py — Agent-mux task dispatcher.

Reads a TODO.md, extracts task detail by ID, generates prompts and launch
scripts from templates, manages task state, and fires sub-agents into tmux panes.

Usage:
    # Ralph: implement a TODO item
    dispatch.py ralph B1 --pane terrapyne:2.0 --repo /home/unop/shalomb/terrapyne

    # Bart: review a PR
    dispatch.py bart B1 --pane terrapyne:2.0 --repo /home/unop/shalomb/terrapyne --pr 76

    # Show state
    dispatch.py status

    # List available TODO items
    dispatch.py list
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

# Runner: "claude", "gemini", or "kiro"
# Set via --runner flag or AGENT_MUX_RUNNER env var (default: claude)
DEFAULT_RUNNER = "claude"

# Per-agent model and flag defaults (mirrors Springfield's config.toml)
AGENT_CONFIG = {
    "ralph": {
        "claude": {
            "model": "sonnet",
            "persona": None,
            "jsonl": "/tmp/claude-ralph-{id}.jsonl",
            "monitor": str(pathlib.Path(__file__).resolve().parent.parent.parent / "claude-sub-agent" / "scripts" / "monitor.py"),
        },
        "kiro": {
            "model": None,  # uses kiro default
            "logfile": "/tmp/kiro-ralph-{id}.log",
        },
        "gemini": {
            "model": "gemini-2.5-flash",
            "jsonl": "/tmp/gemini-ralph-{id}.jsonl",
            "monitor": str(pathlib.Path(__file__).resolve().parent.parent.parent / "gemini-sub-agent" / "scripts" / "monitor.py"),
        },
    },
    "bart": {
        "claude": {
            "model": "sonnet",
            "persona": "~/.pi/agents/bart.md",
            "jsonl": "/tmp/claude-bart-{id}.jsonl",
            "monitor": str(pathlib.Path(__file__).resolve().parent.parent.parent / "claude-sub-agent" / "scripts" / "monitor.py"),
        },
        "kiro": {
            "model": None,
            "logfile": "/tmp/kiro-bart-{id}.log",
        },
        "gemini": {
            "model": "gemini-2.5-flash",
            "jsonl": "/tmp/gemini-bart-{id}.jsonl",
            "monitor": str(pathlib.Path(__file__).resolve().parent.parent.parent / "gemini-sub-agent" / "scripts" / "monitor.py"),
        },
    },
}


def get_runner() -> str:
    """Get the active runner from env or default."""
    import os
    return os.environ.get("AGENT_MUX_RUNNER", DEFAULT_RUNNER)

# ── State machine ──────────────────────────────────────────────────────────────

TRANSITIONS = {
    "todo":        {"ralph_start": "in_progress"},
    "in_progress": {"ralph_done": "in_review", "ralph_fail": "todo"},
    "in_review":   {"bart_approved": "done", "bart_rejected": "todo"},
    "done":        {},
}

# ── TODO.md parsing ────────────────────────────────────────────────────────────

def find_todo_md(repo: Path) -> Path:
    """Find TODO.md — check planning worktree first, then repo root."""
    candidates = [
        repo / ".worktrees" / "planning" / "TODO.md",
        repo / "TODO.md",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"TODO.md not found in {repo}")


def find_plan_md(repo: Path) -> Path | None:
    """Find PLAN.md for epic-level tasks."""
    candidates = [
        repo / ".worktrees" / "planning" / "PLAN.md",
        repo / "PLAN.md",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def extract_task(todo_path: Path, task_id: str) -> dict:
    """Extract task detail section from TODO.md or PLAN.md by ID."""
    text = todo_path.read_text()

    # Find one-liner from matrix table
    # Matches: | B1 | [BUG] description | ...
    matrix_pattern = rf"^\|\s*{re.escape(task_id)}\s*\|([^|]+)\|"
    matrix_match = re.search(matrix_pattern, text, re.MULTILINE)
    one_liner = matrix_match.group(1).strip() if matrix_match else task_id

    # Find detail section: ### B1 — ... or ## EPIC-001 — ... up to next heading of same level or ---
    detail_pattern = rf"^##\s+{re.escape(task_id)}\b.*?(?=^##\s[^#]|\Z)"
    detail_match = re.search(detail_pattern, text, re.MULTILINE | re.DOTALL)
    if not detail_match:
        # Try ### level (TODO.md style)
        detail_pattern = rf"^###\s+{re.escape(task_id)}\b.*?(?=^###\s|\Z)"
        detail_match = re.search(detail_pattern, text, re.MULTILINE | re.DOTALL)

    detail = detail_match.group(0).strip() if detail_match else ""

    if not detail:
        # Try PLAN.md if we were searching TODO.md
        repo = todo_path.parent
        plan = find_plan_md(repo)
        if plan and plan != todo_path:
            return extract_task(plan, task_id)
        raise ValueError(f"No detail section found for task {task_id} in {todo_path}")

    return {
        "id": task_id,
        "one_liner": one_liner,
        "detail": detail,
    }


def list_todo_items(todo_path: Path) -> list[dict]:
    """List all TODO items from the priority matrix."""
    text = todo_path.read_text()
    items = []
    for line in text.splitlines():
        # Match: | ID | description | ... (flexible — any table row with a task ID)
        m = re.match(
            r"^\|\s*([A-Z]+\d+[\w.]*)\s*\|\s*(.+?)\s*\|",
            line,
        )
        if m:
            task_id = m.group(1)
            description = m.group(2).strip().strip("`")
            # Check for explicit status column (TODO, ✅, 🔄)
            status_match = re.search(r"\|\s*(TODO|✅[^|]*|🔄[^|]*)\s*\|", line)
            status = status_match.group(1).strip() if status_match else "TODO"
            items.append({
                "id": task_id,
                "description": description,
                "status": status,
            })
    return items


# ── State management ───────────────────────────────────────────────────────────

def state_path(repo: Path) -> Path:
    return repo / ".worktrees" / "planning" / ".dispatch-state.json"


def load_state(repo: Path) -> dict:
    p = state_path(repo)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_state(repo: Path, state: dict) -> None:
    p = state_path(repo)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))


def transition(repo: Path, task_id: str, signal: str) -> str:
    """Apply a state transition signal; return new status."""
    state = load_state(repo)
    current = state.get(task_id, {}).get("status", "todo")
    allowed = TRANSITIONS.get(current, {})
    if signal not in allowed:
        raise ValueError(
            f"Invalid signal '{signal}' from state '{current}' "
            f"for {task_id}. Allowed: {list(allowed)}"
        )
    new_status = allowed[signal]
    if task_id not in state:
        state[task_id] = {}
    state[task_id]["status"] = new_status
    state[task_id].setdefault("history", []).append({
        "signal": signal,
        "from": current,
        "to": new_status,
        "at": datetime.now(UTC).isoformat(),
    })
    save_state(repo, state)
    return new_status


# ── Worktree management ────────────────────────────────────────────────────────

def branch_prefix_for(task_id: str) -> str:
    """Derive conventional branch prefix from task ID."""
    prefixes = {
        "B": "fix",
        "C": "fix",
        "F": "feat",
        "AX": "feat",
        "A": "refactor",
        "D": "docs",
        "EPIC": "feat",
    }
    # Check longest prefix first (EPIC before E, AX before A)
    for key in sorted(prefixes, key=len, reverse=True):
        if task_id.startswith(key):
            return prefixes[key]
    return "fix"


def slugify(text: str, max_len: int = 50) -> str:
    """Convert a description into a branch-safe slug."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len].rstrip("-")


def ensure_worktree(repo: Path, task_id: str, one_liner: str = "",
                    branch_prefix: str | None = None) -> Path:
    """Create worktree for task if it doesn't exist; return path."""
    prefix = branch_prefix or branch_prefix_for(task_id)

    # Build a descriptive slug: "f4-workspace-notifications" or "b12-truncation"
    desc_slug = slugify(one_liner) if one_liner else task_id.lower().replace(".", "-")
    slug = f"{task_id.lower()}-{desc_slug}" if one_liner else task_id.lower().replace(".", "-")
    # Avoid redundancy if one_liner already starts with the ID
    if desc_slug.startswith(task_id.lower()):
        slug = desc_slug

    branch = f"{prefix}/{slug}"
    wt_path = repo / ".worktrees" / slug

    if wt_path.exists():
        return wt_path

    subprocess.run(
        ["git", "worktree", "add", str(wt_path), "-b", branch, "origin/main"],
        cwd=repo, check=True,
    )
    result = subprocess.run(["uv", "sync", "-q"], cwd=wt_path, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  uv sync warning: {result.stderr.strip()[:120]}")
    return wt_path


def baseline_check(worktree: Path, test_cmd: list[str] | None = None) -> bool:
    """Run test suite; return True if green. Print summary."""
    cmd = test_cmd or [
        "uv", "run", "pytest", "tests/", "--ignore=tests/uat",
        "-q", "--override-ini=addopts=", "--tb=no",
    ]
    print("  Baseline check...", end=" ", flush=True)
    result = subprocess.run(cmd, cwd=worktree, capture_output=True, text=True)
    last = (result.stdout + result.stderr).strip().splitlines()
    summary = last[-1] if last else "(no output)"
    ok = result.returncode == 0
    icon = "✅" if ok else "❌"
    print(f"{icon} {summary}")
    return ok


def open_pr(worktree: Path, task: dict, repo: Path) -> int | None:
    """Open a GitHub PR for the task branch; return PR number or None."""
    remote = subprocess.check_output(
        ["git", "remote", "get-url", "origin"], cwd=repo, text=True
    ).strip()
    m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    _owner = m.group(1) if m else "owner"
    _repo_name = m.group(2) if m else "repo"

    body = (
        f"## Summary\n\nImplements {task['id']} from the backlog.\n\n"
        f"{task['detail'][:500]}\n\n"
        f"Closes {task['id']} in TODO.md"
    )
    result = subprocess.run(
        ["gh", "pr", "create",
         "--title", f"{task['one_liner']} ({task['id']})",
         "--body", body,
         "--base", "main"],
        cwd=worktree, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ⚠️  PR creation failed: {result.stderr.strip()[:120]}")
        return None
    url = result.stdout.strip()
    pr_num = int(url.rstrip("/").split("/")[-1])
    print(f"  PR: {url}")
    return pr_num


def rebase_on_main(worktree: Path) -> bool:
    """Fetch origin/main and rebase; return True on success."""
    subprocess.run(["git", "fetch", "origin"], cwd=worktree,
                   capture_output=True, check=False)
    result = subprocess.run(
        ["git", "rebase", "origin/main"],
        cwd=worktree, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ⚠️  Rebase failed: {result.stderr.strip()[:120]}")
        return False
    subprocess.run(["git", "push", "--force-with-lease"], cwd=worktree,
                   capture_output=True, check=False)
    return True


# ── Prompt generation ──────────────────────────────────────────────────────────

GUARDRAILS = """\
## Working directory
You are running in {worktree}. Do NOT cd elsewhere for any command.
All git, gh, pytest, and uv commands run from this directory.

## Git safety (pre-flight before any git operation)
```bash
export GPG_TTY=$(tty)
export GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true EDITOR=true VISUAL=true
export GIT_TERMINAL_PROMPT=0 GIT_ASK_YESNO=false GIT_PAGER=cat
```
- Never disable GPG signing (`--no-gpg-sign` or `commit.gpgsign=false` are forbidden)
- If GPG key is locked: stop and report — do not work around it
- Use `git -c commit.gpgsign=false commit` ONLY if GPG is genuinely unavailable in this env

## Non-negotiable rules
- Red/Green TDD: write a failing test first, minimal code to pass, then refactor
- One atomic ACP commit: code + tests together, Conventional Commits format
- Use `uv run pytest tests/ --ignore=tests/uat -q --override-ini="addopts="` to run tests
- Do NOT fix anything outside the scope of this task
- After committing: push the branch and open a PR with `gh pr create`
- After opening PR: rebase onto latest origin/main before requesting review:
  `git fetch origin && git rebase origin/main && git push --force-with-lease`
"""

RALPH_TEMPLATE = """\
# Ralph — {id}: {one_liner}

{guardrails}

## Task

{detail}
"""

RALPH_WAVE_TEMPLATE = """\
# Ralph — Wave [{ids}]

{guardrails}

## Tasks — implement ALL of the following in one branch, one commit per task

Work through each task in order. For each:
1. Write a failing test (Red)
2. Minimal code to pass (Green)
3. Run full suite before moving on
4. One atomic commit per task (`type(scope): description`)

After all tasks are committed: push the branch and open ONE PR covering all.

{tasks}
"""

BART_TEMPLATE = """\
# Bart review — PR #{pr} ({id}: {one_liner})

{guardrails}

## Context
- PR: #{pr} on {owner}/{repo}
- Branch: {branch}
- Pre-existing failures to ignore: {preexisting}

## Task that was implemented
{detail}

## Your job
Use the `bart` skill in PR review mode:
1. Read the diff: `gh pr diff {pr}`
2. Run the tests
3. Apply the adversarial checklist
4. Post inline BLOCKER comments: `gh pr review {pr} --comment "BLOCKER: ..." --file path --line N`
5. Write verdict to /tmp/bart-verdict-{id}.md
6. If APPROVED: `gh pr merge {pr} --squash --repo {owner}/{repo}`
   (omit --delete-branch to avoid "main is already used by worktree" error)
   If REJECTED: write issues, do NOT merge, do NOT edit source files
"""

LAUNCH_TEMPLATE = """\
#!/bin/bash
cd {worktree}
> {jsonl}
claude --print --output-format stream-json \\
  --dangerously-skip-permissions \\
  --no-session-persistence \\
  --model {model} \\
{persona_line}  -p @{prompt} \\
  >> {jsonl} 2>&1 &
echo "PID: $!"
python3 {monitor} {jsonl}
"""

KIRO_LAUNCH_TEMPLATE = """\
#!/bin/bash
cd {worktree}
echo "KIRO_START: $(date -Iseconds)" | tee {logfile}
echo "─── {prompt} ───"
kiro-cli chat --trust-all-tools --no-interactive --agent yolo{model_flag} "$(cat {prompt})" 2>&1 | tee -a {logfile}
echo "KIRO_EXIT: ${{PIPESTATUS[0]}}" | tee -a {logfile}
echo "KIRO_END: $(date -Iseconds)" | tee -a {logfile}
"""

GEMINI_LAUNCH_TEMPLATE = """\
#!/bin/bash
cd {worktree}
> {jsonl}
gemini -y --output-format stream-json --model {model} \\
  -p @{prompt} \\
  >> {jsonl} 2>&1 &
echo "PID: $!"
python3 {monitor} {jsonl}
"""


def write_prompt(agent: str, task: dict, worktree: Path, repo: Path,
                 pr: int | None = None, preexisting: str = "none") -> Path:
    """Generate and write the agent prompt file; return path."""
    guardrails = GUARDRAILS.format(worktree=worktree)

    if agent == "ralph":
        content = RALPH_TEMPLATE.format(
            id=task["id"],
            one_liner=task["one_liner"],
            guardrails=guardrails,
            detail=task["detail"],
        )
    elif agent == "bart":
        # Get repo owner/name from git remote
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], cwd=repo, text=True
        ).strip()
        m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
        owner, repo_name = (m.group(1), m.group(2)) if m else ("owner", "repo")

        # Get current branch
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=worktree, text=True
        ).strip()

        content = BART_TEMPLATE.format(
            id=task["id"],
            one_liner=task["one_liner"],
            guardrails=guardrails,
            pr=pr,
            owner=owner,
            repo=repo_name,
            branch=branch,
            preexisting=preexisting,
            detail=task["detail"],
        )
    else:
        raise ValueError(f"Unknown agent: {agent}")

    prompt_path = Path(f"/tmp/{agent}-{task['id'].lower()}.md")
    prompt_path.write_text(content)
    print(f"  Prompt: {prompt_path}")
    return prompt_path


def write_launch_script(agent: str, task: dict, worktree: Path, prompt: Path,
                        runner: str | None = None) -> Path:
    """Generate and write the launch script; return path."""
    runner = runner or get_runner()
    cfg = AGENT_CONFIG[agent][runner]
    task_slug = task["id"].lower()

    if runner == "kiro":
        logfile = cfg["logfile"].format(id=task_slug)
        model_flag = f" --model {cfg['model']}" if cfg.get("model") else ""
        content = KIRO_LAUNCH_TEMPLATE.format(
            worktree=worktree,
            logfile=logfile,
            model_flag=model_flag,
            prompt=prompt,
        )
    elif runner == "gemini":
        jsonl = cfg["jsonl"].format(id=task_slug)
        content = GEMINI_LAUNCH_TEMPLATE.format(
            worktree=worktree,
            jsonl=jsonl,
            model=cfg["model"],
            prompt=prompt,
            monitor=cfg["monitor"],
        )
    else:  # claude (default)
        jsonl = cfg["jsonl"].format(id=task_slug)
        monitor = cfg["monitor"]
        persona = cfg.get("persona")
        persona_line = f"  --append-system-prompt @{persona} \\\n" if persona else ""
        content = LAUNCH_TEMPLATE.format(
            worktree=worktree,
            jsonl=jsonl,
            model=cfg["model"],
            persona_line=persona_line,
            prompt=prompt,
            monitor=monitor,
        )

    script_path = Path(f"/tmp/launch-{agent}-{task_slug}.sh")
    script_path.write_text(content)
    script_path.chmod(0o755)
    print(f"  Script: {script_path}")
    return script_path


# ── tmux dispatch ──────────────────────────────────────────────────────────────

AGENT_SESSION = None  # Use current tmux session by default


def current_tmux_session() -> str | None:
    """Get the current tmux session name (from $TMUX_PANE or fallback)."""
    import os
    pane = os.environ.get("TMUX_PANE")
    if pane:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#{session_name}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    # Fallback: pick the attached session
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name} #{session_attached}"],
        capture_output=True, text=True,
    )
    for line in result.stdout.strip().splitlines():
        name, attached = line.rsplit(" ", 1)
        if attached == "1":
            return name
    return None


def ensure_agent_panes(num_panes: int = 2, session: str | None = None) -> list[str]:
    """Ensure N bash windows exist in the target session for agent work.
    Creates new windows in the current session by default. Returns pane targets."""
    session = session or current_tmux_session()
    if not session:
        # No tmux at all — create a detached session
        session = "agents"
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session, "-n", "agent-0"],
            check=True,
        )

    # Find existing free bash panes in this session
    result = subprocess.run(
        ["tmux", "list-panes", "-s", "-t", session,
         "-F", "#{session_name}:#{window_index}.#{pane_index} #{pane_current_command}"],
        capture_output=True, text=True,
    )
    free_panes = []
    for line in result.stdout.strip().splitlines():
        target, cmd = line.split(" ", 1)
        if cmd == "bash":
            free_panes.append(target)

    # Create additional windows if we don't have enough
    while len(free_panes) < num_panes:
        idx = len(free_panes)
        subprocess.run(
            ["tmux", "new-window", "-t", session, "-n", f"agent-{idx}"],
            check=True,
        )
        # Get the new pane target
        new_pane = subprocess.check_output(
            ["tmux", "display-message", "-t", f"{session}:agent-{idx}",
             "-p", "#{session_name}:#{window_index}.#{pane_index}"],
            text=True,
        ).strip()
        free_panes.append(new_pane)

    return free_panes[:num_panes]


def find_free_pane(prefer: str | None = None) -> str | None:
    """Find a free bash pane; return tmux target or None."""
    result = subprocess.run(
        ["tmux", "list-panes", "-a", "-F",
         "#{session_name}:#{window_index}.#{pane_index} #{pane_current_command}"],
        capture_output=True, text=True,
    )
    panes = []
    for line in result.stdout.strip().splitlines():
        target, cmd = line.split(" ", 1)
        if prefer and target == prefer:
            return target  # Always use preferred pane if specified
        if cmd == "bash":
            panes.append(target)
    return panes[0] if panes else None


def dispatch_to_pane(pane: str, script: Path) -> None:
    """Send launch script to tmux pane."""
    subprocess.run(
        ["tmux", "send-keys", "-t", pane, f"bash {script}", "Enter"],
        check=True,
    )
    print(f"  Dispatched to pane: {pane}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def cmd_ralph(args, repo: Path) -> None:
    todo = find_todo_md(repo)
    task = extract_task(todo, args.task_id)
    runner = args.runner or get_runner()
    print(f"\n▶ Ralph ({runner}): {args.task_id} — {task['one_liner']}")

    wt = ensure_worktree(repo, args.task_id, one_liner=task["one_liner"],
                         branch_prefix=args.branch_prefix)
    print(f"  Worktree: {wt}")
    if not getattr(args, "skip_baseline", False):
        ok = baseline_check(wt)
        if not ok:
            print("  ❌ Baseline is red. Fix the baseline before dispatching Ralph.")
            print("  Tip: add a TODO entry for the baseline fix and dispatch that first.")
            print("  Override with --skip-baseline if failures are known pre-existing.")
            sys.exit(1)

    prompt = write_prompt("ralph", task, wt, repo)
    script = write_launch_script("ralph", task, wt, prompt, runner=runner)

    pane = args.pane or find_free_pane()
    if not pane:
        panes = ensure_agent_panes(num_panes=2)
        pane = panes[0]
        print(f"  Provisioned agent panes in current session: {len(panes)} panes")

    transition(repo, args.task_id, "ralph_start")
    dispatch_to_pane(pane, script)
    print("\n  State: todo → in_progress")

    cfg = AGENT_CONFIG["ralph"][runner]
    if runner == "kiro":
        print(f"  Log: {cfg['logfile'].format(id=args.task_id.lower())}")
    else:
        print(f"  Monitor JSONL: {cfg['jsonl'].format(id=args.task_id.lower())}")


def cmd_wave(args, repo: Path) -> None:
    """Dispatch Ralph to implement multiple related TODO items in one branch."""
    todo = find_todo_md(repo)
    task_ids = args.task_ids  # e.g. ["D2", "D3", "D4"]
    tasks = [extract_task(todo, tid) for tid in task_ids]
    wave_id = "-".join(t["id"].lower() for t in tasks)
    one_liner = ", ".join(t["id"] for t in tasks)
    runner = args.runner or get_runner()

    print(f"\n▶ Wave Ralph ({runner}): [{one_liner}]")

    # For waves, derive prefix from first task and build a combined slug
    prefix = args.branch_prefix or branch_prefix_for(task_ids[0])
    # Use first task's description as the slug base
    wave_slug = slugify(tasks[0]["one_liner"], max_len=40)
    wave_branch_id = f"{wave_id}-{wave_slug}" if wave_slug else wave_id
    wt = ensure_worktree(repo, wave_id, one_liner=tasks[0]["one_liner"],
                         branch_prefix=prefix)
    print(f"  Worktree: {wt}")

    if not getattr(args, "skip_baseline", False):
        ok = baseline_check(wt)
        if not ok:
            print("  ❌ Baseline is red. Fix before dispatching.")
            sys.exit(1)

    guardrails = GUARDRAILS.format(worktree=wt)
    tasks_section = "\n\n".join(
        f"---\n\n{t['detail']}" for t in tasks
    )
    content = RALPH_WAVE_TEMPLATE.format(
        ids=one_liner,
        guardrails=guardrails,
        tasks=tasks_section,
    )
    prompt_path = Path(f"/tmp/ralph-wave-{wave_id}.md")
    prompt_path.write_text(content)
    print(f"  Prompt: {prompt_path}")

    # Build launch script
    cfg = AGENT_CONFIG["ralph"][runner]
    wave_task = {"id": f"wave-{wave_id}", "one_liner": one_liner}

    if runner == "kiro":
        logfile = f"/tmp/kiro-ralph-wave-{wave_id}.log"
        model_flag = f" --model {cfg['model']}" if cfg.get("model") else ""
        script_content = KIRO_LAUNCH_TEMPLATE.format(
            worktree=wt,
            logfile=logfile,
            model_flag=model_flag,
            prompt=prompt_path,
        )
    elif runner == "gemini":
        jsonl = f"/tmp/gemini-ralph-wave-{wave_id}.jsonl"
        script_content = GEMINI_LAUNCH_TEMPLATE.format(
            worktree=wt,
            jsonl=jsonl,
            model=cfg["model"],
            prompt=prompt_path,
            monitor=cfg["monitor"],
        )
    else:  # claude
        jsonl = f"/tmp/claude-ralph-wave-{wave_id}.jsonl"
        persona_line = f"  --append-system-prompt @{cfg['persona']} \\\n" if cfg.get("persona") else ""
        script_content = LAUNCH_TEMPLATE.format(
            worktree=wt,
            jsonl=jsonl,
            model=cfg["model"],
            persona_line=persona_line,
            prompt=prompt_path,
            monitor=cfg["monitor"],
        )

    script_path = Path(f"/tmp/launch-ralph-wave-{wave_id}.sh")
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    print(f"  Script: {script_path}")

    pane = args.pane or find_free_pane()
    if not pane:
        panes = ensure_agent_panes(num_panes=2)
        pane = panes[0]
        print(f"  Provisioned agent panes in current session: {len(panes)} panes")

    for tid in task_ids:
        try:
            transition(repo, tid, "ralph_start")
        except ValueError:
            pass  # already in_progress is fine for re-runs

    dispatch_to_pane(pane, script_path)
    print(f"\n  Dispatched wave [{one_liner}] to pane: {pane}")
    if runner == "kiro":
        print(f"  Log: /tmp/kiro-ralph-wave-{wave_id}.log")
    else:
        print(f"  Monitor JSONL: /tmp/{runner}-ralph-wave-{wave_id}.jsonl")


def cmd_pr(args, repo: Path) -> None:
    """Open a PR for a task branch that Ralph committed but didn't push/PR."""
    todo = find_todo_md(repo)
    task = extract_task(todo, args.task_id)
    slug = args.task_id.lower().replace(".", "-")
    wt = repo / ".worktrees" / slug
    if not wt.exists():
        print(f"ERROR: Worktree {wt} not found.")
        sys.exit(1)

    # Rebase onto latest main first
    print(f"\n▶ PR: rebasing {args.task_id} onto origin/main...")
    if not rebase_on_main(wt):
        print("  ❌ Rebase failed. Resolve conflicts manually then re-run.")
        sys.exit(1)

    pr_num = open_pr(wt, task, repo)
    if pr_num:
        transition(repo, args.task_id, "ralph_done")
        print("  State: in_progress → in_review")


def cmd_rebase(args, repo: Path) -> None:
    """Rebase a task branch onto latest origin/main."""
    slug = args.task_id.lower().replace(".", "-")
    wt = repo / ".worktrees" / slug
    if not wt.exists():
        print(f"ERROR: Worktree {wt} not found.")
        sys.exit(1)
    print(f"\n▶ Rebase: {args.task_id} onto origin/main...")
    ok = rebase_on_main(wt)
    print("  ✅ Done" if ok else "  ❌ Failed")


def cmd_triage(args, repo: Path) -> None:
    """Read Bart's verdict file and summarise what to do next."""
    task_id = args.task_id
    # Try both cases — Bart sometimes writes uppercase ID in filename
    for candidate in [
        Path(f"/tmp/bart-verdict-{task_id.lower()}.md"),
        Path(f"/tmp/bart-verdict-{task_id.upper()}.md"),
        Path(f"/tmp/bart-verdict-{task_id}.md"),
    ]:
        if candidate.exists():
            verdict_path = candidate
            break
    else:
        print(f"No verdict file found for {task_id} in /tmp/")
        sys.exit(1)

    text = verdict_path.read_text()
    # Scan for VERDICT line (may not be first line)
    verdict_line = next(
        (ln.strip() for ln in text.splitlines() if ln.strip().startswith("VERDICT:")),
        None,
    )
    if not verdict_line:
        print(f"  Could not find VERDICT: line in {verdict_path}")
        sys.exit(1)

    print(f"\n▶ Triage: {task_id}")
    print(f"  Verdict: {verdict_line}")

    if "APPROVED" in verdict_line:
        transition(repo, task_id, "bart_approved")
        print("  State: in_review → done")
        print("  ✅ No action needed.")
    elif "REJECTED" in verdict_line:
        transition(repo, task_id, "bart_rejected")
        print("  State: in_review → todo")
        blockers = [line for line in text.splitlines() if "BLOCKER" in line]
        print(f"  {len(blockers)} BLOCKER(s):")
        for b in blockers:
            print(f"    {b.strip()[:100]}")
        print("  Next: dispatch.py ralph to fix BLOCKERs.")
    else:
        print(f"  Unrecognised verdict: {verdict_line}")


def cmd_bart(args, repo: Path) -> None:
    todo = find_todo_md(repo)
    task = extract_task(todo, args.task_id)
    runner = args.runner or get_runner()
    print(f"\n▶ Bart ({runner}): reviewing PR #{args.pr} for {args.task_id} — {task['one_liner']}")

    # Worktree: explicit override, or default fix/<id> convention, or create from branch
    if getattr(args, "worktree", None):
        wt = Path(args.worktree)
    else:
        slug = args.task_id.lower().replace(".", "-")
        wt = repo / ".worktrees" / slug

    if not wt.exists():
        # Try to create worktree from the PR's branch
        pr_branch = subprocess.check_output(
            ["gh", "pr", "view", str(args.pr), "--json", "headRefName", "--jq", ".headRefName"],
            cwd=repo, text=True,
        ).strip()
        if pr_branch:
            # Check if branch is already checked out in another worktree
            existing = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=repo, capture_output=True, text=True,
            ).stdout
            already_checked_out = any(
                f"branch refs/heads/{pr_branch}" in line
                for line in existing.splitlines()
            )
            if already_checked_out:
                # Find the existing worktree path for this branch
                # Porcelain format: "worktree /path\nHEAD abc\nbranch refs/heads/..."
                lines = existing.splitlines()
                for i, line in enumerate(lines):
                    if f"refs/heads/{pr_branch}" in line:
                        # Walk backwards to find the "worktree" line
                        for j in range(i - 1, -1, -1):
                            if lines[j].startswith("worktree "):
                                wt = Path(lines[j].removeprefix("worktree "))
                                break
                        print(f"  Using existing worktree: {wt}")
                        break
            else:
                print(f"  Creating worktree from PR branch: {pr_branch}")
                wt.mkdir(parents=True, exist_ok=True)
                wt.rmdir()
                subprocess.run(
                    ["git", "worktree", "add", str(wt), pr_branch],
                    cwd=repo, check=True,
                )
                subprocess.run(["uv", "sync", "-q"], cwd=wt, check=False)
        else:
            print(f"ERROR: Worktree {wt} not found and could not determine PR branch.")
            sys.exit(1)

    prompt = write_prompt("bart", task, wt, repo,
                          pr=args.pr, preexisting=args.preexisting or "none")
    script = write_launch_script("bart", task, wt, prompt, runner=runner)

    pane = args.pane or find_free_pane()
    if not pane:
        panes = ensure_agent_panes(num_panes=2)
        pane = panes[0]
        print(f"  Provisioned agent panes in current session: {len(panes)} panes")

    dispatch_to_pane(pane, script)
    cfg = AGENT_CONFIG["bart"][runner]
    if runner == "kiro":
        print(f"\n  Log: {cfg['logfile'].format(id=args.task_id.lower())}")
    else:
        print(f"\n  Monitor JSONL: {cfg['jsonl'].format(id=args.task_id.lower())}")
    print(f"  Verdict will be written to: /tmp/bart-verdict-{args.task_id.lower()}.md")


def cmd_status(args, repo: Path) -> None:
    state = load_state(repo)
    todo = find_todo_md(repo)
    items = list_todo_items(todo)

    print(f"\n{'ID':<8} {'TODO Status':<14} {'Dispatch State':<16} Description")
    print("─" * 90)
    for item in items:
        if item["status"].startswith("✅"):
            continue
        dispatch_status = state.get(item["id"], {}).get("status", "—")
        desc = item['description'][:50]
        print(f"{item['id']:<8} {item['status']:<14} {dispatch_status:<16} {desc}")


def cmd_list(args, repo: Path) -> None:
    todo = find_todo_md(repo)
    items = list_todo_items(todo)
    print(f"\n{'ID':<8} {'Status':<16} Description")
    print("─" * 80)
    for item in items:
        print(f"{item['id']:<8} {item['status']:<16} {item['description'][:60]}")


def cmd_signal(args, repo: Path) -> None:
    new_status = transition(repo, args.task_id, args.signal)
    print(f"{args.task_id}: → {new_status}")


def main():
    parser = argparse.ArgumentParser(
        description="Agent-mux task dispatcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", default=".", help="Repo root (default: .)")
    parser.add_argument("--runner", choices=["claude", "kiro", "gemini"],
                        default=None, help="Agent runner (default: $AGENT_MUX_RUNNER or claude)")
    sub = parser.add_subparsers(dest="command", required=True)

    # ralph
    p_ralph = sub.add_parser("ralph", help="Dispatch Ralph to implement a TODO item")
    p_ralph.add_argument("task_id", help="TODO item ID (e.g. B2, D1)")
    p_ralph.add_argument("--pane", help="Tmux pane target (e.g. terrapyne:2.0)")
    p_ralph.add_argument("--branch-prefix", default=None, help="Branch prefix (default: auto from task type)")
    p_ralph.add_argument(
        "--skip-baseline", action="store_true",
        help="Skip baseline check (for known pre-existing failures)",
    )

    # wave — batch multiple related items into one Ralph session
    p_wave = sub.add_parser(
        "wave",
        help="Dispatch Ralph to implement multiple TODO items in one branch",
    )
    p_wave.add_argument("task_ids", nargs="+", help="TODO item IDs to group (e.g. D2 D3 D4)")
    p_wave.add_argument("--pane", help="Tmux pane target")
    p_wave.add_argument("--branch-prefix", default=None, help="Branch prefix (default: auto from task type)")
    p_wave.add_argument("--skip-baseline", action="store_true", help="Skip baseline check")

    # bart
    p_bart = sub.add_parser("bart", help="Dispatch Bart to review a PR")
    p_bart.add_argument("task_id", help="TODO item ID")
    p_bart.add_argument("--pr", type=int, required=True, help="PR number to review")
    p_bart.add_argument("--pane", help="Tmux pane target")
    p_bart.add_argument("--preexisting", help="Pre-existing failures to ignore")
    p_bart.add_argument("--worktree", help="Override worktree path (for non-standard branch names)")

    # pr — open PR for a committed branch
    p_pr = sub.add_parser("pr", help="Rebase branch and open PR (when Ralph forgot to)")
    p_pr.add_argument("task_id", help="TODO item ID")

    # rebase — rebase a branch onto latest main
    p_rebase = sub.add_parser("rebase", help="Rebase task branch onto origin/main")
    p_rebase.add_argument("task_id", help="TODO item ID")

    # triage — read Bart verdict and determine next action
    p_triage = sub.add_parser("triage", help="Read Bart verdict and show next action")
    p_triage.add_argument("task_id", help="TODO item ID")

    # signal
    p_sig = sub.add_parser("signal", help="Manually apply a state transition signal")
    p_sig.add_argument("task_id")
    p_sig.add_argument("signal", choices=["ralph_start", "ralph_done", "ralph_fail",
                                           "bart_approved", "bart_rejected"])

    # status
    sub.add_parser("status", help="Show dispatch state for all TODO items")

    # list
    sub.add_parser("list", help="List TODO items")

    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    dispatch = {
        "ralph": cmd_ralph,
        "wave": cmd_wave,
        "bart": cmd_bart,
        "pr": cmd_pr,
        "rebase": cmd_rebase,
        "triage": cmd_triage,
        "signal": cmd_signal,
        "status": cmd_status,
        "list": cmd_list,
    }
    dispatch[args.command](args, repo)


if __name__ == "__main__":
    main()
