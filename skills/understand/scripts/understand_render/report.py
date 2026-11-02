"""The report page: narrative sections first, graph, key flows/remaining, glossary last."""
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


def graph_elements(bundle, remote_info=None):
    """Cytoscape elements. Ids are anchor ids, so edges link by anchor, not by position."""
    nodes = []
    for n in bundle.nodes:
        data = {
            "id": n.anchor_id,
            "label": n.label,
            "kind": n.kind,
            "path": n.path,
            "href": view_href(n.path, n.line),
            "summary": n.summary,
            "hub": getattr(n, "hub", False),
        }
        if remote_info and n.path and n.kind != "folder":
            r_url = None
            file_link_fn = getattr(remote_info, "file_link", None)
            if callable(file_link_fn):
                r_url = file_link_fn(n.path, n.line)
            elif callable(remote_info):
                r_url = remote_info(n.path, n.line)
            if isinstance(r_url, str):
                data["remote_href"] = r_url
                host = getattr(remote_info, "host", "github")
                if isinstance(remote_info, dict):
                    host = remote_info.get("host", "github")
                host_name = "GitLab" if str(host).lower() == "gitlab" else "GitHub"
                data["remote_label"] = f"View on {host_name} ↗"
        elem = {"data": data, "classes": "dim"} if n.dimmed else {"data": data}
        nodes.append(elem)
    edges = [
        {"data": {"source": e.source, "target": e.target, "kind": e.kind}}
        for e in bundle.edges]
    return nodes + edges


def _split_sections(sections):
    """Split sections into narrative sections first, and key flows/remaining narrative sections."""
    if not sections:
        return [], []
    # 1. Look for a section explicitly matching key flows / flow
    flow_idx = None
    for idx, s in enumerate(sections):
        s_id = s.anchor_id.lower()
        s_title = s.title.lower()
        if "flow" in s_id or "flow" in s_title:
            flow_idx = idx
            break
    if flow_idx is not None and flow_idx > 0:
        return sections[:flow_idx], sections[flow_idx:]

    # 2. Check for known introductory / narrative-first patterns
    intro_keywords = ("context", "architecture", "overview", "reading-order")
    intro_indices = [
        idx for idx, s in enumerate(sections)
        if any(kw in s.anchor_id.lower() or kw in s.title.lower() for kw in intro_keywords)
    ]
    if intro_indices:
        split_idx = 0
        while split_idx < len(sections) and split_idx in intro_indices:
            split_idx += 1
        if 0 < split_idx < len(sections):
            return sections[:split_idx], sections[split_idx:]

    # 3. Fallback: if len > 1, put first section before graph, remainder after
    if len(sections) > 1:
        return sections[:1], sections[1:]
    return sections, []


def render_report(bundle, diagram, rewrite_link, uses_in_page_mermaid, remote_info=None):
    """The whole report page as one HTML string.

    `diagram` turns Mermaid source into HTML; `rewrite_link` maps a Markdown link
    target to an address; `uses_in_page_mermaid` is asked last, after all diagrams are made.
    """
    first_secs, remaining_secs = _split_sections(bundle.sections)

    sections = []
    for s in first_secs:
        sections.append((s.anchor_id, s.title, _markdown_section(s, rewrite_link, diagram)))

    sections.append((GRAPH_ID, "Graph", _graph_section(bundle, remote_info=remote_info)))

    for s in remaining_secs:
        sections.append((s.anchor_id, s.title, _markdown_section(s, rewrite_link, diagram)))

    sections.append((GLOSSARY_ID, "Glossary", _glossary_section(bundle)))

    nav = "".join(f'<li><a href="#{html.escape(i)}">{html.escape(t)}</a></li>' for i, t, _ in sections)
    body = "".join(
        f'<section class="report-section" id="{html.escape(i)}"><h2>{html.escape(t)}</h2>{content}</section>'
        for i, t, content in sections)
    title = html.escape(bundle.title)

    quick_links = ['<a href="/r/understand/">← All Reports</a>']
    if remote_info:
        web_base = getattr(remote_info, "web_base", None)
        if isinstance(remote_info, dict):
            web_base = remote_info.get("web_base")
        if web_base:
            host = getattr(remote_info, "host", "github")
            if isinstance(remote_info, dict):
                host = remote_info.get("host", "github")
            host_label = "GitLab" if str(host).lower() == "gitlab" else "GitHub"
            quick_links.append(
                f'<a href="{html.escape(web_base)}" target="_blank" rel="noopener noreferrer">{host_label} ↗</a>'
            )
    quick_html = f'<div class="side-quick-links">{"".join(quick_links)}</div>'

    document = (
        f'<div class="wrap"><header class="masthead"><p class="eyebrow">{icon("account_tree")} Understand</p>'
        f'<h1>{title}</h1><p>{len(bundle.nodes)} nodes, {len(bundle.edges)} edges</p></header>'
        f'<nav class="side" aria-label="Sections">{quick_html}<h2>Contents</h2><ol>{nav}</ol></nav>'
        f'<article>{body}</article></div>')
    return page(bundle.title, document, _scripts(bundle, uses_in_page_mermaid(), remote_info=remote_info))


