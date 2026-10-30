# pyright: reportMissingImports=false
"""Data models for discovery planner (Spec Unit 2)."""

from __future__ import annotations

from dataclasses import dataclass, field

ASPECTS = ("architecture", "domain", "dataflow")


@dataclass(frozen=True)
class Lens:
    """Lens specification: full, topic, pr, diff."""

    type: str  # "full" | "topic" | "pr" | "diff"
    target: str | None = None


@dataclass(frozen=True)
class PreScan:
    """Pre-scan statistics derived from directory scan or codemap."""

    total_files: int
    code_files: int = 0
    docs_files: int = 0
    other_files: int = 0
    top_directories: list[str] = field(default_factory=list)
    depth2_directories: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Delegate:
    """Read-only background delegate that discovers one aspect or area."""

    name: str
    aspect: str | None
    area: str | None
    capability: str = "inspect"
    tool: str = "bg_delegate"

    def __post_init__(self):
        if self.capability != "inspect":
            raise ValueError(
                f"Delegates MUST have inspect capability only (read-only), got {self.capability!r}"
            )
        if self.tool != "bg_delegate":
            raise ValueError(
                f"Delegates MUST be launched via bg_delegate, got {self.tool!r}"
            )


@dataclass(frozen=True)
class DiscoveryPlan:
    """Deterministic discovery plan resulting from pre-scan and lens."""

    tier: str  # "small" | "medium" | "large"
    profile: str  # "code" | "docs" | "mixed"
    delegates: list[Delegate]
    areas: list[str]
    lens: Lens
