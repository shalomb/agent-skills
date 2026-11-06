"""Command-line interface for Todo Navigator."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List, Optional

from todo_navigator.batch import DEFAULT_MAX, read_resources, resource_cap, select_wave
from todo_navigator.claims import brief, claim, claim_next, complete, release
from todo_navigator.dag import (
    add_dependency,
    compute_waves,
    detect_cycle,
    find_matching_targets,
    get_all_task_ids,
    remove_dependency,
    replan_todo_file,
)
from todo_navigator.editor import (
    handle_express_edit,
    launch_editor,
    stage_card_as_artifact,
)
from todo_navigator.goals import active_goal_id, current_goal
from todo_navigator.parser import (
    add_task_to_todo,
    get_active_todo_path,
    get_repo_root,
    get_shadow_dir,
    parse_todo_file,
    scaffold_task_card,
)
from todo_navigator.visualizer import (
    format_task_heading,
    render_ascii_tree,
    render_mermaid_graph,
    render_section_grouped_list,
)


def cmd_list(args: argparse.Namespace) -> int:
    """Lists task headings only, optionally filtered by a smart/partial query."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print(f"❌ No active TODO.md found at {todo_file}. Run 'todo add' or '/replan' to start.")
        return 1

    _, tasks, _ = parse_todo_file(todo_file)
    if not tasks:
        print("Backlog is empty.")
        return 0

    query = getattr(args, "query", "")
    show_id = getattr(args, "show_id", False)
    if query:
        query_str = str(query).strip()
        matches = find_matching_targets(repo_root, shadow_dir, query_str, force_shadow=getattr(args, "shadow", False))
        matched_ids = {cid for cid, _ in matches}

        filtered = [
            t
            for t in tasks
            if t.id in matched_ids
            or query_str.lower() in t.title.lower()
            or (t.section and query_str.lower() in t.section.lower())
        ]
        if not filtered:
            print(f"❌ No tasks matching '{query_str}' found.")
            print(f"   Available tasks: {', '.join(t.id for t in tasks)}")
            return 1
        tasks_to_display = filtered
    else:
        tasks_to_display = tasks

    print(render_section_grouped_list(tasks_to_display, show_id=show_id))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Creates a new task in TODO.md and scaffolds its BDD task card."""
    repo_root = get_repo_root()
    force_shadow = getattr(args, "shadow", False)
    title = args.title.strip()
    prio = getattr(args, "prio", "P2") or "P2"
    after_id = getattr(args, "after", None)
    task_id = getattr(args, "id", None)
    section = getattr(args, "section", None)
    goal_arg = getattr(args, "goal", None)
    goal = "" if goal_arg == "none" else goal_arg or active_goal_id(repo_root)

    deps = []
    if getattr(args, "depends", None):
        deps.extend([d.strip() for d in args.depends.split(",") if d.strip()])

    wsjf_cost = 1.0
    wsjf_size = 1.0
    if getattr(args, "wsjf", None):
        parts = args.wsjf.split("/")
        if len(parts) == 2:
            try:
                wsjf_cost = float(parts[0])
                wsjf_size = float(parts[1])
            except ValueError:
                pass

    new_task, card_path = add_task_to_todo(
        repo_root=repo_root,
        title=title,
        task_id=task_id,
        prio=prio,
        depends_on=deps,
        wsjf_cost=wsjf_cost,
        wsjf_size=wsjf_size,
        after_id=after_id,
        section=section,
        force_shadow=force_shadow,
        goal=goal,
        scope=(getattr(args, "scope", None) or "").replace(" ", ""),
    )

    todo_file = get_active_todo_path(repo_root, force_shadow=force_shadow)
    print(f"✅ Added task [{new_task.id}] to [{todo_file.name}](file://{todo_file}):")
    print(f"   {format_task_heading(new_task)}")
    print(f"📄 Scaffolding task card: [{card_path.name}](file://{card_path})")
    return 0


def cmd_dep(args: argparse.Namespace) -> int:
    """Manages task dependencies with cycle detection."""
    repo_root = get_repo_root()
    force_shadow = getattr(args, "shadow", False)
    action = args.action.lower()
    task_id = args.task
    dep_id = args.depends_on

    if action in ("add", "+"):
        success, msg = add_dependency(repo_root, task_id, dep_id, force_shadow=force_shadow)
        if success:
            print(f"✅ {msg}")
            return 0
        else:
            print(f"❌ {msg}")
            return 1
    elif action in ("rm", "remove", "del", "-"):
        success, msg = remove_dependency(repo_root, task_id, dep_id, force_shadow=force_shadow)
        if success:
            print(f"✅ {msg}")
            return 0
        else:
            print(f"❌ {msg}")
            return 1
    else:
        print(f"❌ Unknown dependency action '{action}'. Use 'add' or 'rm'.")
        return 1


def cmd_graph(args: argparse.Namespace) -> int:
    """Visualizes the task dependency graph."""
    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print(f"❌ No active TODO.md found at {todo_file}.")
        return 1

    _, tasks, _ = parse_todo_file(todo_file)
    if getattr(args, "mermaid", False):
        print(render_mermaid_graph(tasks))
    else:
        print(render_ascii_tree(tasks))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Displays backlog metrics, execution waves, and WSJF rankings."""
    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print(f"❌ No active TODO.md found at [{todo_file}](file://{todo_file}).")
        return 1

    _, tasks, _ = parse_todo_file(todo_file)
    completed_ids = {t.id for t in tasks if t.completed}
    unblocked = [t for t in tasks if not t.completed and all(d in completed_ids for d in t.depends_on)]
    blocked = [t for t in tasks if not t.completed and any(d not in completed_ids for d in t.depends_on)]

    total = len(tasks)
    done_count = len(completed_ids)
    pct = int((done_count / total) * 100) if total > 0 else 0

    print("=" * 60)
    print(f"📊 Project Task Status: {todo_file.parent.name}")
    print(f"   Backlog: [{todo_file.name}](file://{todo_file})")
    print(f"   Progress: {done_count}/{total} completed ({pct}%)")
    print(f"   Ready: {len(unblocked)} | Blocked: {len(blocked)} | Done: {done_count}")
    print("=" * 60)

    waves = compute_waves(tasks)
    print(f"\nExecution Waves: {len(waves)} wave(s)")
    for i, wave in enumerate(waves):
        wave_str = ", ".join(f"[{t.id}: {t.priority}]" for t in wave)
        print(f"  🌊 Wave {i + 1}: {wave_str}")

    cycle = detect_cycle(tasks)
    if cycle:
        print(f"\n⚠️ WARNING: Cycle detected: {' -> '.join(cycle)}")

    print("\nNext Actionable Tasks (WSJF Order):")
    for t in sorted(unblocked, key=lambda x: (-x.wsjf_score, x.priority)):
        print(f"  • {format_task_heading(t)}")

    return 0


