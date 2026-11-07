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
from typing import Dict, List, Optional, Sequence, Tuple

from .claims import _ready
from .models import Task

DEFAULT_MAX = 3
RAM_PER_AGENT_GB = 2.0
LOAD_CEILING = 0.7
MIN_FREE_GB = 1.0  # a pi process alone is ~0.5 GB
OVERLOAD = 2.0  # load1 / nproc at which nothing more should start
MEM_PRESSURE_MAX = 10.0  # /proc/pressure/memory some avg10 (%): stalls mean thrash
SWAP_USED_MAX = 0.8


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


def resource_cap(
    *, nproc: int, avail_gb: float, load1: float, mem_pressure: float = 0.0, swap_used_frac: float = 0.0
) -> int:
    """Max concurrent agents the machine can carry, 0 when it cannot carry even one.

    0 on: under MIN_FREE_GB free, load1 >= OVERLOAD x cores, memory stall pressure, or swap nearly full.
    Otherwise min(3, 1 per 2 GB, half the cores), and 1 when load1 >= 70% of cores.
    """
    if avail_gb < MIN_FREE_GB or load1 >= OVERLOAD * nproc:
        return 0
    if mem_pressure >= MEM_PRESSURE_MAX or swap_used_frac >= SWAP_USED_MAX:
        return 0
    cap = min(DEFAULT_MAX, math.floor(avail_gb / RAM_PER_AGENT_GB), nproc // 2)
    if load1 >= LOAD_CEILING * nproc:
        cap = 1
    return max(1, cap)


def explain_none(*, nproc: int, avail_gb: float, load1: float, mem_pressure: float, swap_used_frac: float) -> str:
    """Why resource_cap gave 0, for humans and orchestrators."""
    why = []
    if avail_gb < MIN_FREE_GB:
        why.append(f"{avail_gb:.1f} GB free (< {MIN_FREE_GB:g})")
    if load1 >= OVERLOAD * nproc:
        why.append(f"load {load1:.1f} on {nproc} cores")
    if mem_pressure >= MEM_PRESSURE_MAX:
        why.append(f"memory stall {mem_pressure:.0f}%")
    if swap_used_frac >= SWAP_USED_MAX:
        why.append(f"swap {swap_used_frac:.0%} used")
    return "insufficient resources: " + ", ".join(why)


def read_resources() -> Dict[str, float]:
    """Machine state: nproc, avail_gb, load1, mem_pressure (PSI some avg10, %), swap_used_frac.

    TODO_RESOURCES="nproc,avail_gb,load1[,mem_pressure,swap_used_frac]" overrides it, for tests and for
    containers whose cgroup limits are tighter than /proc shows.
    """
    forced = os.environ.get("TODO_RESOURCES")
    if forced:
        v = [float(x) for x in forced.split(",")] + [0.0, 0.0]
        return {"nproc": int(v[0]), "avail_gb": v[1], "load1": v[2], "mem_pressure": v[3], "swap_used_frac": v[4]}
    meminfo: Dict[str, int] = {}
    with open("/proc/meminfo", encoding="utf-8") as fh:
        for line in fh:
            key, _, rest = line.partition(":")
            meminfo[key] = int(rest.split()[0])
    swap_total = meminfo.get("SwapTotal", 0)
    swap_used = (swap_total - meminfo.get("SwapFree", 0)) / swap_total if swap_total else 0.0
    pressure = 0.0
    try:  # absent on kernels without PSI
        with open("/proc/pressure/memory", encoding="utf-8") as fh:
            some = fh.readline()
        pressure = float(some.split("avg10=")[1].split()[0])
    except (OSError, IndexError, ValueError):
        pass
    return {
        "nproc": os.cpu_count() or 1,
        "avail_gb": meminfo.get("MemAvailable", 0) / 1024 / 1024,
        "load1": os.getloadavg()[0],
        "mem_pressure": pressure,
        "swap_used_frac": swap_used,
    }


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
