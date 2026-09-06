"""Visualization tools: ASCII tree, headings list, and Mermaid diagram output."""

from __future__ import annotations

from typing import Dict, List

from todo_navigator.dag import compute_waves
from todo_navigator.models import Task


def format_task_heading(task: Task, show_deps: bool = True) -> str:
    """Formats a single concise task heading line."""
    checkbox = "[x]" if task.completed else "[ ]"
    prio = f"[{task.priority}]"
    base = f"{checkbox} {prio} [{task.id}] {task.title}"
    details = []
    if task.wsjf_score != 1.0:
        details.append(f"WSJF: {task.wsjf_score}")
    if show_deps and task.depends_on:
        details.append(f"after: {','.join(task.depends_on)}")
    if details:
        base += f" ({'; '.join(details)})"
    return base


def render_ascii_tree(tasks: List[Task]) -> str:
    """Renders the tasks organized by execution waves and dependency tree."""
    if not tasks:
        return "Backlog is empty."

    lines: List[str] = ["Execution Waves (Topological WSJF DAG):", "=" * 60]
    waves = compute_waves(tasks)

    for wave_idx, wave in enumerate(waves):
        wave_label = f"Wave {wave_idx + 1}"
        if wave_idx == 0:
            wave_label += " (Unblocked / In Progress)"
        else:
            wave_label += " (Blocked by prior waves)"

        lines.append(f"\n🌊 {wave_label}")
        for i, t in enumerate(wave):
            is_last = i == len(wave) - 1
            branch = "└── " if is_last else "├── "
            lines.append(f"  {branch}{format_task_heading(t)}")

    completed = [t for t in tasks if t.completed]
    if completed:
        lines.append(f"\n✅ Completed Tasks ({len(completed)}):")
        for i, t in enumerate(completed):
            is_last = i == len(completed) - 1
            branch = "└── " if is_last else "├── "
            lines.append(f"  {branch}{format_task_heading(t, show_deps=False)}")

    lines.append("=" * 60)
    return "\n".join(lines)


def render_mermaid_graph(tasks: List[Task]) -> str:
    """Renders a Mermaid flowchart representing task dependencies."""
    lines: List[str] = ["```mermaid", "graph TD"]

    task_map: Dict[str, Task] = {t.id: t for t in tasks}

    for t in tasks:
        status_label = "Done" if t.completed else "Ready"
        if not t.completed and t.depends_on:
            status_label = "Blocked"

        title_clean = t.title.replace('"', "'")
        node_label = f'"{title_clean}<br/>[{t.priority}] [{status_label}]"'
        lines.append(f"    {t.id}[{node_label}]")

    # Add edges
    for t in tasks:
        for dep_id in t.depends_on:
            if dep_id in task_map:
                lines.append(f"    {dep_id} --> {t.id}")

    # Add styling
    lines.append("    classDef done fill:#2da44e,stroke:#1a7f37,color:#ffffff;")
    lines.append("    classDef blocked fill:#cf222e,stroke:#a40e26,color:#ffffff;")
    lines.append("    classDef ready fill:#0969da,stroke:#0550ae,color:#ffffff;")

    for t in tasks:
        if t.completed:
            lines.append(f"    class {t.id} done;")
        elif t.depends_on:
            lines.append(f"    class {t.id} blocked;")
        else:
            lines.append(f"    class {t.id} ready;")

    lines.append("```")
    return "\n".join(lines)
