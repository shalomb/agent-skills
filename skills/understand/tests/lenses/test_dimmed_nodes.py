# pyright: reportMissingImports=false
"""Unit tests verifying dimmed nodes handling in bundle and rendered report."""

from __future__ import annotations

import json
from pathlib import Path

from understand_render.bundle import load_bundle
from understand_render.report import graph_elements, render_report


def test_bundle_and_report_support_dimmed_nodes(tmp_path):
    """Nodes with dimmed=True produce .dim class in Cytoscape elements and HTML."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    sections = bundle_dir / "sections"
    sections.mkdir()
    (sections / "01-overview.md").write_text("# Overview\n\nContent.\n", encoding="utf-8")

    graph = {
        "schema_version": 1,
        "title": "Dimmed Test",
        "nodes": [
            {
                "anchor_id": "billing-retry-py",
                "label": "retry.py",
                "path": "billing/retry.py",
                "kind": "file",
                "dimmed": False,
            },
            {
                "anchor_id": "auth-login-py",
                "label": "login.py",
                "path": "auth/login.py",
                "kind": "file",
                "dimmed": True,
            },
        ],
        "edges": [],
    }
    (bundle_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    bundle = load_bundle(bundle_dir)
    assert len(bundle.nodes) == 2
    assert not bundle.nodes[0].dimmed
    assert bundle.nodes[1].dimmed

    elements = graph_elements(bundle)
    assert len(elements) == 2
    # Node 0 has no classes
    assert "classes" not in elements[0]
    # Node 1 has classes: "dim"
    assert elements[1].get("classes") == "dim"

    html = render_report(
        bundle,
        diagram=lambda src: "",
        rewrite_link=lambda t: t,
        uses_in_page_mermaid=lambda: False,
    )
    # Login is dimmed
    assert f'id="{bundle.nodes[1].anchor_id}" class="dim"' in html
    # Retry is not dimmed
    assert f'id="{bundle.nodes[0].anchor_id}"' in html
    assert f'id="{bundle.nodes[0].anchor_id}" class="dim"' not in html
