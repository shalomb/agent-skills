"""goals.current_branch and goals.read_front_matter edge cases."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from todo_navigator.goals import current_branch, read_front_matter

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


class CurrentBranchTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.repo = tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.repo), "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
            check=True,
            env={**os.environ, **GIT_IDENTITY},
        )

    def test_returns_the_branch_name(self) -> None:
        self.assertEqual(current_branch(self.repo), "main")

    def test_a_tag_named_like_the_branch_does_not_change_the_name(self) -> None:
        self.git("commit", "-q", "--allow-empty", "-m", "c")
        self.git("tag", "main")
        self.assertEqual(current_branch(self.repo), "main")

    def test_keeps_slashes_in_the_branch_name(self) -> None:
        self.git("checkout", "-q", "-b", "feat/export")
        self.assertEqual(current_branch(self.repo), "feat/export")

    def test_detached_head_is_none(self) -> None:
        self.git("commit", "-q", "--allow-empty", "-m", "c")
        self.git("checkout", "-q", "--detach")
        self.assertIsNone(current_branch(self.repo))

    def test_missing_git_binary_is_none(self) -> None:
        with mock.patch("todo_navigator.goals.subprocess.run", side_effect=FileNotFoundError("git")):
            self.assertIsNone(current_branch(self.repo))

    def test_oserror_from_git_is_none(self) -> None:
        with mock.patch("todo_navigator.goals.subprocess.run", side_effect=OSError("boom")):
            self.assertIsNone(current_branch(self.repo))


class ReadFrontMatterTest(unittest.TestCase):
    def write(self, text: str, encoding: str = "utf-8") -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = tmp / "goal.md"
        path.write_bytes(text.encode(encoding))
        return path

    def test_reads_top_level_keys(self) -> None:
        path = self.write('---\nid: g-1\nstatus: active  # note\noutcome: "Done"\n---\nbody\n')
        self.assertEqual(read_front_matter(path), {"id": "g-1", "status": "active", "outcome": "Done"})

    def test_a_utf8_bom_does_not_hide_the_front_matter(self) -> None:
        path = self.write("---\nid: g-1\nstatus: active\n---\n", encoding="utf-8-sig")
        self.assertEqual(read_front_matter(path), {"id": "g-1", "status": "active"})

    def test_an_unterminated_block_returns_nothing(self) -> None:
        path = self.write("---\nid: g-1\nstatus: active\n")
        self.assertEqual(read_front_matter(path), {})


if __name__ == "__main__":
    unittest.main()
