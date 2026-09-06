"""Markdown parser and serialization for TODO.md and task cards."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from todo_navigator.models import Task

SHADOW_BASE = Path.home() / ".cache" / "agent-skills" / "todos"


def get_repo_root() -> Path:
    """Finds the root of the current git repository, or falls back to CWD."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return Path(res.stdout.strip()).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


def get_repo_slug(repo_root: Path) -> str:
    """Derives a safe filesystem directory slug for the repository."""
    raw = str(repo_root.resolve()).strip("/").replace("/", "-").replace("\\", "-").replace(":", "-")
    return re.sub(r"-+", "-", raw) or "default-repo"


def get_shadow_dir(repo_root: Path) -> Path:
    """Returns the persistent shadow directory in user cache."""
    slug = get_repo_slug(repo_root)
    shadow_dir = SHADOW_BASE / slug
    shadow_dir.mkdir(parents=True, exist_ok=True)
    (shadow_dir / "tasks").mkdir(parents=True, exist_ok=True)
    return shadow_dir


def get_active_todo_path(repo_root: Path, force_shadow: bool = False) -> Path:
    """Determines whether to use repo TODO.md or the shadow cache TODO.md."""
    shadow_dir = get_shadow_dir(repo_root)
    shadow_todo = shadow_dir / "TODO.md"
    repo_todo = repo_root / "TODO.md"

    if force_shadow:
        return shadow_todo

    # If repo has TODO.md tracked in git or present, respect it
    if repo_todo.exists():
        return repo_todo

    # Default to shadow TODO.md
    return shadow_todo


def generate_task_id(title: str, existing_ids: Optional[List[str]] = None) -> str:
    """Converts a task title into a clean, concise kebab-case ID (max 5 words, max 40 chars)."""
    clean = re.sub(r"[^\w\s-]", "", title.lower())
    words = [w for w in re.split(r"[\s_]+", clean) if w]
    short_words = words[:5]
    base_id = "-".join(short_words).strip("-")
    if len(base_id) > 40:
        base_id = base_id[:40].rstrip("-")
    base_id = base_id or "task"

    if not existing_ids:
        return base_id

    candidate = base_id
    counter = 2
    while candidate in existing_ids:
        candidate = f"{base_id}-{counter}"
        counter += 1
    return candidate


def parse_todo_line(line: str, current_section: str = "") -> Optional[Task]:
    """Parses a single markdown line into a Task object if it matches task format."""
    stripped = line.strip()
    if not (stripped.startswith("- [ ]") or stripped.startswith("- [x]") or stripped.startswith("- [X]")):
        return None

    m = re.match(r"^-\s*\[([ xX])\]\s*(.*?)(?:\s*<!--(.*?)-->)?$", stripped)
    if not m:
        return None

    completed = m.group(1).lower() == "x"
    title = m.group(2).strip()
    comment = m.group(3) or ""

    task_id = ""
    prio = "P2"
    wsjf_cost = 1.0
    wsjf_size = 1.0
    deps: List[str] = []

    if comment:
        tags = re.findall(r"\[([a-zA-Z0-9_-]+):\s*([^\]]+)\]", comment)
        for key, val in tags:
            k = key.lower().strip()
            v = val.strip()
            if k == "id":
                task_id = v
            elif k in ("prio", "priority"):
                prio = v.upper()
            elif k in ("depends", "deps", "after"):
                deps = [d.strip() for d in v.split(",") if d.strip()]
            elif k == "wsjf":
                parts = v.split("/")
                if len(parts) == 2:
                    try:
                        wsjf_cost = float(parts[0])
                        wsjf_size = float(parts[1])
                    except ValueError:
                        pass

    if not task_id:
        task_id = generate_task_id(title)

    return Task(
        id=task_id,
        title=title,
        completed=completed,
        priority=prio,
        wsjf_cost=wsjf_cost,
        wsjf_size=wsjf_size,
        depends_on=deps,
        section=current_section,
        raw_line=line,
    )


def parse_todo_file(todo_path: Path) -> Tuple[List[str], List[Task], List[str]]:
    """Reads a TODO.md file and splits it into header, tasks, and footer lines, tracking sections."""
    if not todo_path.exists():
        return [], [], []

    content = todo_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    pre_lines: List[str] = []
    tasks: List[Task] = []
    post_lines: List[str] = []
    in_tasks = False
    current_h2 = ""
    current_h3 = ""

    for line in lines:
        stripped = line.strip()
        m_h2 = re.match(r"^##\s+(.*)$", stripped)
        if m_h2:
            current_h2 = m_h2.group(1).strip()
            current_h3 = ""
        else:
            m_h3 = re.match(r"^###\s+(.*)$", stripped)
            if m_h3:
                current_h3 = m_h3.group(1).strip()

        current_section = current_h2 or current_h3
        task = parse_todo_line(line, current_section=current_section)
        if task:
            in_tasks = True
            tasks.append(task)
        elif not in_tasks:
            pre_lines.append(line)
        else:
            post_lines.append(line)

    return pre_lines, tasks, post_lines


