"""Claiming, releasing and completing tasks safely across concurrent agents."""

from __future__ import annotations

import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from todo_navigator.claims import brief, claim, claim_next, complete, release
from todo_navigator.parser import parse_todo_file

T0 = datetime(2026, 10, 18, 9, 0, tzinfo=timezone.utc)

TODO = (
    "# Backlog\n"
    "\n"
    "## NOW\n"
    "- [ ] Fix crash <!-- [id: fix-crash] [prio: P0] [wsjf: 8/1] -->\n"
    "- [ ] Add export <!-- [id: add-export] [prio: P1] [wsjf: 4/1] -->\n"
    "- [ ] Export docs <!-- [id: export-docs] [prio: P2] [depends: add-export] -->\n"
    "\n"
    "Footer.\n"
)


class ClaimsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.todo = self.dir / "TODO.md"
        self.todo.write_text(TODO, encoding="utf-8")
        self.locks = self.dir / "locks"

    def task(self, task_id: str):
        _, tasks, _ = parse_todo_file(self.todo)
        return next(t for t in tasks if t.id == task_id)

    def test_claim_records_owner_and_time_on_the_task_line(self) -> None:
        ok, _ = claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        self.assertTrue(ok)
        t = self.task("add-export")
        self.assertEqual(t.wip, "pi:A")
        self.assertEqual(t.wip_since, "2026-10-18T09:00Z")

    def test_a_task_claimed_by_another_agent_is_refused(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        ok, msg = claim(self.todo, "add-export", "pi:B", now=T0, lock_dir=self.locks)
        self.assertFalse(ok)
        self.assertIn("pi:A", msg)
        self.assertEqual(self.task("add-export").wip, "pi:A")

    def test_reclaiming_your_own_task_succeeds(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        ok, _ = claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        self.assertTrue(ok)

    def test_a_stale_claim_can_be_taken_over(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        later = T0 + timedelta(hours=5)
        ok, _ = claim(self.todo, "add-export", "pi:B", now=later, lock_dir=self.locks, stale_after=timedelta(hours=4))
        self.assertTrue(ok)
        self.assertEqual(self.task("add-export").wip, "pi:B")

    def test_claim_next_skips_tasks_claimed_by_others_and_blocked_tasks(self) -> None:
        claim(self.todo, "fix-crash", "pi:A", now=T0, lock_dir=self.locks)
        got = claim_next(self.todo, "pi:B", now=T0, lock_dir=self.locks)
        self.assertEqual(got.id, "add-export")
        self.assertEqual(self.task("add-export").wip, "pi:B")

    def test_claim_next_returns_your_existing_claim_first(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        self.assertEqual(claim_next(self.todo, "pi:A", now=T0, lock_dir=self.locks).id, "add-export")

    def test_claim_next_returns_none_when_nothing_is_free(self) -> None:
        claim(self.todo, "fix-crash", "pi:A", now=T0, lock_dir=self.locks)
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        self.assertIsNone(claim_next(self.todo, "pi:B", now=T0, lock_dir=self.locks))

    def test_concurrent_claim_next_never_hands_out_the_same_task_twice(self) -> None:
        results: list = []
        barrier = threading.Barrier(6)

        def worker(n: int) -> None:
            barrier.wait()
            t = claim_next(self.todo, f"pi:{n}", now=T0, lock_dir=self.locks)
            results.append(t.id if t else None)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(6)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        handed = [r for r in results if r]
        self.assertEqual(sorted(handed), ["add-export", "fix-crash"])

    def test_complete_ticks_the_task_clears_the_claim_and_records_time_and_commit(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        ok, _ = complete(self.todo, "add-export", now=T0, commit="abc1234", lock_dir=self.locks)
        self.assertTrue(ok)
        t = self.task("add-export")
        self.assertTrue(t.completed)
        self.assertEqual(t.wip, "")
        self.assertEqual((t.done_at, t.commit), ("2026-10-18T09:00Z", "abc1234"))

    def test_completing_a_task_unblocks_its_dependents(self) -> None:
        complete(self.todo, "fix-crash", now=T0, lock_dir=self.locks)
        complete(self.todo, "add-export", now=T0, lock_dir=self.locks)
        self.assertEqual(claim_next(self.todo, "pi:A", now=T0, lock_dir=self.locks).id, "export-docs")

    def test_release_frees_your_claim_but_not_someone_elses(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        self.assertFalse(release(self.todo, "add-export", "pi:B", lock_dir=self.locks)[0])
        self.assertTrue(release(self.todo, "add-export", "pi:A", lock_dir=self.locks)[0])
        self.assertEqual(self.task("add-export").wip, "")

    def test_edits_leave_headings_prose_and_other_lines_untouched(self) -> None:
        claim(self.todo, "add-export", "pi:A", now=T0, lock_dir=self.locks)
        lines = self.todo.read_text(encoding="utf-8").splitlines()
        original = TODO.splitlines()
        self.assertEqual([ln for i, ln in enumerate(lines) if i != 4], [ln for i, ln in enumerate(original) if i != 4])

    def test_unknown_task_ids_are_reported_not_created(self) -> None:
        ok, msg = claim(self.todo, "nope", "pi:A", now=T0, lock_dir=self.locks)
        self.assertFalse(ok)
        self.assertIn("nope", msg)

    def test_brief_summarises_open_claimed_and_next_for_an_owner(self) -> None:
        claim(self.todo, "fix-crash", "pi:A", now=T0, lock_dir=self.locks)
        b = brief(self.todo, "pi:B")
        self.assertEqual(b["open"], 3)
        self.assertEqual(b["claimed"], [{"id": "fix-crash", "owner": "pi:A", "since": "2026-10-18T09:00Z"}])
        self.assertEqual(b["mine"], [])
        self.assertEqual(b["next"]["id"], "add-export")

    def test_claiming_a_completed_task_is_refused_and_leaves_file_untouched(self) -> None:
        self.assertTrue(complete(self.todo, "fix-crash", now=T0, lock_dir=self.locks)[0])
        before = self.todo.read_text(encoding="utf-8")
        ok, msg = claim(self.todo, "fix-crash", "pi:B", now=T0, lock_dir=self.locks)
        self.assertFalse(ok)
        self.assertIn("already done", msg)
        self.assertEqual(self.todo.read_text(encoding="utf-8"), before)

    def test_claim_accepts_keyword_arguments(self) -> None:
        ok, _ = claim(todo_path=self.todo, task_id="add-export", owner="pi:A", now=T0, lock_dir=self.locks)
        self.assertTrue(ok)

    def test_default_lock_dir_honours_xdg_runtime_dir(self) -> None:
        import importlib
        import os
        from unittest import mock

        import todo_navigator.claims as claims_mod

        try:
            with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(self.dir)}):
                importlib.reload(claims_mod)
                self.assertEqual(claims_mod.DEFAULT_LOCK_DIR, self.dir / "todo-navigator-locks")
        finally:
            importlib.reload(claims_mod)


if __name__ == "__main__":
    unittest.main()