def _markdown_section(section, rewrite_link, diagram):
    text = _without_first_heading(section.markdown)
    return render_markdown(text, heading_offset=1, rewrite_link=rewrite_link, render_diagram=diagram)


def _without_first_heading(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return "\n".join(lines[:i] + lines[i + 1:])
    return text


def _graph_section(bundle, remote_info=None):
    kinds = sorted({n.kind for n in bundle.nodes})
    options = '<option value="">All kinds</option>' + "".join(
        f'<option value="{html.escape(k)}">{html.escape(k)}</option>' for k in kinds)
    items = "".join(_node_item(n, remote_info=remote_info) for n in bundle.nodes)

    def _cited_item(i, c):
        remote_badge = ""
        if remote_info and c.path:
            r_url = None
            if hasattr(remote_info, "file_link"):
                r_url = remote_info.file_link(c.path, c.line)
            elif callable(remote_info):
                r_url = remote_info(c.path, c.line)
            if isinstance(r_url, str):
                remote_badge = f' <a class="remote-badge" href="{html.escape(r_url)}" target="_blank" rel="noopener noreferrer">view online ↗</a>'
        return (
            f'<li id="{html.escape(i)}"><a href="{html.escape(view_href(c.path, c.line))}">'
            f'{html.escape(c.path)}:{c.line}</a>{remote_badge} <span class="summary">{html.escape(i)}</span></li>'
        )

    cited = "".join(_cited_item(i, c) for i, c in bundle.extra_anchors.items())
    cited_block = f'<h3>Cited places</h3><ul class="entries">{cited}</ul>' if cited else ""
    node_count = len(bundle.nodes)
    return (
        '<div class="graph-tools">'
        '<input id="graph-search" type="search" placeholder="Search nodes" aria-label="Search nodes">'
        f'<select id="graph-kind" aria-label="Filter by kind">{options}</select></div>'
        '<div class="graph-viewport">'
        '<div id="graph-canvas"></div>'
        '<div id="graph-inspector" class="graph-inspector" hidden></div></div>'
        f'<details class="node-drawer"><summary>Browse all nodes as text list ({node_count} items)</summary>'
        f'<ul class="nodes">{items}</ul></details>{cited_block}')


def _node_item(node, remote_info=None):
    summary = f'<span class="summary">{html.escape(node.summary)}</span>' if node.summary else ""
    dim_class = ' class="dim"' if node.dimmed else ""
    remote_badge = ""
    if remote_info and node.path and node.kind != "folder":
        r_url = None
        if hasattr(remote_info, "file_link"):
            r_url = remote_info.file_link(node.path, node.line)
        elif callable(remote_info):
            r_url = remote_info(node.path, node.line)
        if isinstance(r_url, str):
            remote_badge = f' <a class="remote-badge" href="{html.escape(r_url)}" target="_blank" rel="noopener noreferrer">view online ↗</a>'
    return (
        f'<li id="{html.escape(node.anchor_id)}"{dim_class}><span class="kind">{html.escape(node.kind)}</span>'
        f'<a href="{html.escape(view_href(node.path, node.line))}">{html.escape(node.label)}</a>{remote_badge}{summary}</li>')


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


def _scripts(bundle, with_mermaid, remote_info=None):
    data = json.dumps(graph_elements(bundle, remote_info=remote_info)).replace("<", "\\u003c")
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
