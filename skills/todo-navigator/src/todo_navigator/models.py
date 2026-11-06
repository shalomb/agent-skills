"""Domain models for Todo Navigator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    """Represents an atomic task in the backlog."""

    id: str
    title: str
    completed: bool = False
    priority: str = "P2"
    wsjf_cost: float = 1.0
    wsjf_size: float = 1.0
    depends_on: List[str] = field(default_factory=list)
    section: str = ""
    raw_line: str = ""
    line_no: int = -1
    wip: str = ""
    wip_since: str = ""
    done_at: str = ""
    commit: str = ""
    created: str = ""
    goal: str = ""
    scope: str = ""

    @property
    def wsjf_score(self) -> float:
        """Computes WSJF priority score (Cost of Delay / Job Size)."""
        return round(self.wsjf_cost / max(self.wsjf_size, 0.1), 2)

    def to_markdown_line(self) -> str:
        """Formats the task as a standard Markdown checklist line with metadata comment."""
        checkbox = "[x]" if self.completed else "[ ]"
        tags: List[str] = [f"id: {self.id}", f"prio: {self.priority}"]
        if self.depends_on:
            tags.append(f"depends: {','.join(self.depends_on)}")
        if self.wsjf_cost != 1.0 or self.wsjf_size != 1.0:
            tags.append(f"wsjf: {self.wsjf_cost}/{self.wsjf_size}")
        if self.created:
            tags.append(f"created: {self.created}")
        if self.goal:
            tags.append(f"goal: {self.goal}")
        if self.scope:
            tags.append(f"scope: {self.scope}")
        if self.wip:
            tags.append(f"wip: {self.wip}")
            if self.wip_since:
                tags.append(f"since: {self.wip_since}")
        if self.done_at:
            tags.append(f"done: {self.done_at}")
        if self.commit:
            tags.append(f"commit: {self.commit}")
        tag_str = " ".join(f"[{t}]" for t in tags)
        return f"- {checkbox} {self.title} <!-- {tag_str} -->"
