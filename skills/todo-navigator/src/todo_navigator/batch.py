"""Wave selection: pick ready tasks whose declared scopes cannot collide.

Deterministic and LLM-free (ADR-003). A task's `scope` is a comma-separated list of
paths, directories (trailing `/`) or globs, and must include its test files.
A task with no scope is assumed to touch everything, so it runs alone.
"""

from __future__ import annotations

import fnmatch
import math
import os
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .claims import _ready
from .models import Task

DEFAULT_MAX = 3
RAM_PER_AGENT_GB = 2.0
LOAD_CEILING = 0.7


@dataclass
class Skipped:
    id: str
    reason: str


def _paths(scope: str) -> List[str]:
    return [p.strip().lstrip("./") for p in scope.split(",") if p.strip()]


def _is_glob(p: str) -> bool:
    return any(c in p for c in "*?[")


def _dir(p: str) -> str:
    return p.rstrip("/") + "/"


def _collide(a: str, b: str) -> bool:
    if _is_glob(a) or _is_glob(b):
        return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)
    if a == b:
        return True
    return (a.endswith("/") and b.startswith(_dir(a))) or (b.endswith("/") and a.startswith(_dir(b)))


def _first_overlap(scope_a: List[str], scope_b: List[str]) -> Optional[str]:
    for a in scope_a:
        for b in scope_b:
            if _collide(a, b):
                return a if a == b else f"{a} ~ {b}"
    return None


def resource_cap(*, nproc: int, avail_gb: float, load1: float) -> int:
    """Max concurrent agents the machine can carry: min(3, 1 per 2 GB, half the cores); 1 if loaded."""
    cap = min(DEFAULT_MAX, math.floor(avail_gb / RAM_PER_AGENT_GB), nproc // 2)
    if load1 >= LOAD_CEILING * nproc:
        cap = 1
    return max(1, cap)


def read_resources() -> Tuple[int, float, float]:
    """(nproc, available GB, 1-minute load average) from the running machine."""
    nproc = os.cpu_count() or 1
    avail_kb = 0
    with open("/proc/meminfo", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("MemAvailable:"):
                avail_kb = int(line.split()[1])
                break
    return nproc, avail_kb / 1024 / 1024, os.getloadavg()[0]


def select_wave(tasks: Sequence[Task], max_n: int = DEFAULT_MAX) -> Tuple[List[Task], List[Skipped]]:
    """Return (chosen, skipped). In-flight claims hold their scope and a slot."""
    in_flight = [t for t in tasks if t.wip and not t.completed]
    taken: List[Tuple[str, List[str]]] = [(t.id, _paths(t.scope)) for t in in_flight]
    slots = max_n - len(in_flight)
    chosen: List[Task] = []
    skipped: List[Skipped] = []
    if any(not s for _, s in taken):
        return chosen, skipped  # an unscoped task is running: nothing else is safe
    for t in (t for t in _ready(list(tasks)) if not t.wip):
        scope = _paths(t.scope)
        if len(chosen) >= slots:
            skipped.append(Skipped(t.id, f"wave full ({max_n})"))
            continue
        if not scope:
            if not chosen and not in_flight:
                chosen.append(t)
                taken.append((t.id, scope))
                break
            skipped.append(Skipped(t.id, "no scope declared: runs alone"))
            continue
        clash = next(((tid, o) for tid, s in taken if (o := _first_overlap(scope, s))), None)
        if clash:
            skipped.append(Skipped(t.id, f"overlaps {clash[0]} on {clash[1]}"))
            continue
        chosen.append(t)
        taken.append((t.id, scope))
    return chosen, skipped
