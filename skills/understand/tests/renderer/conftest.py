import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from pages import Page

UNDERSTAND = Path(__file__).resolve().parents[2]
RENDER_SCRIPT = UNDERSTAND / "scripts" / "render.py"
FIXTURES = UNDERSTAND / "tests" / "fixtures"
CHROMIUM = shutil.which("chromium-headless-shell") or "/usr/bin/chromium-headless-shell"


@dataclass
class RenderRun:
    """What a user sees after running the renderer."""
    returncode: int
    stdout: str
    stderr: str
    out_dir: Path


@pytest.fixture
def fixture_bundle(tmp_path):
    """A writable copy of the hand-written fixture bundle."""
    dest = tmp_path / "bundle"
    shutil.copytree(FIXTURES / "bundle-basic", dest)
    return dest


@pytest.fixture
def source_root():
    return FIXTURES / "source-basic"


@pytest.fixture
def fake_mmdc(tmp_path):
    """A stand-in for mmdc that draws every diagram as a one-box SVG."""
    script = tmp_path / "fake-mmdc"
    script.write_text(
        "#!/bin/sh\n"
        "while [ $# -gt 0 ]; do\n"
        '  case "$1" in -o) out="$2"; shift;; esac\n'
        "  shift\n"
        "done\n"
        'printf \'<svg xmlns="http://www.w3.org/2000/svg" data-fake-mmdc="1"><rect width="10" height="10"/></svg>\' > "$out"\n'
    )
    script.chmod(0o755)
    return script


@pytest.fixture
def absent_mmdc(tmp_path):
    return tmp_path / "no-such-mmdc"


@pytest.fixture
def render(tmp_path, source_root, fake_mmdc):
    """Run the renderer as a user would and return the process result."""
    def run(bundle, out=None, mmdc=None, source=None):
        out = out or tmp_path / "out"
        proc = subprocess.run(
            [sys.executable, str(RENDER_SCRIPT), str(bundle), str(out),
             "--source-root", str(source or source_root),
             "--mmdc", str(mmdc or fake_mmdc)],
            capture_output=True, text=True,
        )
        return RenderRun(proc.returncode, proc.stdout, proc.stderr, Path(out))
    return run


def dump_dom(html_path):
    """Open a page in headless chromium with name resolution blocked; return the DOM."""
    proc = subprocess.run(
        [CHROMIUM, "--no-sandbox", "--disable-gpu",
         "--host-resolver-rules=MAP * ~NOTFOUND",
         "--virtual-time-budget=15000", "--dump-dom", Path(html_path).resolve().as_uri()],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


needs_browser = pytest.mark.skipif(not os.path.exists(CHROMIUM), reason="chromium-headless-shell not installed")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
