"""CLI contract for `todo batch` and `todo add --scope`, run as a subprocess against a temp repo."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
TODO = (
    "# Backlog\n\n## NOW\n"
    "- [ ] Alpha <!-- [id: alpha] [prio: P1] [wsjf: 5/1] [scope: src/a.py,tests/test_shared.py] -->\n"
    "- [ ] Beta <!-- [id: beta] [prio: P1] [wsjf: 4/1] [scope: src/b.py,tests/test_shared.py] -->\n"
    "- [ ] Gamma <!-- [id: gamma] [prio: P2] [wsjf: 1/1] [scope: src/c.py] -->\n"
)


class BatchCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / "TODO.md").write_text(TODO, encoding="utf-8")
        self.env = {
            **os.environ,
            "PYTHONPATH": str(SRC),
            "XDG_RUNTIME_DIR": str(self.repo / ".run"),
            "XDG_CACHE_HOME": str(self.repo / ".cache"),
            "TODO_OWNER": "pi:A",
        }

    def todo(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "todo_navigator.cli", *args],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def test_batch_json_picks_disjoint_tasks_and_explains_the_skip(self) -> None:
        r = self.todo("batch", "--json", "--no-resources")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([t["id"] for t in out["chosen"]], ["alpha", "gamma"])
        self.assertEqual(out["skipped"][0]["id"], "beta")
        self.assertIn("tests/test_shared.py", out["skipped"][0]["reason"])
        self.assertEqual(out["cap"], 3)

    def test_batch_does_not_claim_unless_asked(self) -> None:
        self.todo("batch", "--no-resources")
        self.assertNotIn("wip:", (self.repo / "TODO.md").read_text())

    def test_batch_claim_claims_each_chosen_task_for_its_own_builder(self) -> None:
        self.todo("batch", "--claim", "--no-resources")
        text = (self.repo / "TODO.md").read_text()
        self.assertIn("[wip: pi:A/alpha]", text)
        self.assertIn("[wip: pi:A/gamma]", text)
        self.assertNotIn("pi:A/beta", text)

    def test_max_flag_caps_the_wave(self) -> None:
        out = json.loads(self.todo("batch", "--json", "--no-resources", "--max", "1").stdout)
        self.assertEqual([t["id"] for t in out["chosen"]], ["alpha"])

    def test_resources_can_only_lower_the_cap(self) -> None:
        out = json.loads(self.todo("batch", "--json", "--max", "2").stdout)
        self.assertLessEqual(len(out["chosen"]), 2)
        self.assertLessEqual(out["cap"], 2)
        self.assertIn("resources", out)

    def test_add_scope_writes_the_tag(self) -> None:
        r = self.todo("add", "Delta", "--id", "delta", "--scope", "src/d.py,tests/test_d.py", "--goal", "none")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[scope: src/d.py,tests/test_d.py]", (self.repo / "TODO.md").read_text())


if __name__ == "__main__":
    unittest.main()
