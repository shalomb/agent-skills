# pyright: reportMissingImports=false
"""Unit tests for Architectural Synthesizer and sections generation (Spec Unit 3)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from understand_deps.extractor import DependencyGraph  # noqa: E402
from understand_lenses.models import LensFocus  # noqa: E402
from understand_plan.models import Lens  # noqa: E402
from understand_synth.sections import synthesize_sections  # noqa: E402


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Creates a sample multi-subsystem codebase fixture for synthesis tests."""
    repo = tmp_path / "sample_project"
    repo.mkdir()

    # README
    readme = (
        "# Sample Project\n\n"
        "Sample Project is an autonomous workflow orchestrator designed to process data pipelines "
        "and publish architectural intelligence reports.\n\n"
        "It provides high reliability, scalable workers, and offline visual rendering.\n"
    )
    (repo / "README.md").write_text(readme, encoding="utf-8")

    # pyproject.toml
    pyproject = (
        "[project]\n"
        "name = 'sample-project'\n"
        "version = '1.0.0'\n"
        "dependencies = ['fastapi', 'click', 'pydantic']\n"
    )
    (repo / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    # Directory hierarchy and source files
    src_dir = repo / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "app.py").write_text("import click\nfrom .core import process_data\n", encoding="utf-8")
    (src_dir / "core.py").write_text("from .storage import save_record\nfrom .utils import helper\n", encoding="utf-8")
    (src_dir / "storage.py").write_text("import sqlite3\n", encoding="utf-8")
    (src_dir / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")

    # Tests directory
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_dummy(): assert True\n", encoding="utf-8")

    # Scripts directory
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "run.py").write_text("from src.app import main\n", encoding="utf-8")

    return repo


