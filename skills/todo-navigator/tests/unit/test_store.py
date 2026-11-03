"""Store location: one shadow store per repository, shared by all its worktrees."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from todo_navigator.parser import get_shadow_dir


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


class SharedStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.cache = tmp / "cache"
        self.main = tmp / "main"
        self.linked = tmp / "linked"
        self.main.mkdir()
        _git(self.main, "init", "-q")
        _git(self.main, "commit", "-q", "--allow-empty", "-m", "init")
        _git(self.main, "worktree", "add", "-q", "-b", "side", str(self.linked))
        patcher = mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.cache)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_linked_worktree_and_main_checkout_share_one_store(self) -> None:
        self.assertEqual(get_shadow_dir(self.linked), get_shadow_dir(self.main))

    def test_store_lives_under_xdg_cache_home_read_at_call_time(self) -> None:
        store = get_shadow_dir(self.main)
        self.assertEqual(store.parent, self.cache / "agent-skills" / "todos")
        self.assertTrue((store / "tasks").is_dir())

        other = self.cache.parent / "other-cache"
        with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": str(other)}):
            self.assertEqual(get_shadow_dir(self.main).parent, other / "agent-skills" / "todos")

    def test_store_slug_is_derived_from_main_worktree_path(self) -> None:
        slug = str(self.main).strip("/").replace("/", "-")
        self.assertEqual(get_shadow_dir(self.linked).name, slug)


if __name__ == "__main__":
    unittest.main()
