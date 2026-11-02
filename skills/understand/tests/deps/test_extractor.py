# pyright: reportMissingImports=false
"""Unit tests for dependency and topology extraction module."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from understand_deps.extractor import (
    DependencyGraph,
    compute_metrics,
    detect_hubs,
    extract_dependencies,
    extract_fallback_dependencies,
    extract_js_ts_dependencies,
    extract_python_dependencies,
    normalize_edges,
    parse_codemap_deps,
    strip_ansi,
)


CODEMAP_OUTPUT_BASIC = """
╭─────────────────────────────╮
│  sample-app - Dependency Flow  │
╰─────────────────────────────╯

Src ════════════════════════════════════════════════════════
  index ───▶ src/utils
  cli ───▶ src/utils
  api ───▶ src/utils
  +1 standalone files

─────────────────────────────────────────────────────────────
HUBS: src/utils (3←)
4 files · 3 functions · 3 deps
"""

CODEMAP_OUTPUT_WITH_ANSI = """
\x1b[38;5;240m╭─────────────────────────────╮\x1b[0m
\x1b[38;5;240m│\x1b[0m  \x1b[1mtest-ts\x1b[0m - Dependency Flow  \x1b[38;5;240m│\x1b[0m
\x1b[38;5;240m╰─────────────────────────────╯\x1b[0m

\x1b[36mSrc\x1b[0m ════════════════════════════════════════════════════════
  \x1b[32muser1\x1b[0m ───▶ \x1b[34msrc/h1\x1b[0m, \x1b[34msrc/h2\x1b[0m
  \x1b[32muser2\x1b[0m ───▶ \x1b[34msrc/h1\x1b[0m, \x1b[34msrc/h2\x1b[0m
  \x1b[32muser3\x1b[0m ───▶ \x1b[34msrc/h1\x1b[0m, \x1b[34msrc/h2\x1b[0m
  +2 standalone files

─────────────────────────────────────────────────────────────
\x1b[1mHUBS:\x1b[0m \x1b[33msrc/h1 (3←)\x1b[0m, \x1b[33msrc/h2 (3←)\x1b[0m
5 files · 2 functions · 6 deps
"""

CODEMAP_OUTPUT_MULTI_SECTION = """
╭──────────────────────────────╮
│  multi-sect - Dependency Flow│
╰──────────────────────────────╯

Lib ════════════════════════════════════════════════════════
  +1 standalone files

Src ════════════════════════════════════════════════════════
  main ───▶ lib/helper
  runner ───▶ lib/helper, src/nested/worker

2 files · 1 functions · 3 deps
"""


class TestCodemapParsing:
    """Tests for parsing `codemap --deps` output."""

    def test_strip_ansi(self):
        colored = "\x1b[32mhello\x1b[0m \x1b[1;34mworld\x1b[0m"
        assert strip_ansi(colored) == "hello world"

    def test_parse_basic_codemap_deps(self):
        files = ["src/index.ts", "src/cli.ts", "src/api.ts", "src/utils.ts"]
        graph = parse_codemap_deps(CODEMAP_OUTPUT_BASIC, files)

        assert isinstance(graph, DependencyGraph)
        assert len(graph.edges) == 3
        assert ("src/index.ts", "src/utils.ts", "imports") in graph.edges
        assert ("src/cli.ts", "src/utils.ts", "imports") in graph.edges
        assert ("src/api.ts", "src/utils.ts", "imports") in graph.edges

        assert graph.hubs == ["src/utils.ts"]
        assert graph.metrics["src/utils.ts"]["in_degree"] == 3
        assert graph.metrics["src/utils.ts"]["out_degree"] == 0
        assert graph.metrics["src/index.ts"]["out_degree"] == 1
        assert graph.metrics["src/index.ts"]["in_degree"] == 0

    def test_parse_codemap_deps_with_ansi_and_multiple_destinations(self):
        files = [
            "src/user1.ts",
            "src/user2.ts",
            "src/user3.ts",
            "src/h1.ts",
            "src/h2.ts",
        ]
        graph = parse_codemap_deps(CODEMAP_OUTPUT_WITH_ANSI, files)

        assert len(graph.edges) == 6
        assert ("src/user1.ts", "src/h1.ts", "imports") in graph.edges
        assert ("src/user1.ts", "src/h2.ts", "imports") in graph.edges
        assert ("src/user2.ts", "src/h1.ts", "imports") in graph.edges
        assert ("src/user3.ts", "src/h2.ts", "imports") in graph.edges

        assert set(graph.hubs) == {"src/h1.ts", "src/h2.ts"}
        assert graph.metrics["src/h1.ts"]["in_degree"] == 3
        assert graph.metrics["src/h2.ts"]["in_degree"] == 3

    def test_parse_codemap_multi_section_and_nested_paths(self):
        files = [
            "lib/helper.ts",
            "src/main.ts",
            "src/runner.ts",
            "src/nested/worker.ts",
        ]
        graph = parse_codemap_deps(CODEMAP_OUTPUT_MULTI_SECTION, files)

        assert ("src/main.ts", "lib/helper.ts", "imports") in graph.edges
        assert ("src/runner.ts", "lib/helper.ts", "imports") in graph.edges
        assert ("src/runner.ts", "src/nested/worker.ts", "imports") in graph.edges


class TestFallbackPythonExtraction:
    """Tests for fallback Python AST import extraction."""

    def test_extract_python_ast_imports(self, tmp_path: Path):
        repo = tmp_path / "py_repo"
        repo.mkdir()
        (repo / "app").mkdir()
        (repo / "app" / "models").mkdir()

        (repo / "app" / "main.py").write_text(
            "import os\n"
            "import sys\n"
            "from .utils import helper\n"
            "from .models.user import User\n"
            "import app.config\n",
            encoding="utf-8",
        )
        (repo / "app" / "utils.py").write_text(
            "from .models import user\n"
            "def helper(): pass\n",
            encoding="utf-8",
        )
        (repo / "app" / "models" / "__init__.py").write_text(
            "from .user import User\n",
            encoding="utf-8",
        )
        (repo / "app" / "models" / "user.py").write_text(
            "class User: pass\n",
            encoding="utf-8",
        )
        (repo / "app" / "config.py").write_text(
            "CONFIG = {'port': 8000}\n",
            encoding="utf-8",
        )
        (repo / "app" / "standalone.py").write_text(
            "# Standalone module with no imports\n",
            encoding="utf-8",
        )
        (repo / "app" / "broken.py").write_text(
            "def broken_syntax( - not valid python\n",
            encoding="utf-8",
        )

        files = [
            "app/main.py",
            "app/utils.py",
            "app/models/__init__.py",
            "app/models/user.py",
            "app/config.py",
            "app/standalone.py",
            "app/broken.py",
        ]

        edges = extract_python_dependencies(repo, files)

        # Standard library imports (os, sys) should NOT be in edges because they are not in files
        assert not any(target in ("os", "sys") for _, target, _ in edges)

        # Check expected intra-repo edges
        assert ("app/main.py", "app/utils.py", "imports") in edges
        assert ("app/main.py", "app/models/user.py", "imports") in edges
        assert ("app/main.py", "app/config.py", "imports") in edges
        assert ("app/models/__init__.py", "app/models/user.py", "imports") in edges

        # Ensure broken syntax file does not crash extraction and has 0 outgoing edges
        assert not any(src == "app/broken.py" for src, _, _ in edges)

    def test_extract_fallback_dependencies_complete(self, tmp_path: Path):
        repo = tmp_path / "py_repo2"
        repo.mkdir()
        (repo / "core.py").write_text("def run(): pass\n", encoding="utf-8")
        (repo / "cli.py").write_text("from .core import run\n", encoding="utf-8")
        (repo / "web.py").write_text("from .core import run\n", encoding="utf-8")
        (repo / "worker.py").write_text("from .core import run\n", encoding="utf-8")

        files = ["core.py", "cli.py", "web.py", "worker.py"]
        graph = extract_fallback_dependencies(repo, files)

        assert isinstance(graph, DependencyGraph)
        assert len(graph.edges) == 3
        assert ("cli.py", "core.py", "imports") in graph.edges
        assert ("web.py", "core.py", "imports") in graph.edges
        assert ("worker.py", "core.py", "imports") in graph.edges

        # core.py is imported by 3 files -> it's a hub!
        assert graph.hubs == ["core.py"]
        assert graph.metrics["core.py"]["in_degree"] == 3
        assert graph.metrics["cli.py"]["out_degree"] == 1


class TestFallbackJsTsExtraction:
    """Tests for fallback JS/TS regex/ast import extraction."""

    def test_extract_js_ts_imports(self, tmp_path: Path):
        repo = tmp_path / "ts_repo"
        (repo / "src" / "components").mkdir(parents=True)

        (repo / "src" / "index.ts").write_text(
            "import { helper } from './utils';\n"
            "import { Button } from './components/Button';\n"
            "import * as react from 'react';\n",
            encoding="utf-8",
        )
        (repo / "src" / "utils.ts").write_text(
            "export const helper = 42;\n",
            encoding="utf-8",
        )
        (repo / "src" / "components" / "Button.tsx").write_text(
            "import { helper } from '../utils';\n"
            "export const Button = () => null;\n",
            encoding="utf-8",
        )

        files = ["src/index.ts", "src/utils.ts", "src/components/Button.tsx"]
        edges = extract_js_ts_dependencies(repo, files)

        # 'react' should be omitted (external library)
        assert not any(t == "react" for _, t, _ in edges)

        assert ("src/index.ts", "src/utils.ts", "imports") in edges
        assert ("src/index.ts", "src/components/Button.tsx", "imports") in edges
        assert ("src/components/Button.tsx", "src/utils.ts", "imports") in edges


class TestHubDetectionAndEdgeNormalization:
    """Tests for hub detection, metrics computation, and edge normalization."""

    def test_compute_metrics_and_detect_hubs(self):
        files = ["a.py", "b.py", "c.py", "hub1.py", "hub2.py"]
        edges = [
            ("a.py", "hub1.py", "imports"),
            ("b.py", "hub1.py", "imports"),
            ("c.py", "hub1.py", "imports"),
            ("a.py", "hub2.py", "imports"),
            ("b.py", "hub2.py", "imports"),
            ("c.py", "hub2.py", "imports"),
            ("hub2.py", "hub1.py", "imports"),
        ]

        metrics = compute_metrics(files, edges)
        assert metrics["hub1.py"]["in_degree"] == 4
        assert metrics["hub1.py"]["out_degree"] == 0
        assert metrics["hub2.py"]["in_degree"] == 3
        assert metrics["hub2.py"]["out_degree"] == 1
        assert metrics["a.py"]["out_degree"] == 2
        assert metrics["a.py"]["in_degree"] == 0

        # Hub detection threshold >= 3
        hubs = detect_hubs(metrics, threshold=3)
        # Should be ordered descending by in-degree (hub1 has 4, hub2 has 3)
        assert hubs == ["hub1.py", "hub2.py"]

    def test_normalize_edges(self):
        files = ["src/app.py", "src/util.py", "src/db.py"]
        raw_edges = [
            ("src/app.py", "src/util.py", "imports"),
            ("src/app.py", "src/util.py", "imports"),  # duplicate
            ("src/app.py", "src/app.py", "imports"),   # self loop
            ("src/app.py", "external_lib", "imports"), # target not in files
            ("external_mod", "src/db.py", "imports"),  # source not in files
            ("app", "util", "depends_on"),             # short names resolvable
        ]

        normalized = normalize_edges(raw_edges, files)
        assert len(normalized) == 2
        assert ("src/app.py", "src/util.py", "imports") in normalized
        assert ("src/app.py", "src/util.py", "depends_on") in normalized


class TestExtractDependenciesStrategy:
    """Tests for the primary extract_dependencies strategy and fallbacks."""

    def test_extract_dependencies_primary_codemap(self, tmp_path: Path):
        files = ["src/index.ts", "src/utils.ts"]
        # Mock subprocess call to codemap returning CODEMAP_OUTPUT_BASIC
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Src ═══════════════════════════════════════\n  index ───▶ src/utils\n"

        with patch("shutil.which", return_value="/bin/codemap"), \
             patch("subprocess.run", return_value=mock_res):
            graph = extract_dependencies(tmp_path, files)
            assert ("src/index.ts", "src/utils.ts", "imports") in graph.edges

    def test_extract_dependencies_fallback_when_codemap_not_installed(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("pass\n", encoding="utf-8")
        files = ["a.py", "b.py"]

        with patch("shutil.which", return_value=None):
            graph = extract_dependencies(tmp_path, files)
            assert ("a.py", "b.py", "imports") in graph.edges

    def test_extract_dependencies_fallback_when_codemap_fails(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("pass\n", encoding="utf-8")
        files = ["a.py", "b.py"]

        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""

        with patch("shutil.which", return_value="/bin/codemap"), \
             patch("subprocess.run", return_value=mock_res):
            graph = extract_dependencies(tmp_path, files)
            assert ("a.py", "b.py", "imports") in graph.edges

    def test_extract_dependencies_never_crashes(self, tmp_path: Path):
        # Empty repo, non-existent files, syntax errors
        graph = extract_dependencies(tmp_path / "does_not_exist", ["nonexistent.py"])
        assert isinstance(graph, DependencyGraph)
        assert graph.edges == []
        assert graph.hubs == []
        assert "nonexistent.py" in graph.metrics

    def test_extract_dependencies_on_source_basic_fixture(self):
        root = Path(__file__).resolve().parents[1] / "fixtures" / "source-basic"
        files = ["src/app.ts", "src/config.ts"]
        graph = extract_dependencies(root, files)
        assert isinstance(graph, DependencyGraph)
        assert ("src/app.ts", "src/config.ts", "imports") in graph.edges
        assert graph.metrics["src/app.ts"]["out_degree"] == 1
        assert graph.metrics["src/config.ts"]["in_degree"] == 1
