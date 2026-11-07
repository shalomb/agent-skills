"""Wave selection: at most N ready tasks whose declared scopes are pairwise disjoint."""

from __future__ import annotations

import unittest

from todo_navigator.batch import resource_cap, select_wave
from todo_navigator.models import Task
from todo_navigator.parser import parse_todo_line


def T(tid, scope="", prio="P2", cost=1.0, deps=(), wip="", done=False):
    return Task(
        id=tid,
        title=tid,
        completed=done,
        priority=prio,
        wsjf_cost=cost,
        depends_on=list(deps),
        scope=scope,
        wip=wip,
    )


def ids(tasks):
    return [t.id for t in tasks]


class ScopeTagTest(unittest.TestCase):
    def test_scope_round_trips_through_the_markdown_line(self):
        t = T("a", scope="src/a.py,tests/test_a.py")
        parsed = parse_todo_line(t.to_markdown_line(), "NOW")
        self.assertEqual(parsed.scope, "src/a.py,tests/test_a.py")


class SelectWaveTest(unittest.TestCase):
    def test_picks_disjoint_scopes_in_wsjf_order(self):
        tasks = [T("a", "src/a.py", cost=1), T("b", "src/b.py", cost=5), T("c", "src/c.py", cost=3)]
        chosen, _ = select_wave(tasks)
        self.assertEqual(ids(chosen), ["b", "c", "a"])

    def test_caps_the_wave_at_max_n(self):
        tasks = [T(x, f"src/{x}.py") for x in "abcd"]
        chosen, skipped = select_wave(tasks, max_n=3)
        self.assertEqual(len(chosen), 3)
        self.assertEqual(ids(skipped), ["d"])

    def test_skips_a_task_whose_test_file_overlaps_a_chosen_one(self):
        tasks = [T("a", "src/a.py,tests/test_shared.py", cost=5), T("b", "src/b.py,tests/test_shared.py", cost=1)]
        chosen, skipped = select_wave(tasks)
        self.assertEqual(ids(chosen), ["a"])
        self.assertIn("tests/test_shared.py", skipped[0].reason)
        self.assertIn("a", skipped[0].reason)

    def test_directory_scope_overlaps_files_beneath_it(self):
        chosen, _ = select_wave([T("a", "src/pkg/", cost=5), T("b", "src/pkg/mod.py")])
        self.assertEqual(ids(chosen), ["a"])

    def test_glob_scope_overlaps_matching_files(self):
        chosen, _ = select_wave([T("a", "src/*.py", cost=5), T("b", "src/x.py")])
        self.assertEqual(ids(chosen), ["a"])

    def test_unscoped_task_runs_alone(self):
        chosen, _ = select_wave([T("a", "", cost=5), T("b", "src/b.py")])
        self.assertEqual(ids(chosen), ["a"])

    def test_scoped_tasks_are_not_admitted_after_an_unscoped_one_even_if_lower_ranked_first(self):
        chosen, skipped = select_wave([T("b", "src/b.py", cost=5), T("a", "", cost=1)])
        self.assertEqual(ids(chosen), ["b"])
        self.assertEqual(ids(skipped), ["a"])

    def test_blocked_and_done_tasks_are_never_chosen(self):
        tasks = [T("a", "x", done=True), T("b", "y", deps=["z"]), T("c", "w")]
        chosen, skipped = select_wave(tasks)
        self.assertEqual(ids(chosen), ["c"])
        self.assertEqual(skipped, [])

    def test_in_flight_claims_hold_their_scope_and_a_slot(self):
        tasks = [T("busy", "src/a.py", wip="agent1"), T("a2", "src/a.py"), T("b", "src/b.py")]
        chosen, _ = select_wave(tasks, max_n=2)
        self.assertEqual(ids(chosen), ["b"])

    def test_in_flight_claims_count_toward_the_cap(self):
        tasks = [T("busy", "src/a.py", wip="agent1"), T("b", "src/b.py"), T("c", "src/c.py")]
        chosen, _ = select_wave(tasks, max_n=2)
        self.assertEqual(ids(chosen), ["b"])


class ResourceCapTest(unittest.TestCase):
    def test_roomy_machine_allows_three(self):
        self.assertEqual(resource_cap(nproc=16, avail_gb=32, load1=1.0), 3)

    def test_ram_limits_to_one_agent_per_two_gb(self):
        self.assertEqual(resource_cap(nproc=16, avail_gb=4.5, load1=1.0), 2)

    def test_cpu_limits_to_half_the_cores(self):
        self.assertEqual(resource_cap(nproc=4, avail_gb=32, load1=0.5), 2)

    def test_high_load_drops_to_one(self):
        self.assertEqual(resource_cap(nproc=8, avail_gb=32, load1=6.0), 1)

    def test_just_enough_headroom_still_allows_one(self):
        self.assertEqual(resource_cap(nproc=1, avail_gb=1.2, load1=0.1), 1)

    def test_under_one_gb_free_means_none(self):
        self.assertEqual(resource_cap(nproc=16, avail_gb=0.5, load1=0.1), 0)

    def test_severe_overload_means_none(self):
        self.assertEqual(resource_cap(nproc=4, avail_gb=32, load1=8.0), 0)

    def test_memory_pressure_means_none(self):
        self.assertEqual(resource_cap(nproc=16, avail_gb=32, load1=0.1, mem_pressure=12.0), 0)

    def test_heavy_swap_use_means_none(self):
        self.assertEqual(resource_cap(nproc=16, avail_gb=32, load1=0.1, swap_used_frac=0.85), 0)

    def test_moderate_swap_use_alone_does_not_block(self):
        self.assertEqual(resource_cap(nproc=16, avail_gb=32, load1=0.1, swap_used_frac=0.4), 3)


if __name__ == "__main__":
    unittest.main()
