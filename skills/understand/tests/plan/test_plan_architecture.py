# pyright: reportMissingImports=false
"""Architecture tests for discovery planner and delegates (Spec Unit 2 & Architecture tests)."""

import pytest

from understand_plan.models import Delegate, DiscoveryPlan, Lens, PreScan
from understand_plan.planner import plan_discovery


def test_rule_planner_is_pure_function_with_tiers():
    """Rule: The planner is a pure function with tiers.

    Check: Unit tests: size tiers, caps (8 and 12), lens narrowing.
    """
    # 1. Size tier: small (< 1k)
    small_prescan = PreScan(total_files=999, code_files=900, top_directories=["src"])
    small_plan = plan_discovery(small_prescan, Lens("full"))
    assert small_plan.tier == "small"
    assert len(small_plan.delegates) == 3

    # 2. Size tier: medium (< 10k) and cap 8
    med_prescan = PreScan(
        total_files=5000,
        code_files=4500,
        top_directories=["d1", "d2", "d3", "d4", "d5"],
    )
    med_plan = plan_discovery(med_prescan, Lens("full"))
    assert med_plan.tier == "medium"
    assert len(med_plan.delegates) == 8  # capped at 8

    # 3. Size tier: large (>= 10k) and cap 12
    large_prescan = PreScan(
        total_files=15000,
        code_files=14000,
        depth2_directories=[f"src/sub_{i:02d}" for i in range(25)],
    )
    large_plan = plan_discovery(large_prescan, Lens("full"))
    assert large_plan.tier == "large"
    assert len(large_plan.delegates) == 12  # capped at 12

    # 4. Lens narrowing
    lens = Lens("topic", "sub_05")
    narrowed_plan = plan_discovery(large_prescan, lens)
    assert narrowed_plan.areas == ["src/sub_05"]
    assert len(narrowed_plan.delegates) == 1
    assert narrowed_plan.delegates[0].area == "src/sub_05"

    # 5. Purity: identical outputs, immutable, deterministic
    repeat_plan = plan_discovery(large_prescan, lens)
    assert repeat_plan == narrowed_plan


def test_rule_delegates_are_read_only():
    """Rule: Delegates are read-only.

    Check: Test: the skill launches delegates only with the inspect capability.
    """
    prescan = PreScan(
        total_files=3500,
        code_files=3000,
        top_directories=["core", "api"],
    )
    plan = plan_discovery(prescan, Lens("full"))

    # Every delegate in the plan MUST have capability="inspect" and tool="bg_delegate"
    assert len(plan.delegates) > 0
    for delegate in plan.delegates:
        assert delegate.capability == "inspect"
        assert delegate.tool == "bg_delegate"

    # Attempting to declare any non-inspect delegate is strictly prohibited
    for forbidden_cap in ("edit", "write", "bash", "execute", "admin"):
        with pytest.raises(ValueError, match="inspect capability only"):
            Delegate(name="unsafe", aspect="architecture", area="src", capability=forbidden_cap)
