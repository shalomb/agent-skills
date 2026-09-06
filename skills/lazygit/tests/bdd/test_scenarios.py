"""BDD Scenario tests for lazygit launcher."""

from __future__ import annotations

import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.lazygit_popup import main

_orig_run = subprocess.run


class TestLazygitBDDScenarios(unittest.TestCase):
    """BDD Scenarios testing end-to-end user journeys."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name)
        # Initialize a real git repo with an initial commit
        _orig_run(
            ["git", "init", "-b", "main", str(self.repo_dir)],
            check=True,
            capture_output=True,
        )
        (self.repo_dir / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        _orig_run(
            ["git", "-C", str(self.repo_dir), "add", "."],
            check=True,
            capture_output=True,
        )
        _orig_run(
            [
                "git",
                "-C",
                str(self.repo_dir),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "--no-gpg-sign",
                "-m",
                "initial commit",
            ],
            check=True,
            capture_output=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scenario_user_launches_lazygit_in_tmux_popup(self) -> None:
        """Scenario: User executes /lazygit in a tmux session to review agent work.

        Given an active git repository on branch 'main'
        And the user is running inside a tmux session
        When the user runs '/lazygit'
        Then a blocking tmux popup is spawned targeting the current repo and branch
        And upon exit, a clear status summary is displayed.
        """
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,123,0"}):
            with patch("scripts.lazygit_popup.subprocess.run") as mock_run:
                tmux_calls = []

                def run_side_effect(cmd, **kwargs):
                    if cmd[0] == "tmux":
                        tmux_calls.append(cmd)
                        return subprocess.CompletedProcess(cmd, 0)
                    return _orig_run(cmd, **kwargs)

                mock_run.side_effect = run_side_effect

                with patch("sys.stdout", new=io.StringIO()) as out:
                    ret = main(["--path", str(self.repo_dir)])
                    self.assertEqual(ret, 0)
                    val = out.getvalue()
                    self.assertIn("Closed lazygit for", val)
                    self.assertIn(f"[{self.repo_dir.name}]", val)

                    # Verify tmux display-popup command args
                    self.assertTrue(len(tmux_calls) > 0)
                    cmd_executed = tmux_calls[0]
                    self.assertEqual(cmd_executed[0], "tmux")
                    self.assertEqual(cmd_executed[1], "display-popup")
                    self.assertIn("-E", cmd_executed)
                    self.assertIn("-d", cmd_executed)
                    self.assertIn(str(self.repo_dir), cmd_executed)
                    self.assertIn("-T", cmd_executed)
                    title_idx = cmd_executed.index("-T") + 1
                    self.assertIn(self.repo_dir.name, cmd_executed[title_idx])
                    self.assertIn("main", cmd_executed[title_idx])

    def test_scenario_user_forwards_subcommand_panel(self) -> None:
        """Scenario: User invokes /lg with a specific panel like 'log' or 'status'.

        Given an active git repository
        When the user runs '/lg log'
        Then lazygit is invoked in the popup with argument 'log'.
        """
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,123,0"}):
            with patch("scripts.lazygit_popup.subprocess.run") as mock_run:
                tmux_calls = []

                def run_side_effect(cmd, **kwargs):
                    if cmd[0] == "tmux":
                        tmux_calls.append(cmd)
                        return subprocess.CompletedProcess(cmd, 0)
                    return _orig_run(cmd, **kwargs)

                mock_run.side_effect = run_side_effect

                with patch("sys.stdout", new=io.StringIO()):
                    ret = main(["--path", str(self.repo_dir), "log"])
                    self.assertEqual(ret, 0)
                    self.assertTrue(len(tmux_calls) > 0)
                    cmd_executed = tmux_calls[0]
                    self.assertEqual(cmd_executed[-1], "log")

    def test_scenario_fails_outside_git_repository(self) -> None:
        """Scenario: User attempts to run /lazygit outside a git repository.

        Given an isolated directory that is not a git repository
        When the user runs '/lazygit'
        Then the command exits with an error code and helpful message.
        """
        with tempfile.TemporaryDirectory() as isolated_dir:
            with patch("sys.stdout", new=io.StringIO()) as out:
                ret = main(["--path", isolated_dir])
                self.assertEqual(ret, 1)
                self.assertIn("Not a git repository", out.getvalue())


if __name__ == "__main__":
    unittest.main()
