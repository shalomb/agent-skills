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

# Per-agent model and flag defaults (mirrors Springfield's config.toml)
AGENT_CONFIG = {
    "ralph": {
        "model": "sonnet",
        "persona": None,              # No persona appended — ralph is the default claude mode
        "jsonl": "/tmp/claude-ralph-{id}.jsonl",
        "monitor": "~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py",
    },
    "bart": {
        "model": "sonnet",
        "persona": "~/.pi/agents/bart.md",
        "jsonl": "/tmp/claude-bart-{id}.jsonl",
        "monitor": "~/.pi/agent/skills/claude-sub-agent/scripts/monitor.py",
    },
}

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


def extract_task(todo_path: Path, task_id: str) -> dict:
    """Extract task detail section from TODO.md by ID."""
    text = todo_path.read_text()

    # Find one-liner from matrix table
    # Matches: | B1 | [BUG] description | ...
    matrix_pattern = rf"^\|\s*{re.escape(task_id)}\s*\|([^|]+)\|"
    matrix_match = re.search(matrix_pattern, text, re.MULTILINE)
    one_liner = matrix_match.group(1).strip() if matrix_match else task_id

    # Find detail section: ### B1 — ... up to next ### or ---
    detail_pattern = rf"^###\s+{re.escape(task_id)}\b.*?(?=^###\s|\Z)"
    detail_match = re.search(detail_pattern, text, re.MULTILINE | re.DOTALL)
    detail = detail_match.group(0).strip() if detail_match else ""

    if not detail:
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
        m = re.match(
            r"^\|\s*([A-Z][0-9]+|\d+[\w.]*)\s*\|\s*(\[.*?\].*?)\s*\|"
            r".*\|\s*(TODO|✅|🔄.*)\s*\|",
            line,
        )
        if m:
            items.append({
                "id": m.group(1),
                "description": m.group(2).strip(),
                "status": m.group(3).strip(),
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

def ensure_worktree(repo: Path, task_id: str, branch_prefix: str = "fix") -> Path:
    """Create worktree for task if it doesn't exist; return path."""
    slug = task_id.lower().replace(".", "-")
    branch = f"{branch_prefix}/{slug}"
    wt_path = repo / ".worktrees" / slug

    if wt_path.exists():
        return wt_path

    subprocess.run(
        ["git", "worktree", "add", str(wt_path), "-b", branch, "origin/main"],
        cwd=repo, check=True,
    )
    subprocess.run(["uv", "sync", "-q"], cwd=wt_path, check=False)
    return wt_path


# ── Prompt generation ──────────────────────────────────────────────────────────

GUARDRAILS = """\
## Working directory
You are running in {worktree}. Do NOT cd elsewhere for any command.
All git, gh, pytest, and uv commands run from this directory.

## Non-negotiable rules
- Red/Green TDD: write a failing test first, minimal code to pass, then refactor
- One atomic ACP commit: code + tests together, Conventional Commits format
- Use `uv run pytest tests/ --ignore=tests/uat -q --override-ini="addopts="` to run tests
- Use `git -c commit.gpgsign=false commit` if GPG causes issues
- Do NOT fix anything outside the scope of this task
"""

RALPH_TEMPLATE = """\
# Ralph — {id}: {one_liner}

{guardrails}

## Task

{detail}
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
6. If APPROVED: `gh pr merge {pr} --squash --delete-branch`
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


def write_launch_script(agent: str, task: dict, worktree: Path, prompt: Path) -> Path:
    """Generate and write the launch script; return path."""
    cfg = AGENT_CONFIG[agent]
    jsonl = cfg["jsonl"].format(id=task["id"].lower())
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

    script_path = Path(f"/tmp/launch-{agent}-{task['id'].lower()}.sh")
    script_path.write_text(content)
    script_path.chmod(0o755)
    print(f"  Script: {script_path}")
    return script_path


# ── tmux dispatch ──────────────────────────────────────────────────────────────

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
    print(f"\n▶ Ralph: {args.task_id} — {task['one_liner']}")

    wt = ensure_worktree(repo, args.task_id,
                         branch_prefix=args.branch_prefix or "fix")
    print(f"  Worktree: {wt}")

    prompt = write_prompt("ralph", task, wt, repo)
    script = write_launch_script("ralph", task, wt, prompt)

    pane = args.pane or find_free_pane()
    if not pane:
        print("ERROR: No free tmux pane found. Specify --pane.")
        sys.exit(1)

    transition(repo, args.task_id, "ralph_start")
    dispatch_to_pane(pane, script)
    print("\n  State: todo → in_progress")
    print(f"  Monitor JSONL: {AGENT_CONFIG['ralph']['jsonl'].format(id=args.task_id.lower())}")


def cmd_bart(args, repo: Path) -> None:
    todo = find_todo_md(repo)
    task = extract_task(todo, args.task_id)
    print(f"\n▶ Bart: reviewing PR #{args.pr} for {args.task_id} — {task['one_liner']}")

    # Determine worktree (must already exist from Ralph)
    slug = args.task_id.lower().replace(".", "-")
    wt = repo / ".worktrees" / slug
    if not wt.exists():
        print(f"ERROR: Worktree {wt} not found. Run ralph first.")
        sys.exit(1)

    prompt = write_prompt("bart", task, wt, repo,
                          pr=args.pr, preexisting=args.preexisting or "none")
    script = write_launch_script("bart", task, wt, prompt)

    pane = args.pane or find_free_pane()
    if not pane:
        print("ERROR: No free tmux pane found. Specify --pane.")
        sys.exit(1)

    dispatch_to_pane(pane, script)
    print(f"\n  Monitor JSONL: {AGENT_CONFIG['bart']['jsonl'].format(id=args.task_id.lower())}")
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
    sub = parser.add_subparsers(dest="command", required=True)

    # ralph
    p_ralph = sub.add_parser("ralph", help="Dispatch Ralph to implement a TODO item")
    p_ralph.add_argument("task_id", help="TODO item ID (e.g. B2, D1)")
    p_ralph.add_argument("--pane", help="Tmux pane target (e.g. terrapyne:2.0)")
    p_ralph.add_argument("--branch-prefix", default="fix", help="Branch prefix (default: fix)")

    # bart
    p_bart = sub.add_parser("bart", help="Dispatch Bart to review a PR")
    p_bart.add_argument("task_id", help="TODO item ID")
    p_bart.add_argument("--pr", type=int, required=True, help="PR number to review")
    p_bart.add_argument("--pane", help="Tmux pane target")
    p_bart.add_argument("--preexisting", help="Pre-existing failures to ignore")

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
        "bart": cmd_bart,
        "signal": cmd_signal,
        "status": cmd_status,
        "list": cmd_list,
    }
    dispatch[args.command](args, repo)


if __name__ == "__main__":
    main()
