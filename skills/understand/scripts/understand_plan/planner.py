# pyright: reportMissingImports=false
"""Pure function discovery planner (Spec Unit 2)."""

from __future__ import annotations

from .models import ASPECTS, Delegate, DiscoveryPlan, Lens, PreScan


def _determine_tier(total_files: int) -> str:
    if total_files < 1000:
        return "small"
    if total_files < 10000:
        return "medium"
    return "large"


def _determine_profile(prescan: PreScan) -> str:
    if prescan.code_files > 0 and prescan.docs_files == 0:
        return "code"
    if prescan.docs_files > 0 and prescan.code_files == 0:
        return "docs"
    if prescan.code_files > 0 and prescan.docs_files > 0:
        return "mixed"
    # Neither detected or 0 files
    return "docs" if prescan.docs_files > 0 or prescan.total_files == 0 else "code"


def _narrow_areas(areas: list[str], lens: Lens) -> list[str]:
    if not lens.target or lens.type not in ("topic", "diff", "pr"):
        return list(areas)

    target_lower = lens.target.lower()

    # Priority 1: direct match (target is substring of area or area is substring of target)
    direct = [a for a in areas if target_lower in a.lower() or a.lower() in target_lower]
    if direct:
        return direct

    # Priority 2: word tokens with length > 2
    terms = [
        t
        for t in target_lower.replace("/", " ").replace("-", " ").replace("_", " ").split()
        if len(t) > 2
    ]
    matched = [a for a in areas if any(term in a.lower() for term in terms)]
    return matched if matched else list(areas)


def plan_discovery(prescan: PreScan, lens: Lens | None = None) -> DiscoveryPlan:
    """Pure function calculating the discovery plan from pre-scan and lens.

    Deterministic, side-effect free.
    """
    effective_lens = lens if lens is not None else Lens("full")
    tier = _determine_tier(prescan.total_files)
    profile = _determine_profile(prescan)

    if tier == "small":
        # < 1,000 files: 3 delegates partitioned by aspect
        delegates = [
            Delegate(name=f"aspect-{aspect}", aspect=aspect, area=None)
            for aspect in ASPECTS
        ]
        areas = list(prescan.top_directories)
    elif tier == "medium":
        # 1,000 - 10,000 files: aspects x areas/subsystems, capped at 8 delegates
        candidate_areas = _narrow_areas(prescan.top_directories, effective_lens)
        if not candidate_areas:
            candidate_areas = ["root"]
        delegates = []
        for area in sorted(candidate_areas):
            for aspect in ASPECTS:
                delegates.append(
                    Delegate(name=f"{area}-{aspect}", aspect=aspect, area=area)
                )
                if len(delegates) == 8:
                    break
            if len(delegates) == 8:
                break
        areas = candidate_areas
    else:
        # >= 10,000 files: areas only at depth 2, capped at 12 delegates
        depth2 = prescan.depth2_directories or prescan.top_directories or ["root"]
        candidate_areas = _narrow_areas(depth2, effective_lens)
        if not candidate_areas:
            candidate_areas = ["root"]
        delegates = []
        for area in sorted(candidate_areas):
            delegates.append(
                Delegate(
                    name=f"area-{area.replace('/', '-')}",
                    aspect=None,
                    area=area,
                )
            )
            if len(delegates) == 12:
                break
        areas = candidate_areas

    return DiscoveryPlan(
        tier=tier,
        profile=profile,
        delegates=delegates,
        areas=areas,
        lens=effective_lens,
    )
