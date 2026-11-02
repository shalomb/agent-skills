"""Unit tests for the report page: sections, graph, glossary, offline script use."""
import json
import re
import shutil
from pathlib import Path

import pytest

from pages import Page
from understand_render.bundle import load_bundle
from understand_render.report import graph_elements, render_report

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "bundle-basic"


@pytest.fixture
def bundle():
    return load_bundle(FIXTURE)


def report(bundle, **kw):
    kw.setdefault("diagram", lambda src: f"<figure class='diagram'>[{len(src)}]</figure>")
    kw.setdefault("rewrite_link", lambda t: t)
    kw.setdefault("uses_in_page_mermaid", lambda: False)
    return render_report(bundle, **kw)


def test_sections_come_in_file_order_and_the_glossary_comes_last(bundle):
    assert Page(report(bundle)).section_ids == ["overview", "graph", "configuration", "glossary"]


def test_glossary_is_last_even_when_the_bundle_has_no_terms(bundle):
    bundle.glossary_contexts = []
    page = Page(report(bundle))
    assert page.section_ids[-1] == "glossary"


def test_every_node_and_section_has_an_html_id_equal_to_its_anchor(bundle):
    ids = Page(report(bundle)).ids
    for anchor in ["src/app.ts", "src/config.ts", "src/config.ts::parseConfig", "overview", "configuration"]:
        assert anchor in ids


def test_no_html_id_is_used_twice(bundle):
    ids = Page(report(bundle)).ids
    assert len(ids) == len(set(ids))


def test_node_entry_links_to_its_source_view_at_its_line(bundle):
    html = report(bundle)
    assert 'href="src/src/config.ts.html#L12"' in html
    assert 'href="src/src/app.ts.html"' in html


def test_section_title_becomes_the_h2_and_the_first_h1_is_not_repeated(bundle):
    html = report(bundle)
    overview = html.split('id="overview"', 1)[1].split("</section>", 1)[0]
    assert overview.count("Overview</h2>") == 1 and "<h1" not in overview


def test_mermaid_fences_in_sections_go_through_the_diagram_hook(bundle):
    assert "<figure class='diagram'>" in report(bundle)


def test_markdown_links_go_through_the_link_rewriter(bundle):
    html = report(bundle, rewrite_link=lambda t: "R:" + t)
    assert 'href="R:src/app.ts#L42"' in html


def test_cytoscape_is_inlined_and_not_loaded_by_address(bundle):
    page = Page(report(bundle))
    assert page.script_srcs == [] and page.link_hrefs == []
    assert "cytoscape" in report(bundle)


def test_in_page_mermaid_is_inlined_only_when_asked(bundle):
    assert "mermaid.initialize" not in report(bundle)
    with_mermaid = report(bundle, uses_in_page_mermaid=lambda: True)
    assert "mermaid.initialize" in with_mermaid and "mermaid.run" in with_mermaid


def test_graph_elements_carry_anchor_ids_and_link_edges_by_anchor(bundle):
    elements = graph_elements(bundle)
    nodes = [e["data"] for e in elements if "source" not in e["data"]]
    edges = [e["data"] for e in elements if "source" in e["data"]]
    assert [n["id"] for n in nodes] == ["src/app.ts", "src/config.ts", "src/config.ts::parseConfig"]
    assert {(e["source"], e["target"]) for e in edges} == {
        ("src/app.ts", "src/config.ts"), ("src/app.ts", "src/config.ts::parseConfig")}
    assert nodes[2]["href"] == "src/src/config.ts.html#L12"


def test_graph_data_is_embedded_as_json_that_cannot_close_the_script(bundle):
    bundle.nodes[0] = type(bundle.nodes[0])(**{**bundle.nodes[0].__dict__, "label": "</script><b>"})
    html = report(bundle)
    match = re.search(r'<script type="application/json" id="graph-data">(.*?)</script>', html, re.S)
    assert match and "</script" not in match.group(1)
    assert json.loads(match.group(1))[0]["data"]["label"] == "</script><b>"


def test_glossary_groups_terms_by_context(bundle):
    glossary = report(bundle).split('id="glossary"', 1)[1]
    assert "runtime" in glossary and "Config" in glossary and "The settings that the server starts with." in glossary


def test_nav_lists_each_section_once(bundle):
    html = report(bundle)
    nav = html.split('<nav', 1)[1].split("</nav>", 1)[0]
    assert re.findall(r'href="#([^"]+)"', nav) == ["overview", "graph", "configuration", "glossary"]


def test_page_inlines_the_material_3_tokens_and_the_theme_switch(bundle):
    html = report(bundle)
    assert "--md-sys-color-primary" in html and "prefers-color-scheme" in html


def test_cited_places_from_anchors_json_get_an_id_and_a_link_to_their_line(bundle):
    html = report(bundle)
    assert 'id="src/app.ts:entry-call"' in html
    assert 'href="src/src/app.ts.html#L42"' in html


def test_empty_graph_still_renders_a_graph_section(bundle):
    bundle.nodes, bundle.edges, bundle.extra_anchors = [], [], {}
    assert "graph" in Page(report(bundle)).section_ids


def test_nav_sidebar_quick_links_without_remote(bundle):
    html = report(bundle)
    assert '<div class="side-quick-links">' in html
    side_nav = html.split('<nav class="side"', 1)[1].split('</nav>', 1)[0]
    assert '<a href="/r/understand/">← All Reports</a>' in side_nav
    assert 'GitHub ↗' not in side_nav
    assert 'GitLab ↗' not in side_nav


def test_nav_sidebar_quick_links_with_remote_github(bundle):
    class FakeRemote:
        web_base = "https://github.com/example-org/my-project"
        host = "github"
    html = report(bundle, remote_info=FakeRemote())
    assert '<a href="/r/understand/">← All Reports</a>' in html
    assert '<a href="https://github.com/example-org/my-project" target="_blank" rel="noopener noreferrer">GitHub ↗</a>' in html


def test_nav_sidebar_quick_links_with_remote_gitlab(bundle):
    class FakeRemote:
        web_base = "https://gitlab.com/example-org/my-project"
        host = "gitlab"
    html = report(bundle, remote_info=FakeRemote())
    assert '<a href="https://gitlab.com/example-org/my-project" target="_blank" rel="noopener noreferrer">GitLab ↗</a>' in html


def test_graph_section_has_node_drawer_and_inspector(bundle):
    html = report(bundle)
    assert '<div id="graph-inspector" class="graph-inspector" hidden></div>' in html
    assert '<details class="node-drawer">' in html
    assert f'<summary>Browse all nodes as text list ({len(bundle.nodes)} items)</summary>' in html
    assert '<ul class="nodes">' in html


def test_c4_synthesized_sections_reading_order():
    from understand_render.bundle import Bundle, Section
    sections = [
        Section("system-context", "01-system-context.md", "System Context: Demo", "content"),
        Section("architecture-and-containers", "02-architecture-and-containers.md", "Architecture & Containers: Demo", "content"),
        Section("key-flows-and-dependencies", "03-key-flows-and-dependencies.md", "Key Flows & Dependencies", "content"),
    ]
    b = Bundle("Demo", nodes=[], edges=[], sections=sections, glossary_contexts=[], extra_anchors={})
    html = render_report(b, diagram=lambda s: s, rewrite_link=lambda t: t, uses_in_page_mermaid=lambda: False)
    page = Page(html)
    assert page.section_ids == [
        "system-context",
        "architecture-and-containers",
        "graph",
        "key-flows-and-dependencies",
        "glossary",
    ]
