"""Visualization tools: ASCII tree, headings list, and Mermaid diagram output."""

from __future__ import annotations

from typing import Dict, List

from todo_navigator.dag import compute_waves
from todo_navigator.models import Task


def format_task_heading(task: Task, show_id: bool = False, show_deps: bool = True) -> str:
    """Formats a single concise task heading line."""
    checkbox = "[x]" if task.completed else "[ ]"
    prio = f"[{task.priority}]"
    if show_id:
        base = f"{checkbox} {prio} [{task.id}] {task.title}"
    else:
        base = f"{checkbox} {prio} {task.title}"
    details = []
    if task.wsjf_score != 1.0:
        details.append(f"WSJF: {task.wsjf_score}")
    if show_deps and task.depends_on:
        details.append(f"after: {','.join(task.depends_on)}")
    if details:
        base += f" ({'; '.join(details)})"
    return base


def render_section_grouped_list(tasks: List[Task], show_id: bool = False) -> str:
    """Renders task headings grouped by their markdown section."""
    if not tasks:
        return "Backlog is empty."

    has_sections = any(bool(t.section) for t in tasks)
    if not has_sections:
        return "\n".join(format_task_heading(t, show_id=show_id) for t in tasks)

    sections: Dict[str, List[Task]] = {}
    for t in tasks:
        sec = t.section or "General"
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(t)

    lines: List[str] = []
    for sec, sec_tasks in sections.items():
        if sec == "General":
            for t in sec_tasks:
                lines.append(format_task_heading(t, show_id=show_id))
        else:
            if lines:
                lines.append("")
            lines.append(f"## {sec}")
            for t in sec_tasks:
                lines.append(f"  {format_task_heading(t, show_id=show_id)}")

    return "\n".join(lines)


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
