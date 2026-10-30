"""The report page: graph, sections in file order, glossary last."""
import html
import json
import re
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


def _slug(text):
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return cleaned or "item"


def _glossary_draft(contexts, collisions):
    lines = ["# Glossary\n"]
    valid = [c for c in contexts if c.terms]
    if not valid:
        lines.append("## domain\n\n**Term**:\nDefinition of term.\n")
        return "\n".join(lines).strip() + "\n"
    for ctx in valid:
        lines.append(f"## {ctx.name}\n")
        for t in ctx.terms:
            lines.append(f"**{t.term}**:\n{t.meaning}\n")
    if collisions:
        lines.append("## Collisions\n")
        for term_name, _, occs in collisions:
            ctx_meanings = ", ".join(f'"{c}" ({t.meaning})' for c, t in occs)
            lines.append(f"- **{term_name}**: multiple meanings in {ctx_meanings}\n")
    return "\n".join(lines).strip() + "\n"


def _glossary_section(bundle):
    term_occs = {}
    for ctx in bundle.glossary_contexts:
        for t in ctx.terms:
            key = t.term.strip().lower()
            if not key:
                continue
            term_occs.setdefault(key, []).append((ctx.name, t))

    collisions = []
    collided_keys = set()
    for key, occs in sorted(term_occs.items()):
        contexts_seen = {c for c, _ in occs}
        if len(contexts_seen) < 2:
            continue
        meanings_set = {t.meaning.strip() for _, t in occs}
        if len(meanings_set) <= 1:
            continue
        canonical_term = occs[0][1].term
        collisions.append((canonical_term, key, occs))
        collided_keys.add(key)

    draft_text = _glossary_draft(bundle.glossary_contexts, collisions)
    draft_block = (
        '<div class="glossary-draft">'
        '<h3>Glossary draft</h3>'
        '<p>Suggested <code>GLOSSARY.md</code> draft that can be applied to the repository:</p>'
        f'<pre class="glossary-draft-text"><code>{html.escape(draft_text)}</code></pre></div>'
    )

    if not any(c.terms for c in bundle.glossary_contexts):
        return f"<p>This report defines no terms.</p>{draft_block}"

    seen_ids = set()
    term_anchors = {}
    for ctx in bundle.glossary_contexts:
        for t in ctx.terms:
            base = f"glossary-{_slug(ctx.name)}-{_slug(t.term)}"
            cand = base
            counter = 2
            while cand in seen_ids:
                cand = f"{base}-{counter}"
                counter += 1
            seen_ids.add(cand)
            term_anchors[(ctx.name, t.term.strip().lower())] = cand

    out = []

    if collisions:
        collision_items = []
        for term_name, key, occs in collisions:
            links = []
            for ctx_name, t in occs:
                anchor = term_anchors.get((ctx_name, key), "")
                href = f"#{anchor}" if anchor else "#"
                links.append(f'<a href="{html.escape(href)}">{html.escape(ctx_name)}</a>: {html.escape(t.meaning)}')
            links_html = " &middot; ".join(links)
            collision_items.append(f'<li><strong>{html.escape(term_name)}</strong>: {links_html}</li>')
        collisions_html = "".join(collision_items)
        out.append(
            '<div class="glossary-collisions">'
            '<h3>Collisions</h3>'
            '<p>The following terms have different meanings across contexts:</p>'
            f'<ul class="collision-list">{collisions_html}</ul></div>'
        )

    for context in bundle.glossary_contexts:
        items = []
        for t in context.terms:
            k = t.term.strip().lower()
            anchor = term_anchors.get((context.name, k), "")
            id_attr = f' id="{html.escape(anchor)}"' if anchor else ""
            badge = ' <span class="collision-badge">collision</span>' if k in collided_keys else ""
            items.append(f"<dt{id_attr}>{html.escape(t.term)}{badge}</dt><dd>{html.escape(t.meaning)}</dd>")
        terms_html = "".join(items)
        out.append(f'<h3>{html.escape(context.name)}</h3><dl class="terms">{terms_html}</dl>')

    out.append(draft_block)
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