def cmd_next(args: argparse.Namespace) -> int:
    """Selects the highest-WSJF unblocked task and displays its acceptance card."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print("❌ No active TODO.md found. Run 'todo add' or '/replan' to start.")
        return 1

    _, tasks, _ = parse_todo_file(todo_file)
    completed_ids = {t.id for t in tasks if t.completed}
    unblocked = [t for t in tasks if not t.completed and all(d in completed_ids for d in t.depends_on)]
    me = current_owner()
    unblocked = [t for t in unblocked if not t.wip or t.wip == me]

    if not unblocked:
        if any(not t.completed for t in tasks):
            print("⚠️ All remaining tasks are blocked by pending dependencies or cycles.")
        else:
            print("🎉 All backlog tasks are completed!")
        return 0

    unblocked.sort(key=lambda t: (-t.wsjf_score, t.priority))
    top_task = unblocked[0]

    card_path = shadow_dir / "tasks" / f"{top_task.id}.md"
    if not card_path.exists():
        scaffold_task_card(card_path, top_task.id, top_task.title)

    stage_card_as_artifact(top_task.id, card_path)

    print("=" * 60)
    print(f"🎯 Next Actionable Task: {top_task.title}")
    print(f"   ID: `{top_task.id}` | Priority: {top_task.priority} | WSJF: {top_task.wsjf_score}")
    print(f"   Card: [{card_path.name}](file://{card_path})")
    print("=" * 60)
    print(card_path.read_text(encoding="utf-8"))
    print("=" * 60)
    return 0


def cmd_prev(args: argparse.Namespace) -> int:
    """Produces a concise 3-line factual summary of recent completed work."""
    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    last_task = None
    if todo_file.exists():
        _, tasks, _ = parse_todo_file(todo_file)
        completed = [t for t in tasks if t.completed]
        if completed:
            last_task = completed[-1]

    last_commit_subject = "No recent commits"
    last_commit_hash = ""
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%h %s"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split(" ", 1)
            last_commit_hash = parts[0]
            last_commit_subject = parts[1] if len(parts) > 1 else ""
    except Exception:
        pass

    print("=" * 60)
    print("⏮️ Previous Work Recall:")
    if last_task:
        print(f"1. Task: [{last_task.id}] {last_task.title} (Status: Done)")
    else:
        print("1. Task: No completed tasks found in current backlog.")
    if last_commit_hash:
        print(f"2. Git:  commit {last_commit_hash} - {last_commit_subject}")
    else:
        print("2. Git:  No git commits found.")
    print(f"3. Path: [{todo_file.name}](file://{todo_file})")
    print("=" * 60)
    return 0


def cmd_view(args: argparse.Namespace) -> int:
    """Views one or more task cards matching the query."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    target = args.target

    matches = find_matching_targets(repo_root, shadow_dir, target, force_shadow=getattr(args, "shadow", False))

    if not matches:
        print(f"❌ No task card matching '{target}' found.")
        all_ids = get_all_task_ids(repo_root, shadow_dir, force_shadow=getattr(args, "shadow", False))
        if all_ids:
            print(f"   Available tasks: {', '.join(all_ids)}")
        return 1

    if len(matches) == 1:
        cid, target_path = matches[0]
        print("=" * 70)
        print(f"📄 Viewing: [{target_path.name}](file://{target_path})")
        print("=" * 70)
        if target_path.exists():
            print(target_path.read_text(encoding="utf-8"))
        else:
            print(f"(Task card file does not exist: {target_path})")
        print("=" * 70)
        return 0

    print("=" * 70)
    print(f"📄 Found {len(matches)} task cards matching '{target}': {', '.join(cid for cid, _ in matches)}")
    print("=" * 70)
    for idx, (cid, target_path) in enumerate(matches, 1):
        print(f"\n--- [{idx}/{len(matches)}] {target_path.name} (file://{target_path}) ---")
        if target_path.exists():
            print(target_path.read_text(encoding="utf-8"))
        else:
            print(f"(Task card file does not exist: {target_path})")
    print("=" * 70)
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    """Opens candidate cards in editor or applies express operations."""
    repo_root = get_repo_root()
    shadow_dir = get_shadow_dir(repo_root)
    target = getattr(args, "target", "todo") or "todo"
    extra_ops = getattr(args, "ops", [])

    matches = find_matching_targets(repo_root, shadow_dir, target, force_shadow=getattr(args, "shadow", False))

    if not matches:
        new_card_path = shadow_dir / "tasks" / f"{target}.md"
        scaffold_task_card(new_card_path, target, target)
        matches = [(target, new_card_path)]

    for cid, cpath in matches:
        if not cpath.exists() and cid not in ("todo", "backlog"):
            scaffold_task_card(cpath, cid, cid)

    if extra_ops:
        if len(matches) > 1:
            print(f"ℹ️ Applying express edit to {len(matches)} matches: {', '.join(cid for cid, _ in matches)}")
        ret = 0
        todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))
        for cid, cpath in matches:
            res = handle_express_edit(repo_root, todo_file, shadow_dir, cid, cpath, extra_ops)
            if res != 0:
                ret = res
        return ret

    return launch_editor(repo_root, matches, no_popup=getattr(args, "no_popup", False))


