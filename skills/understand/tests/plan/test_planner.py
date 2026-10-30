# pyright: reportMissingImports=false
"""Unit tests for understand_plan discovery planner (Step 4)."""

import pytest

from understand_plan.models import Delegate, DiscoveryPlan, PreScan
from understand_plan.planner import plan_discovery
from understand_runs.runner import Lens


# --- Sizing Tiers --------------------------------------------------------

def test_tier_small_under_1000_files():
    """< 1,000 files: 3 delegates partitioned by aspect (architecture, domain, dataflow)."""
    prescan = PreScan(
        total_files=500,
        code_files=450,
        docs_files=50,
        top_directories=["src", "tests"],
    )
    plan = plan_discovery(prescan, Lens("full"))

    assert plan.tier == "small"
    assert len(plan.delegates) == 3

    aspects = [d.aspect for d in plan.delegates]
    assert aspects == ["architecture", "domain", "dataflow"]
    for d in plan.delegates:
        assert d.area is None
        assert d.capability == "inspect"
        assert d.tool == "bg_delegate"


def test_tier_medium_1000_to_10000_files():
    """1,000 - 10,000 files: aspects x areas, capped at 8 delegates."""
    # 2 areas x 3 aspects = 6 delegates (under cap of 8)
    prescan_2_areas = PreScan(
        total_files=2500,
        code_files=2400,
        docs_files=100,
        top_directories=["api", "web"],
    )
    plan_2 = plan_discovery(prescan_2_areas, Lens("full"))
    assert plan_2.tier == "medium"
    assert len(plan_2.delegates) == 6

    # 4 areas x 3 aspects = 12 combinations -> capped at 8 delegates
    prescan_4_areas = PreScan(
        total_files=5000,
        code_files=4800,
        docs_files=200,
        top_directories=["api", "auth", "billing", "web"],
    )
    plan_4 = plan_discovery(prescan_4_areas, Lens("full"))
    assert plan_4.tier == "medium"
    assert len(plan_4.delegates) == 8

    # All delegates must have an aspect and an area
    for d in plan_4.delegates:
        assert d.aspect in {"architecture", "domain", "dataflow"}
        assert d.area in {"api", "auth", "billing", "web"}
        assert d.capability == "inspect"
        assert d.tool == "bg_delegate"


def test_tier_large_10000_or_more_files():
    """≥ 10,000 files: areas only at depth 2, capped at 12 delegates."""
    # 5 depth-2 areas -> 5 delegates
    prescan_5 = PreScan(
        total_files=12000,
        code_files=11500,
        docs_files=500,
        top_directories=["src"],
        depth2_directories=["src/api", "src/auth", "src/core", "src/models", "src/utils"],
    )
    plan_5 = plan_discovery(prescan_5, Lens("full"))
    assert plan_5.tier == "large"
    assert len(plan_5.delegates) == 5
    for d in plan_5.delegates:
        assert d.aspect is None  # areas only
        assert d.area is not None
        assert d.capability == "inspect"

    # 20 depth-2 areas -> capped at 12 delegates
    many_areas = [f"src/module_{i:02d}" for i in range(20)]
    prescan_20 = PreScan(
        total_files=25000,
        code_files=24000,
        docs_files=1000,
        top_directories=["src"],
        depth2_directories=many_areas,
    )
    plan_20 = plan_discovery(prescan_20, Lens("full"))
    assert plan_20.tier == "large"
    assert len(plan_20.delegates) == 12
    for d in plan_20.delegates:
        assert d.aspect is None
        assert d.area in many_areas
        assert d.capability == "inspect"


# --- Profile Selection ---------------------------------------------------

def test_profile_code():
    """Repository containing source code with no documentation."""
    prescan = PreScan(total_files=50, code_files=50, docs_files=0)
    plan = plan_discovery(prescan, Lens("full"))
    assert plan.profile == "code"


def test_profile_docs():
    """Directory containing markdown/documentation files with no code."""
    prescan = PreScan(total_files=12, code_files=0, docs_files=12)
    plan = plan_discovery(prescan, Lens("full"))
    assert plan.profile == "docs"


def test_profile_mixed():
    """Repository containing both source code and documentation."""
    prescan = PreScan(total_files=100, code_files=80, docs_files=20)
    plan = plan_discovery(prescan, Lens("full"))
    assert plan.profile == "mixed"


# --- Pure Function Architecture ------------------------------------------

def test_planner_is_pure_function():
    """Planner must be deterministic, returning equal plans for equal inputs without side effects."""
    prescan = PreScan(
        total_files=1500,
        code_files=1200,
        docs_files=300,
        top_directories=["api", "core", "frontend"],
    )
    lens = Lens("full")

    plan1 = plan_discovery(prescan, lens)
    plan2 = plan_discovery(prescan, lens)

    assert plan1 == plan2
    assert plan1 is not plan2  # new instance, not mutated shared object


# --- Delegates Read-Only -------------------------------------------------

def test_delegates_must_be_read_only():
    """Delegates must have inspect capability only and use bg_delegate."""
    delegate = Delegate(name="arch", aspect="architecture", area=None)
    assert delegate.capability == "inspect"
    assert delegate.tool == "bg_delegate"

    # Any attempt to grant write/execute capability must be rejected
    with pytest.raises(ValueError, match="inspect"):
        Delegate(name="bad", aspect="architecture", area=None, capability="edit")


# --- Lens Narrowing ------------------------------------------------------

def test_lens_narrowing_focuses_areas():
    """Topic or diff lens narrows areas to the focus set before assigning delegates."""
    prescan = PreScan(
        total_files=3000,
        code_files=2800,
        docs_files=200,
        top_directories=["api", "auth", "billing", "reports", "web"],
    )

    # Focus lens on 'auth'
    topic_lens = Lens("topic", "auth")
    plan = plan_discovery(prescan, topic_lens)

    # Filtered to auth area
    assert plan.areas == ["auth"]
    for d in plan.delegates:
        assert d.area == "auth"
