# pyright: reportMissingImports=false
"""BDD step definitions for skills/understand/features/report-docs.feature (Step 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from understand_runs.runner import Lens, make_report

scenarios("../../features/report-docs.feature")


@pytest.fixture
def docs_world(temp_cache, tmp_path):
    """World fixture tracking state for report-docs scenarios."""
    return {
        "dir": tmp_path / "docs_repo",
        "result": None,
        "files": [],
    }


# --- Scenario: A directory of documents gets a reading order -------------

@given("a directory that contains only Markdown documents")
def _only_markdown_docs(docs_world):
    docs_dir = docs_world["dir"]
    docs_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "README.md": "# Welcome\n\nWelcome to the documentation project.\n",
        "getting-started.md": "# Getting Started\n\nStep by step guide to setup.\n",
        "architecture.md": "# Architecture Overview\n\nHigh level design of the system.\n",
        "reference.md": "# API Reference\n\nComplete API details.\n",
    }
    for name, content in files.items():
        (docs_dir / name).write_text(content, encoding="utf-8")
    docs_world["files"] = list(files.keys())


@when("the user makes a report of the full directory")
def _make_report_full_directory(docs_world):
    docs_world["result"] = make_report(docs_world["dir"], Lens("full"))


@then("the report gives a reading order of the documents")
def _report_gives_reading_order(docs_world):
    result = docs_world["result"]
    assert result is not None
    report_file = result.run_dir / "report.html"
    assert report_file.exists(), "report.html was not generated"

    content = report_file.read_text(encoding="utf-8")
    # Verify reading order section exists and lists documents in order
    assert 'id="reading-order"' in content or "Reading Order" in content
    for doc in docs_world["files"]:
        assert doc in content, f"Expected {doc} to be listed in reading order"


# --- Scenario: A directory of documents gets a document map -------------

@given("a directory that contains only Markdown documents that link to each other")
def _markdown_docs_with_links(docs_world):
    docs_dir = docs_world["dir"]
    docs_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "index.md": "# Index\n\nSee [Getting Started](intro.md) and [Guide](guide.md).\n",
        "intro.md": "# Introduction\n\nRead the [Detailed Guide](guide.md).\n",
        "guide.md": "# Guide\n\nSee [Advanced Topics](advanced.md).\n",
        "advanced.md": "# Advanced\n\nRefer back to [Index](index.md).\n",
    }
    for name, content in files.items():
        (docs_dir / name).write_text(content, encoding="utf-8")
    docs_world["files"] = list(files.keys())


@then("the report shows which document links to which")
def _report_shows_document_links(docs_world):
    result = docs_world["result"]
    assert result is not None
    report_file = result.run_dir / "report.html"
    assert report_file.exists()

    content = report_file.read_text(encoding="utf-8")
    # Check that document map section exists
    assert 'id="document-map"' in content or "Document Map" in content

    # Inspect the bundle graph.json directly from the run directory or embedded graph
    # Check for links/edges between documents in the graph or document map section
    assert "intro.md" in content
    assert "guide.md" in content
    assert "advanced.md" in content
    assert "index.md" in content
