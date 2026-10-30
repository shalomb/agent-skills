# pyright: reportMissingImports=false
"""Data models for lens focus and discovery (Spec Unit 1 & 2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LensFocus:
    """Represents the focus set and seed nodes computed by a lens."""

    lens_type: str  # "topic" | "pr" | "diff" | "full"
    focus_set: set[str] = field(default_factory=set)
    seed_nodes: set[str] = field(default_factory=set)
    all_files: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
