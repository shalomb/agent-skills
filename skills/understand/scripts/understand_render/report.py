"""The report page: graph, sections in file order, glossary last."""
import html
import json
from pathlib import Path
from urllib.parse import quote

from .anchors import source_view_href
from .icons import icon
from .markdown import render_markdown
from .page import ASSETS, inline_script, page

GRAPH_ID = "graph"
GLOSSARY_ID = "glossary"


def view_href(path, line=None):
    """Address of a source view, with characters made safe for a URL."""
    href = source_view_href(path, line)
    return quote(href, safe="/#:,@+$&=;")


def graph_elements(bundle):
    """Cytoscape elements. Ids are anchor ids, so edges link by anchor, not by position."""
    nodes = []
    for n in bundle.nodes:
        data = {
            "id": n.anchor_id,
            "label": n.label,
            "kind": n.kind,
            "path": n.path,
            "href": view_href(n.path, n.line),
        }
        elem = {"data": data, "classes": "dim"} if n.dimmed else {"data": data}
        nodes.append(elem)
    edges = [
        {"data": {"source": e.source, "target": e.target, "kind": e.kind}}
        for e in bundle.edges]
    return nodes + edges


def render_report(bundle, diagram, rewrite_link, uses_in_page_mermaid):
    """The whole report page as one HTML string.

    `diagram` turns Mermaid source into HTML; `rewrite_link` maps a Markdown link
    target to an address; `uses_in_page_mermaid` is asked last, after all diagrams are made.
    """
    sections = [(GRAPH_ID, "Graph", _graph_section(bundle))]
    for s in bundle.sections:
        sections.append((s.anchor_id, s.title, _markdown_section(s, rewrite_link, diagram)))
    sections.append((GLOSSARY_ID, "Glossary", _glossary_section(bundle)))

    nav = "".join(f'<li><a href="#{html.escape(i)}">{html.escape(t)}</a></li>' for i, t, _ in sections)
    body = "".join(
        f'<section class="report-section" id="{html.escape(i)}"><h2>{html.escape(t)}</h2>{content}</section>'
        for i, t, content in sections)
    title = html.escape(bundle.title)
    document = (
        f'<div class="wrap"><header class="masthead"><p class="eyebrow">{icon("account_tree")} Understand</p>'
        f'<h1>{title}</h1><p>{len(bundle.nodes)} nodes, {len(bundle.edges)} edges</p></header>'
        f'<nav class="side" aria-label="Sections"><h2>Contents</h2><ol>{nav}</ol></nav>'
        f'<article>{body}</article></div>')
    return page(bundle.title, document, _scripts(bundle, uses_in_page_mermaid()))


def _markdown_section(section, rewrite_link, diagram):
    text = _without_first_heading(section.markdown)
    return render_markdown(text, heading_offset=1, rewrite_link=rewrite_link, render_diagram=diagram)


def _without_first_heading(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[:i] + lines[i + 1:])
    return text


def _graph_section(bundle):
    kinds = sorted({n.kind for n in bundle.nodes})
    options = '<option value="">All kinds</option>' + "".join(
        f'<option value="{html.escape(k)}">{html.escape(k)}</option>' for k in kinds)
    items = "".join(_node_item(n) for n in bundle.nodes)
    cited = "".join(
        f'<li id="{html.escape(i)}"><a href="{html.escape(view_href(c.path, c.line))}">'
        f'{html.escape(c.path)}:{c.line}</a> <span class="summary">{html.escape(i)}</span></li>'
        for i, c in bundle.extra_anchors.items())
    cited_block = f'<h3>Cited places</h3><ul class="entries">{cited}</ul>' if cited else ""
    return (
        '<div class="graph-tools">'
        '<input id="graph-search" type="search" placeholder="Search nodes" aria-label="Search nodes">'
        f'<select id="graph-kind" aria-label="Filter by kind">{options}</select></div>'
        '<div id="graph-canvas"></div>'
        f'<ul class="nodes">{items}</ul>{cited_block}')


def _node_item(node):
    summary = f'<span class="summary">{html.escape(node.summary)}</span>' if node.summary else ""
    dim_class = ' class="dim"' if node.dimmed else ""
    return (
        f'<li id="{html.escape(node.anchor_id)}"{dim_class}><span class="kind">{html.escape(node.kind)}</span>'
        f'<a href="{html.escape(view_href(node.path, node.line))}">{html.escape(node.label)}</a>{summary}</li>')


def _glossary_section(bundle):
    if not any(c.terms for c in bundle.glossary_contexts):
        return "<p>This report defines no terms.</p>"
    out = []
    for context in bundle.glossary_contexts:
        terms = "".join(
            f"<dt>{html.escape(t.term)}</dt><dd>{html.escape(t.meaning)}</dd>" for t in context.terms)
        out.append(f"<h3>{html.escape(context.name)}</h3><dl class=\"terms\">{terms}</dl>")
    return "".join(out)


def _scripts(bundle, with_mermaid):
    data = json.dumps(graph_elements(bundle)).replace("<", "\\u003c")
    parts = [
        f'<script type="application/json" id="graph-data">{data}</script>',
        f"<script>{inline_script((ASSETS / 'vendor' / 'cytoscape.min.js').read_text(encoding='utf-8'))}</script>",
        f"<script>{inline_script((ASSETS / 'graph.js').read_text(encoding='utf-8'))}</script>",
    ]
    if with_mermaid:
        mermaid = (ASSETS / "vendor" / "mermaid.min.js").read_text(encoding="utf-8")
        parts.append(f"<script>{inline_script(mermaid)}</script>")
        parts.append(
            "<script>mermaid.initialize({startOnLoad:false,securityLevel:'strict'});"
            "mermaid.run({querySelector:'pre.mermaid'});</script>")
    return "\n".join(parts)