def cmd_replan(args: argparse.Namespace) -> int:
    """Topologically sorts tasks by WSJF and rewrites TODO.md."""
    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))

    if not todo_file.exists():
        print(f"❌ No active TODO.md found at {todo_file}.")
        return 1

    replan_todo_file(todo_file)
    print(f"✅ Re-planned backlog in [{todo_file.name}](file://{todo_file}) by topological WSJF waves.")
    return 0


def current_owner() -> str:
    """Claim owner: $TODO_OWNER, else pi:<PI_SESSION_ID[:8]> inside pi, else user@host:<parent pid>."""
    import os
    import socket

    if os.environ.get("TODO_OWNER"):
        return os.environ["TODO_OWNER"]
    if os.environ.get("PI_SESSION_ID"):
        return f"pi:{os.environ['PI_SESSION_ID'][:8]}"
    return f"{os.environ.get('USER', 'user')}@{socket.gethostname()}:{os.getppid()}"


def _todo_or_fail(args: argparse.Namespace):
    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))
    if not todo_file.exists():
        print(f"❌ No active TODO.md found at {todo_file}.", file=sys.stderr)
        return repo_root, None
    return repo_root, todo_file


def cmd_claim(args: argparse.Namespace) -> int:
    """Claims a task (or the next ready one) for this agent and prints its card."""
    repo_root, todo_file = _todo_or_fail(args)
    if not todo_file:
        return 1
    owner = args.owner or current_owner()
    if args.target:
        ok, msg = claim(todo_file, args.target, owner)
        print(msg)
        if not ok:
            return 1
        task_id = args.target
    else:
        task = claim_next(todo_file, owner)
        if not task:
            print("Nothing ready to claim (all open tasks are blocked or claimed).")
            return 0
        task_id = task.id
        print(f"Claimed '{task_id}' for {owner}.")
    card = get_shadow_dir(repo_root) / "tasks" / f"{task_id}.md"
    if not card.exists():
        _, tasks, _ = parse_todo_file(todo_file)
        title = next((t.title for t in tasks if t.id == task_id), task_id)
        scaffold_task_card(card, task_id, title)
    print(f"Card: {card}")
    print(card.read_text(encoding="utf-8"))
    print(f"When finished: todo done {task_id} --commit HEAD   To give up: todo release {task_id}")
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    _, todo_file = _todo_or_fail(args)
    if not todo_file:
        return 1
    commit = args.commit
    if commit == "HEAD":
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
        commit = r.stdout.strip()
    ok, msg = complete(todo_file, args.target, commit=commit or "")
    print(msg)
    return 0 if ok else 1


