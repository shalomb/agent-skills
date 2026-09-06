"""Unit tests for lazygit popup launcher."""

from __future__ import annotations

import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from scripts.lazygit_popup import (
    build_tmux_command,
    find_lazygit_binary,
    get_git_context,
    launch_lazygit,
)


class TestLazygitLauncher(unittest.TestCase):
    """Unit tests for lazygit launcher functions."""

    @patch("subprocess.run")
    def test_get_git_context_success(self, mock_run: MagicMock) -> None:
        """Verifies git repo root, name, and branch extraction."""

        def run_side_effect(cmd, **kwargs):
            if "--show-toplevel" in cmd:
                return subprocess.CompletedProcess(
                    cmd, 0, stdout="/workspace/my-repo\n", stderr=""
                )
            if "--abbrev-ref" in cmd:
                return subprocess.CompletedProcess(
                    cmd, 0, stdout="feat/new-ui\n", stderr=""
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect
        ctx = get_git_context(Path("/workspace/my-repo/subfolder"))

        self.assertIsNotNone(ctx)
        assert ctx is not None
        repo_root, repo_name, branch = ctx
        self.assertEqual(repo_root, Path("/workspace/my-repo"))
        self.assertEqual(repo_name, "my-repo")
        self.assertEqual(branch, "feat/new-ui")

    @patch("subprocess.run")
    def test_get_git_context_not_a_repo(self, mock_run: MagicMock) -> None:
        """Returns None if not in a git repository."""
        mock_run.return_value = subprocess.CompletedProcess(
            ["git", "rev-parse", "--show-toplevel"],
            128,
            stdout="",
            stderr="fatal: not a git repository",
        )
        ctx = get_git_context(Path("/tmp/non-repo"))
        self.assertIsNone(ctx)

    @patch("shutil.which")
    def test_find_lazygit_binary_in_path(self, mock_which: MagicMock) -> None:
        """Finds lazygit when available in PATH."""
        mock_which.return_value = "/usr/local/bin/lazygit"
        bin_path = find_lazygit_binary()
        self.assertEqual(bin_path, "/usr/local/bin/lazygit")

    @patch("shutil.which", return_value=None)
    @patch("pathlib.Path.is_file")
    @patch("os.access")
    def test_find_lazygit_binary_fallback(
        self, mock_access: MagicMock, mock_is_file: MagicMock, mock_which: MagicMock
    ) -> None:
        """Finds lazygit in fallback directories when not in standard PATH."""
        mock_is_file.return_value = True
        mock_access.return_value = True

        bin_path = find_lazygit_binary()
        self.assertIsNotNone(bin_path)
        assert bin_path is not None
        self.assertIn("lazygit", bin_path)

    @patch("shutil.which", return_value=None)
    @patch("pathlib.Path.is_file", return_value=False)
    def test_find_lazygit_binary_not_found(
        self, mock_is_file: MagicMock, mock_which: MagicMock
    ) -> None:
        """Returns None when lazygit is completely absent."""
        bin_path = find_lazygit_binary()
        self.assertIsNone(bin_path)

    def test_build_tmux_command(self) -> None:
        """Builds proper tmux display-popup invocation command."""
        repo_root = Path("/workspace/test-repo")
        cmd = build_tmux_command(
            repo_root=repo_root,
            repo_name="test-repo",
            branch="main",
            lazygit_bin="/bin/lazygit",
            extra_args=["status"],
        )
        expected = [
            "tmux",
            "display-popup",
            "-E",
            "-d",
            "/workspace/test-repo",
            "-w",
            "90%",
            "-h",
            "90%",
            "-T",
            " Lazygit: test-repo (main) ",
            "/bin/lazygit",
            "status",
        ]
        self.assertEqual(cmd, expected)

    @patch("scripts.lazygit_popup.get_git_context")
    @patch("scripts.lazygit_popup.find_lazygit_binary")
    @patch("subprocess.run")
    def test_launch_lazygit_in_tmux(
        self, mock_run: MagicMock, mock_find: MagicMock, mock_ctx: MagicMock
    ) -> None:
        """Launches tmux popup when TMUX environment variable is set."""
        mock_ctx.return_value = (Path("/workspace/my-repo"), "my-repo", "main")
        mock_find.return_value = "/bin/lazygit"
        mock_run.return_value = subprocess.CompletedProcess(["tmux"], 0)

        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,123,0"}):
            with patch("sys.stdout", new=io.StringIO()) as out:
                ret = launch_lazygit()
                self.assertEqual(ret, 0)
                self.assertIn("Closed lazygit for [my-repo]", out.getvalue())
                first_call = mock_run.call_args_list[0][0][0]
                self.assertEqual(first_call[0], "tmux")
                self.assertEqual(first_call[1], "display-popup")

    @patch("scripts.lazygit_popup.get_git_context")
    @patch("scripts.lazygit_popup.find_lazygit_binary")
    @patch("sys.stdin.isatty", return_value=False)
    def test_launch_lazygit_headless_without_tmux(
        self, mock_isatty: MagicMock, mock_find: MagicMock, mock_ctx: MagicMock
    ) -> None:
        """Emits graceful warning when run in non-interactive environment without tmux."""
        mock_ctx.return_value = (Path("/workspace/my-repo"), "my-repo", "main")
        mock_find.return_value = "/bin/lazygit"

        env = dict(os.environ)
        env.pop("TMUX", None)
        with patch.dict(os.environ, env, clear=True):
            with patch("sys.stdout", new=io.StringIO()) as out:
                ret = launch_lazygit()
                self.assertEqual(ret, 1)
                self.assertIn(
                    "No active tmux session or interactive TTY", out.getvalue()
                )


if __name__ == "__main__":
    unittest.main()
