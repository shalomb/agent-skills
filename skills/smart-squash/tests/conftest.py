"""Shared fixtures: real temporary git repos (never mock what you can use for real)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "smart_squash.py"


def load_module():
    spec = importlib.util.spec_from_file_location("smart_squash", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["smart_squash"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def ss():
    return load_module()


class Repo:
    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test Dev")
        self.git("config", "user.email", "dev@example.com")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "tag.gpgsign", "false")
        self._n = 0

    def git(self, *args, check=True, env=None):
        r = subprocess.run(["git", "-C", str(self.path), *args], capture_output=True, text=True, env=env)
        if check and r.returncode:
            raise AssertionError(f"git {args} failed: {r.stderr}")
        return r.stdout.strip()

    def commit(self, subject, files=None, body="", author=None):
        self._n += 1
        files = files or {f"f{self._n}.txt": f"{self._n}\n"}
        for name, content in files.items():
            p = self.path / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        self.git("add", "-A")
        msg = subject + (f"\n\n{body}" if body else "")
        args = ["commit", "-q", "-m", msg]
        if author:
            args += ["--author", author]
        self.git(*args)
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path / "r")