def cmd_release(args: argparse.Namespace) -> int:
    _, todo_file = _todo_or_fail(args)
    if not todo_file:
        return 1
    ok, msg = release(todo_file, args.target, args.owner or current_owner(), force=args.force)
    print(msg)
    return 0 if ok else 1


def cmd_batch(args: argparse.Namespace) -> int:
    """Pick the next wave: ready tasks with disjoint scopes, capped by --max and machine resources."""
    import json

    _, todo_file = _todo_or_fail(args)
    if not todo_file:
        return 1
    cap = args.max
    resources = None
    if not args.no_resources:
        nproc, avail_gb, load1 = read_resources()
        resources = {"nproc": nproc, "avail_gb": round(avail_gb, 1), "load1": round(load1, 2)}
        cap = min(cap, resource_cap(nproc=nproc, avail_gb=avail_gb, load1=load1))
    _, tasks, _ = parse_todo_file(todo_file)
    chosen, skipped = select_wave(tasks, max_n=cap)
    owner = args.owner or current_owner()
    if args.claim:
        chosen = [t for t in chosen if claim(todo_file, t.id, f"{owner}/{t.id}")[0]]
    if args.json:
        out = {
            "cap": cap,
            "chosen": [{"id": t.id, "title": t.title, "scope": t.scope} for t in chosen],
            "skipped": [{"id": s.id, "reason": s.reason} for s in skipped],
        }
        if resources:
            out["resources"] = resources
        print(json.dumps(out))
        return 0
    print(f"Wave (cap {cap}): " + (", ".join(t.id for t in chosen) or "nothing ready"))
    for s in skipped:
        print(f"  skipped {s.id}: {s.reason}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    """Backlog summary for agent context injection. Silent (exit 0, no output) when no backlog."""
    import json

    repo_root = get_repo_root()
    todo_file = get_active_todo_path(repo_root, force_shadow=getattr(args, "shadow", False))
    if not todo_file.exists():
        return 0
    b = brief(todo_file, args.owner or current_owner())
    b["goal"] = current_goal(repo_root)
    if args.json:
        print(json.dumps(b))
        return 0
    nxt = f"next ready: {b['next']['id']} ({b['next']['priority']})" if b["next"] else "nothing ready"
    mine = ", ".join(m["id"] for m in b["mine"]) or "none"
    print(f"Backlog {todo_file}: {b['open']} open, {len(b['claimed'])} claimed by others, yours: {mine}; {nxt}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Constructs the unified CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="todo",
        description="Todo Navigator - Shadow task backlog and navigation engine",
    )
    parser.add_argument(
        "--shadow",
        action="store_true",
        help="Force operations against shadow cache directory",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # list
    p_list = subparsers.add_parser("list", help="List task item headings only")
    p_list.add_argument("query", nargs="?", default="", help="Optional search query filter")
    p_list.add_argument("--id", dest="show_id", action="store_true", help="Display task ID slugs")
    p_list.set_defaults(func=cmd_list)

    # add
    p_add = subparsers.add_parser("add", help="Create a new task in backlog")
    p_add.add_argument("title", help="Task title / description")
    p_add.add_argument("--id", dest="id", help="Explicit task ID")
    p_add.add_argument("--prio", choices=["P0", "P1", "P2", "P3"], default="P2", help="Priority level")
    p_add.add_argument("--after", help="Place task after this task ID and depend on it")
    p_add.add_argument("--depends", help="Comma-separated prerequisite task IDs")
    p_add.add_argument("--wsjf", help="WSJF cost/size ratio (e.g. 2.0/1.0)")
    p_add.add_argument("--section", help="Insert task under this markdown section heading")
    p_add.add_argument("--goal", help="Link task to this goal id (default: active goal of the branch; 'none' to skip)")
    p_add.add_argument("--scope", help="Comma-separated paths/globs touched, tests included (for `batch`)")
    p_add.set_defaults(func=cmd_add)

    # dep
    p_dep = subparsers.add_parser("dep", help="Manage task dependencies")
    p_dep.add_argument("action", choices=["add", "rm"], help="Action: add or rm")
    p_dep.add_argument("task", help="Target task ID")
    p_dep.add_argument("depends_on", help="Prerequisite task ID")
    p_dep.set_defaults(func=cmd_dep)

    # graph
    p_graph = subparsers.add_parser("graph", help="Visualize dependency graph")
    p_graph.add_argument("--mermaid", action="store_true", help="Output Mermaid diagram syntax")
    p_graph.set_defaults(func=cmd_graph)

    # status
    p_status = subparsers.add_parser("status", help="Show project task roadmap and status matrix")
    p_status.set_defaults(func=cmd_status)

    # next
    p_next = subparsers.add_parser("next", help="Pulls the next highest-leverage task card")
    p_next.set_defaults(func=cmd_next)

    # prev
    p_prev = subparsers.add_parser("prev", help="Recall recent completed work and git commit")
    p_prev.set_defaults(func=cmd_prev)

    # view
    p_view = subparsers.add_parser("view", help="View a task card")
    p_view.add_argument("target", help="Task ID or partial query")
    p_view.set_defaults(func=cmd_view)

    # edit
    p_edit = subparsers.add_parser("edit", help="Edit a task card or perform express ops")
    p_edit.add_argument("target", nargs="?", default="todo", help="Task ID or partial query (default: todo)")
    p_edit.add_argument("ops", nargs="*", help="Optional express operations (done, P1, add ...)")
    p_edit.add_argument("--no-popup", action="store_true", help="Bypass tmux popup")
    p_edit.set_defaults(func=cmd_edit)

    # replan
    p_replan = subparsers.add_parser("replan", help="Topologically sort backlog by WSJF")
    p_replan.set_defaults(func=cmd_replan)

    # claim / done / release / brief (multi-agent coordination)
    p_claim = subparsers.add_parser("claim", help="Claim a task (default: next ready) for this agent")
    p_claim.add_argument("target", nargs="?", default="", help="Task ID (default: next ready task)")
    p_claim.add_argument("--as", dest="owner", help="Owner (default: $TODO_OWNER or user@host:ppid)")
    p_claim.set_defaults(func=cmd_claim)

    p_done = subparsers.add_parser("done", help="Mark a task done, recording time and commit")
    p_done.add_argument("target", help="Task ID")
    p_done.add_argument("--commit", help="Commit sha (HEAD = current)")
    p_done.set_defaults(func=cmd_done)

    p_release = subparsers.add_parser("release", help="Give up a claim")
    p_release.add_argument("target", help="Task ID")
    p_release.add_argument("--as", dest="owner", help="Owner (default: $TODO_OWNER)")
    p_release.add_argument("--force", action="store_true", help="Release someone else's claim")
    p_release.set_defaults(func=cmd_release)

    p_brief = subparsers.add_parser("brief", help="One-line backlog summary for agent context")
    p_brief.add_argument("--json", action="store_true")
    p_brief.add_argument("--as", dest="owner")
    p_brief.set_defaults(func=cmd_brief)

    p_batch = subparsers.add_parser("batch", help="Pick the next wave: ready tasks with disjoint scopes")
    p_batch.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"Wave size cap (default {DEFAULT_MAX})")
    p_batch.add_argument("--no-resources", action="store_true", help="Ignore RAM/CPU/load limits")
    p_batch.add_argument("--claim", action="store_true", help="Claim each chosen task as <owner>/<id>")
    p_batch.add_argument("--json", action="store_true")
    p_batch.add_argument("--as", dest="owner")
    p_batch.set_defaults(func=cmd_batch)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        return cmd_status(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
