"""Dependency graph resolution, WSJF sorting, and cycle detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from todo_navigator.models import Task
from todo_navigator.parser import get_active_todo_path, parse_todo_file


def get_all_task_ids(repo_root: Path, shadow_dir: Path, force_shadow: bool = False) -> List[str]:
    """Collects all known task IDs from TODO.md and task card files."""
    todo_file = get_active_todo_path(repo_root, force_shadow=force_shadow)
    _, tasks, _ = parse_todo_file(todo_file)
    task_ids = {t.id for t in tasks}

    tasks_dir = shadow_dir / "tasks"
    if tasks_dir.exists():
        for p in tasks_dir.glob("*.md"):
            stem = p.stem
            if stem not in ("todo", "backlog"):
                task_ids.add(stem)

    return sorted(task_ids)


def find_matching_targets(
    repo_root: Path, shadow_dir: Path, target: str, force_shadow: bool = False
) -> List[Tuple[str, Path]]:
    """Smart-matches a target query against task cards and TODO.md."""
    query = target.strip()
    if not query or query.lower() in ("todo", "backlog"):
        return [("todo", get_active_todo_path(repo_root, force_shadow=force_shadow))]

    tasks_dir = shadow_dir / "tasks"
    all_cards: Dict[str, Path] = {}
    if tasks_dir.exists():
        for p in tasks_dir.glob("*.md"):
            all_cards[p.stem] = p

    # Also check tasks in active TODO.md
    todo_file = get_active_todo_path(repo_root, force_shadow=force_shadow)
    _, tasks, _ = parse_todo_file(todo_file)
    for t in tasks:
        if t.id not in all_cards:
            all_cards[t.id] = tasks_dir / f"{t.id}.md"

    # 1. Exact match
    clean_target = query[:-3] if query.endswith(".md") else query
    if clean_target in all_cards:
        return [(clean_target, all_cards[clean_target])]

    # 2. Case-insensitive exact match
    lower_target = clean_target.lower()
    for cid, cpath in all_cards.items():
        if cid.lower() == lower_target:
            return [(cid, cpath)]

    # 3. Substring match
    matches: List[Tuple[str, Path]] = []
    for cid, cpath in all_cards.items():
        if lower_target in cid.lower():
            matches.append((cid, cpath))

    # 4. Token-based matching (all query tokens present in candidate ID)
    if not matches:
        tokens = re.split(r"[\s_-]+", lower_target)
        tokens = [tk for tk in tokens if tk]
        if tokens:
            for cid, cpath in all_cards.items():
                cid_lower = cid.lower()
                if all(tk in cid_lower for tk in tokens):
                    matches.append((cid, cpath))

    matches.sort(key=lambda x: (len(x[0]), x[0]))
    return matches


def detect_cycle(tasks: List[Task]) -> Optional[List[str]]:
    """Detects cycles in the task dependency graph using DFS. Returns cycle path if found."""
    graph: Dict[str, List[str]] = {t.id: list(t.depends_on) for t in tasks}

    # 0 = unvisited, 1 = visiting, 2 = visited
    state: Dict[str, int] = {k: 0 for k in graph}
    parent: Dict[str, Optional[str]] = {k: None for k in graph}

    def dfs(node: str) -> Optional[List[str]]:
        state[node] = 1
        for dep in graph.get(node, []):
            if dep not in state:
                continue
            if state[dep] == 1:
                # Cycle found: reconstruct path
                cycle = [dep, node]
                curr = node
                while curr != dep and parent.get(curr) is not None:
                    curr = parent[curr]  # type: ignore
                    cycle.append(curr)
                cycle.reverse()
                return cycle
            elif state[dep] == 0:
                parent[dep] = node
                res = dfs(dep)
                if res:
                    return res
        state[node] = 2
        return None

    for node in graph:
        if state[node] == 0:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def compute_waves(tasks: List[Task]) -> List[List[Task]]:
    """Groups unblocked and dependent tasks into sequential execution waves."""
    completed_ids = {t.id for t in tasks if t.completed}
    remaining = [t for t in tasks if not t.completed]
    waves: List[List[Task]] = []
    satisfied = set(completed_ids)

    while remaining:
        current_wave = [t for t in remaining if all(d in satisfied for d in t.depends_on)]
        if not current_wave:
            # Deadlock / circular dependency among remaining tasks
            current_wave = list(remaining)
            current_wave.sort(key=lambda t: (-t.wsjf_score, t.priority))
            waves.append(current_wave)
            break

        current_wave.sort(key=lambda t: (-t.wsjf_score, t.priority))
        waves.append(current_wave)
        for t in current_wave:
            satisfied.add(t.id)
            remaining.remove(t)

    return waves


def sort_tasks_wsjf(tasks: List[Task]) -> List[Task]:
    """Sorts tasks by dependency waves first, then WSJF score descending."""
    completed = [t for t in tasks if t.completed]
    waves = compute_waves(tasks)
    sorted_uncompleted: List[Task] = []
    for w in waves:
        sorted_uncompleted.extend(w)
    return completed + sorted_uncompleted


def add_dependency(repo_root: Path, task_id: str, dep_id: str, force_shadow: bool = False) -> Tuple[bool, str]:
    """Adds dep_id to task_id's depends_on list in TODO.md, checking for cycles."""
    todo_path = get_active_todo_path(repo_root, force_shadow=force_shadow)
    pre, tasks, post = parse_todo_file(todo_path)

    target_task = next((t for t in tasks if t.id == task_id), None)
    if not target_task:
        return False, f"Task '{task_id}' not found in {todo_path.name}"

    if dep_id == task_id:
        return False, "A task cannot depend on itself."

    if dep_id in target_task.depends_on:
        return True, f"Task '{task_id}' already depends on '{dep_id}'."

    # Test-add dependency
    target_task.depends_on.append(dep_id)
    cycle = detect_cycle(tasks)
    if cycle:
        target_task.depends_on.remove(dep_id)
        return False, f"Cannot add dependency: circular cycle detected ({' -> '.join(cycle)})"

    # Write updated TODO.md
    new_lines = list(pre)
    for t in tasks:
        new_lines.append(t.to_markdown_line())
    new_lines.extend(post)
    todo_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return True, f"Added dependency: '{task_id}' now depends on '{dep_id}'."


def remove_dependency(repo_root: Path, task_id: str, dep_id: str, force_shadow: bool = False) -> Tuple[bool, str]:
    """Removes dep_id from task_id's depends_on list in TODO.md."""
    todo_path = get_active_todo_path(repo_root, force_shadow=force_shadow)
    pre, tasks, post = parse_todo_file(todo_path)

    target_task = next((t for t in tasks if t.id == task_id), None)
    if not target_task:
        return False, f"Task '{task_id}' not found in {todo_path.name}"

    if dep_id not in target_task.depends_on:
        return True, f"Task '{task_id}' does not depend on '{dep_id}'."

    target_task.depends_on.remove(dep_id)
    new_lines = list(pre)
    for t in tasks:
        new_lines.append(t.to_markdown_line())
    new_lines.extend(post)
    todo_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return True, f"Removed dependency: '{task_id}' no longer depends on '{dep_id}'."