class TestSynthesizeSections:
    """Tests for synthesizing Markdown bundle sections adhering to the Uninformed Reader Test."""

    def test_synthesize_sections_core_files(self, sample_repo: Path):
        folders = ["src", "tests", "scripts"]
        files = [
            "README.md",
            "pyproject.toml",
            "src/__init__.py",
            "src/app.py",
            "src/core.py",
            "src/storage.py",
            "src/utils.py",
            "tests/test_app.py",
            "scripts/run.py",
        ]
        dep_graph = DependencyGraph(
            edges=[
                ("scripts/run.py", "src/app.py", "imports"),
                ("src/app.py", "src/core.py", "imports"),
                ("src/core.py", "src/storage.py", "imports"),
                ("src/core.py", "src/utils.py", "imports"),
                ("tests/test_app.py", "src/app.py", "imports"),
            ],
            hubs=["src/app.py", "src/core.py"],
            metrics={
                "src/app.py": {"in_degree": 2, "out_degree": 1, "in": 2, "out": 1},
                "src/core.py": {"in_degree": 1, "out_degree": 2, "in": 1, "out": 2},
                "src/storage.py": {"in_degree": 1, "out_degree": 0, "in": 1, "out": 0},
                "src/utils.py": {"in_degree": 1, "out_degree": 0, "in": 1, "out": 0},
                "scripts/run.py": {"in_degree": 0, "out_degree": 1, "in": 0, "out": 1},
                "tests/test_app.py": {"in_degree": 0, "out_degree": 1, "in": 0, "out": 1},
            },
        )

        sections = synthesize_sections(sample_repo, "sample_project", folders, files, dep_graph, lens=None)

        assert "01-system-context.md" in sections
        assert "02-architecture-and-containers.md" in sections
        assert "03-key-flows-and-dependencies.md" in sections
        # Full lens does not produce a lens-specific 04 section
        assert "04-topic-focus.md" not in sections

    def test_section_01_system_context(self, sample_repo: Path):
        folders = ["src", "tests"]
        files = ["README.md", "pyproject.toml", "src/app.py", "src/core.py"]
        sections = synthesize_sections(sample_repo, "sample_project", folders, files)
        sec1 = sections["01-system-context.md"]

        # Title & System Intent
        assert "# System Context: sample_project" in sec1
        assert "autonomous workflow orchestrator" in sec1

        # Tech stack
        assert "Python" in sec1
        assert "pyproject.toml" in sec1

        # C4Context diagram
        assert "```mermaid" in sec1
        assert "C4Context" in sec1
        assert "Person(user" in sec1
        assert "System(sample_project" in sec1

        # Entry points
        assert "Primary Entry Points" in sec1
        assert "`src/app.py`" in sec1

    def test_section_02_architecture_and_containers(self, sample_repo: Path):
        folders = ["src", "tests", "scripts"]
        files = ["src/app.py", "src/core.py", "src/storage.py", "scripts/run.py", "tests/test_app.py"]
        sections = synthesize_sections(sample_repo, "sample_project", folders, files)
        sec2 = sections["02-architecture-and-containers.md"]

        # Title & Subsystems
        assert "# Architecture & Containers: sample_project" in sec2
        assert "Major Subsystems" in sec2
        assert "`src/`" in sec2
        assert "`scripts/`" in sec2

        # C4Container diagram
        assert "```mermaid" in sec2
        assert "C4Container" in sec2
        assert "Container_Boundary(" in sec2
        assert "Container(" in sec2
        assert "ContainerDb(" in sec2

        # Uninformed reader test
        assert "Container Breakdown" in sec2 or "Container Decomposition" in sec2

    def test_section_03_key_flows_and_dependencies(self, sample_repo: Path):
        folders = ["src"]
        files = ["src/app.py", "src/core.py", "src/storage.py"]
        dep_graph = DependencyGraph(
            edges=[
                ("src/app.py", "src/core.py", "imports"),
                ("src/core.py", "src/storage.py", "imports"),
            ],
            hubs=["src/core.py"],
            metrics={
                "src/core.py": {"in_degree": 1, "out_degree": 1, "in": 1, "out": 1},
                "src/app.py": {"in_degree": 0, "out_degree": 1, "in": 0, "out": 1},
                "src/storage.py": {"in_degree": 1, "out_degree": 0, "in": 1, "out": 0},
            },
        )
        sections = synthesize_sections(sample_repo, "sample_project", folders, files, dep_graph)
        sec3 = sections["03-key-flows-and-dependencies.md"]

        assert "# Key Flows & Dependencies" in sec3
        assert "Dependency Flow" in sec3
        assert "Hub Analysis" in sec3 or "Hubs" in sec3
        assert "src/core.py" in sec3
        assert "Critical Path" in sec3 or "Callout" in sec3

    def test_topic_lens_synthesizes_focus_section(self, sample_repo: Path):
        folders = ["src"]
        files = ["src/app.py", "src/core.py", "src/storage.py"]
        lens = Lens(type="topic", target="data pipeline")
        sections = synthesize_sections(sample_repo, "sample_project", folders, files, lens=lens)

        assert "04-topic-focus.md" in sections
        focus_sec = sections["04-topic-focus.md"]
        assert "# Topic Focus: data pipeline" in focus_sec
        assert "Seed Nodes" in focus_sec
        assert "1-Hop Neighbours" in focus_sec or "Neighbours" in focus_sec
        assert "Impact Analysis" in focus_sec

    def test_diff_lens_synthesizes_focus_section(self, sample_repo: Path):
        folders = ["src"]
        files = ["src/app.py", "src/core.py", "src/storage.py"]
        lens = LensFocus(
            lens_type="diff",
            focus_set={"src/storage.py"},
            seed_nodes={"src/storage.py"},
            all_files=files,
            metadata={"base_ref": "main"},
        )
        sections = synthesize_sections(sample_repo, "sample_project", folders, files, lens=lens)

        assert "04-diff-focus.md" in sections
        diff_sec = sections["04-diff-focus.md"]
        assert "Diff Focus" in diff_sec
        assert "src/storage.py" in diff_sec
        assert "Impact" in diff_sec

    def test_pr_lens_synthesizes_focus_section(self, sample_repo: Path):
        folders = ["src"]
        files = ["src/app.py", "src/core.py"]
        lens = LensFocus(
            lens_type="pr",
            focus_set={"src/core.py"},
            seed_nodes={"src/core.py"},
            all_files=files,
            metadata={"pr_number": "101", "title": "Refactor core processing"},
        )
        sections = synthesize_sections(sample_repo, "sample_project", folders, files, lens=lens)

        assert "04-pr-focus.md" in sections
        pr_sec = sections["04-pr-focus.md"]
        assert "Pull Request Focus" in pr_sec
        assert "101" in pr_sec
        assert "src/core.py" in pr_sec

    def test_synthesize_sections_fallback_when_no_readme(self, tmp_path: Path):
        bare_repo = tmp_path / "bare_project"
        bare_repo.mkdir()
        folders = ["pkg"]
        files = ["pkg/module.py"]
        (bare_repo / "pkg").mkdir()
        (bare_repo / "pkg" / "module.py").write_text("x = 1\n", encoding="utf-8")

        sections = synthesize_sections(bare_repo, "bare_project", folders, files)
        sec1 = sections["01-system-context.md"]
        assert "# System Context: bare_project" in sec1
        assert "bare_project" in sec1
        assert "C4Context" in sec1

    def test_sections_render_with_markdown_engine(self, sample_repo: Path):
        from understand_render.markdown import render_markdown

        folders = ["src", "tests", "scripts"]
        files = ["README.md", "src/app.py", "scripts/run.py"]
        sections = synthesize_sections(sample_repo, "sample_project", folders, files)

        for name, md in sections.items():
            rendered = render_markdown(md)
            assert "<h1" in rendered
            assert len(rendered) > 100
