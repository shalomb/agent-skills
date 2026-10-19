"""CLI contract for claim / done / release / brief, run as a subprocess against a temp repo."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
TODO = (
    "# Backlog\n\n## NOW\n"
    "- [ ] Fix crash <!-- [id: fix-crash] [prio: P0] [wsjf: 8/1] -->\n"
    "- [ ] Add export <!-- [id: add-export] [prio: P1] -->\n"
)


class ClaimCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / "TODO.md").write_text(TODO, encoding="utf-8")
        self.env = {**os.environ, "PYTHONPATH": str(SRC), "XDG_RUNTIME_DIR": str(self.repo / ".run")}

    def todo(self, *args: str, owner: str = "pi:A") -> subprocess.CompletedProcess:
        env = {**self.env, "TODO_OWNER": owner}
        return subprocess.run(
            [sys.executable, "-m", "todo_navigator.cli", *args], cwd=self.repo, env=env, capture_output=True, text=True
        )

    def test_claim_without_id_takes_the_next_ready_task_and_prints_its_card(self) -> None:
        r = self.todo("claim")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fix-crash", r.stdout)
        self.assertIn("[wip: pi:A]", (self.repo / "TODO.md").read_text())

    def test_a_second_agent_gets_a_different_task(self) -> None:
        self.todo("claim", owner="pi:A")
        r = self.todo("claim", owner="pi:B")
        self.assertIn("add-export", r.stdout)

    def test_claiming_a_held_task_exits_non_zero(self) -> None:
        self.todo("claim", "fix-crash", owner="pi:A")
        r = self.todo("claim", "fix-crash", owner="pi:B")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pi:A", r.stdout + r.stderr)

    def test_done_ticks_the_task_with_the_commit(self) -> None:
        self.todo("claim", "fix-crash")
        r = self.todo("done", "fix-crash", "--commit", "abc1234")
        self.assertEqual(r.returncode, 0, r.stderr)
        line = (self.repo / "TODO.md").read_text().splitlines()[3]
        self.assertTrue(line.startswith("- [x] Fix crash"))
        self.assertIn("[commit: abc1234]", line)

    def test_brief_json_reports_mine_and_next(self) -> None:
        self.todo("claim", "fix-crash", owner="pi:A")
        b = json.loads(self.todo("brief", "--json", owner="pi:A").stdout)
        self.assertEqual(b["mine"], [{"id": "fix-crash", "title": "Fix crash"}])
        self.assertEqual(b["next"]["id"], "add-export")

    def test_next_does_not_offer_a_task_claimed_by_someone_else(self) -> None:
        self.todo("claim", "fix-crash", owner="pi:A")
        out = self.todo("next", owner="pi:B").stdout
        self.assertIn("Next Actionable Task: Add export", out)

    def test_owner_defaults_to_the_pi_session_when_todo_owner_is_unset(self) -> None:
        env = {k: v for k, v in self.env.items() if k != "TODO_OWNER"}
        env["PI_SESSION_ID"] = "abcdef12-3456-7890"
        subprocess.run(
            [sys.executable, "-m", "todo_navigator.cli", "claim"],
            cwd=self.repo,
            env=env,
            check=True,
            capture_output=True,
        )
        self.assertIn("[wip: pi:abcdef12]", (self.repo / "TODO.md").read_text())


if __name__ == "__main__":
    unittest.main()