def scaffold_task_card(card_path: Path, task_id: str, title: str) -> Path:
    """Scaffolds a new BDD acceptance criteria task card if it doesn't exist."""
    card_path.parent.mkdir(parents=True, exist_ok=True)
    if not card_path.exists():
        content = (
            f"# Task: {title}\n"
            f"**Parent:** [TODO.md](../TODO.md)\n"
            f"**ID:** `{task_id}`\n\n"
            f"## Acceptance Criteria (BDD)\n"
            f"- [ ] **Scenario 1: Initial capability**\n"
            f"  - Given a valid starting state\n"
            f"  - When the action is triggered\n"
            f"  - Then the expected outcome is observed\n\n"
            f"## Target Codebase Artifacts\n\n"
            f"## Notes\n"
        )
        card_path.write_text(content, encoding="utf-8")
    return card_path


def add_task_to_todo(
    repo_root: Path,
    title: str,
    task_id: Optional[str] = None,
    prio: str = "P2",
    depends_on: Optional[List[str]] = None,
    wsjf_cost: float = 1.0,
    wsjf_size: float = 1.0,
    after_id: Optional[str] = None,
    section: Optional[str] = None,
    force_shadow: bool = False,
) -> Tuple[Task, Path]:
    """Adds a task to the active TODO.md and creates its shadow task card."""
    shadow_dir = get_shadow_dir(repo_root)
    todo_path = get_active_todo_path(repo_root, force_shadow=force_shadow)

    content = todo_path.read_text(encoding="utf-8") if todo_path.exists() else ""
    lines = content.splitlines() if content else []

    _, tasks, _ = parse_todo_file(todo_path)
    existing_ids = [t.id for t in tasks]

    final_id = task_id or generate_task_id(title, existing_ids)
    deps = list(depends_on) if depends_on else []
    if after_id and after_id not in deps:
        deps.append(after_id)

    target_section = ""
    new_task_line = Task(
        id=final_id,
        title=title,
        completed=False,
        priority=prio.upper(),
        wsjf_cost=wsjf_cost,
        wsjf_size=wsjf_size,
        depends_on=deps,
    ).to_markdown_line()

    inserted = False
    if section:
        target_kw = section.lower().strip()
        sec_start = -1
        for idx, line in enumerate(lines):
            if line.strip().startswith("##") and target_kw in line.lower():
                sec_start = idx
                target_section = re.sub(r"^#+\s*", "", line.strip())
                break

        if sec_start != -1:
            insert_at = len(lines)
            for idx in range(sec_start + 1, len(lines)):
                if lines[idx].strip().startswith("##"):
                    insert_at = idx
                    while insert_at > sec_start + 1 and not lines[insert_at - 1].strip():
                        insert_at -= 1
                    break
            lines.insert(insert_at, new_task_line)
            inserted = True
        else:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append(f"## {section}")
            lines.append(new_task_line)
            target_section = section
            inserted = True

    if not inserted and after_id:
        for idx, line in enumerate(lines):
            if f"[id: {after_id}]" in line:
                lines.insert(idx + 1, new_task_line)
                inserted = True
                break

    if not inserted:
        if not lines:
            lines = ["# Task Backlog", ""]
        last_task_idx = -1
        for idx, line in enumerate(lines):
            if line.strip().startswith("- [ ]") or line.strip().startswith("- [x]"):
                last_task_idx = idx
        if last_task_idx != -1:
            lines.insert(last_task_idx + 1, new_task_line)
        else:
            lines.append(new_task_line)

    todo_path.parent.mkdir(parents=True, exist_ok=True)
    todo_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    new_task = Task(
        id=final_id,
        title=title,
        completed=False,
        priority=prio.upper(),
        wsjf_cost=wsjf_cost,
        wsjf_size=wsjf_size,
        depends_on=deps,
        section=target_section,
    )

    card_path = shadow_dir / "tasks" / f"{final_id}.md"
    scaffold_task_card(card_path, final_id, title)

    return new_task, card_path
