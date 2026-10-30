# pyright: reportMissingImports=false
"""Unit tests for directory scanner and docs profile analysis (Step 4)."""

import json
from pathlib import Path

import pytest

from understand_plan.docs import (
    DocNode,
    analyze_docs_directory,
    extract_markdown_links,
    generate_docs_bundle,
)
from understand_plan.scanner import scan_directory
from understand_render.bundle import load_bundle


def test_scan_directory_pure_docs(tmp_path):
    """A directory of only markdown docs classifies as docs profile."""
    (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")
    sub = tmp_path / "guides"
    sub.mkdir()
    (sub / "start.md").write_text("# Start", encoding="utf-8")

    prescan = scan_directory(tmp_path)
    assert prescan.total_files == 2
    assert prescan.docs_files == 2
    assert prescan.code_files == 0
    assert "guides" in prescan.top_directories


def test_scan_directory_pure_code(tmp_path):
    """A directory of source code classifies as code profile."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("print('hello')", encoding="utf-8")
    (src / "util.ts").write_text("export const x = 1;", encoding="utf-8")

    prescan = scan_directory(tmp_path)
    assert prescan.total_files == 2
    assert prescan.code_files == 2
    assert prescan.docs_files == 0


def test_scan_directory_mixed(tmp_path):
    """A directory with both code and markdown classifies as mixed profile."""
    (tmp_path / "README.md").write_text("# Repo", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main", encoding="utf-8")

    prescan = scan_directory(tmp_path)
    assert prescan.total_files == 2
    assert prescan.code_files == 1
    assert prescan.docs_files == 1


def test_extract_markdown_links():
    """Extracts internal links between markdown files while ignoring externals, anchors, and images."""
    content = """
    # Sample Document
    
    Here is a [Local Link](sub/guide.md).
    Here is a [Link With Anchor](sub/guide.md#section-one).
    Here is an [External Link](https://example.com/page).
    Here is an [In-Page Anchor](#heading).
    Here is an image: ![Diagram](img/arch.png).
    Here is another [Sibling Doc](./other.md).
    """
    links = extract_markdown_links(content, source_file="index.md")
    assert "sub/guide.md" in links
    assert "other.md" in links
    assert "https://example.com/page" not in links
    assert "#heading" not in links
    assert "img/arch.png" not in links


def test_analyze_docs_directory_reading_order_and_links(tmp_path):
    """Analyzes a set of markdown files, determines links and builds sequential reading order."""
    (tmp_path / "README.md").write_text(
        "# Readme\n\nStart at [Guide](guide.md).\n", encoding="utf-8"
    )
    (tmp_path / "guide.md").write_text(
        "# Guide\n\nSee [Advanced](advanced.md).\n", encoding="utf-8"
    )
    (tmp_path / "advanced.md").write_text(
        "# Advanced\n\nRefer back to [Readme](README.md).\n", encoding="utf-8"
    )
    (tmp_path / "faq.md").write_text("# FAQ\n\nFrequently asked questions.\n", encoding="utf-8")

    analysis = analyze_docs_directory(tmp_path)

    # 4 documents found
    assert len(analysis.documents) == 4

    # Links correctly identified
    edges = set(analysis.links)
    assert ("README.md", "guide.md") in edges
    assert ("guide.md", "advanced.md") in edges
    assert ("advanced.md", "README.md") in edges

    # Reading order starts with README and flows through links
    order_paths = [doc.path for doc in analysis.reading_order]
    assert order_paths[0] == "README.md"
    assert order_paths[1] == "guide.md"
    assert order_paths[2] == "advanced.md"
    assert "faq.md" in order_paths


def test_generate_docs_bundle_is_schema_compliant(tmp_path):
    """generate_docs_bundle produces a bundle that passes load_bundle schema validation."""
    docs_dir = tmp_path / "docs_repo"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Home\n\nSee [API](api.md).\n", encoding="utf-8")
    (docs_dir / "api.md").write_text("# API Reference\n\nDetails.\n", encoding="utf-8")

    bundle_dir = tmp_path / "bundle"
    summary = generate_docs_bundle(bundle_dir, docs_dir)

    assert "2 documents" in summary

    # Must be valid per bundle schema
    bundle = load_bundle(bundle_dir)
    assert bundle.title == "Documentation: docs_repo"
    assert len(bundle.nodes) == 2
    assert len(bundle.edges) == 1
    assert bundle.edges[0].source == "index.md"
    assert bundle.edges[0].target == "api.md"

    section_anchors = [s.anchor_id for s in bundle.sections]
    assert "reading-order" in section_anchors
    assert "document-map" in section_anchors
