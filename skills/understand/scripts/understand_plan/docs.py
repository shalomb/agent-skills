# pyright: reportMissingImports=false
"""Docs profile analysis: extracts links, computes reading order, and creates document bundle."""

from __future__ import annotations

import json
import os
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .models import Lens

DOC_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkdn", ".rst", ".adoc"}

LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True)
class DocNode:
    """Document representation in docs profile."""

    path: str
    title: str
    summary: str
    links: list[str]


@dataclass(frozen=True)
class DocsAnalysis:
    """Result of analyzing documents in a directory."""

    documents: list[DocNode]
    links: list[tuple[str, str]]
    reading_order: list[DocNode]


def _extract_frontmatter_field(frontmatter: str, field: str) -> str | None:
    match = re.search(rf"^{field}\s*:\s*[\"']?(.*?)[\"']?\s*$", frontmatter, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_title_and_summary(content: str, default_title: str) -> tuple[str, str]:
    """Extracts document title and summary from frontmatter, markdown headings, or body."""
    title = None
    summary = None

    fm_match = FRONTMATTER_RE.match(content)
    body = content
    if fm_match:
        fm = fm_match.group(1)
        title = _extract_frontmatter_field(fm, "title")
        summary = _extract_frontmatter_field(fm, "description") or _extract_frontmatter_field(fm, "summary")
        body = content[fm_match.end() :]

    if not title:
        h_match = HEADING_RE.search(body)
        if h_match:
            title = h_match.group(1).strip()

    if not title:
        stem = Path(default_title).stem
        title = stem.replace("-", " ").replace("_", " ").title()

    if not summary:
        # First non-empty, non-heading paragraph
        for line in body.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("<!--") and not s.startswith("!["):
                summary = s
                break

    return title, summary or f"Document {default_title}"


def extract_markdown_links(content: str, source_file: str) -> list[str]:
    """Extracts relative paths of markdown links from markdown content."""
    links: list[str] = []
    source_parent = PurePosixPath(source_file).parent

    for _, target_raw in LINK_RE.findall(content):
        target = target_raw.strip().split()[0].strip("<>")
        target = target.split("#")[0].split("?")[0]
        if not target:
            continue
        if any(target.startswith(p) for p in ("http://", "https://", "mailto:", "ftp://")):
            continue

        resolved = (
            PurePosixPath(os.path.normpath(str(source_parent / target)))
            if str(source_parent) != "."
            else PurePosixPath(os.path.normpath(target))
        )
        resolved_str = str(resolved).replace("\\", "/")
        if not resolved_str.startswith(".."):
            links.append(resolved_str)

    return links


def _natural_key(text: str) -> list[int | str]:
    parts = re.split(r"(\d+)", text)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def analyze_docs_directory(
    root: Path,
    file_list: list[str] | None = None,
) -> DocsAnalysis:
    """Discovers markdown documents, maps internal links, and builds reading order."""
    if file_list is None:
        file_list = []
        for current, _, filenames in os.walk(root):
            curr_p = Path(current)
            for fname in filenames:
                fpath = curr_p / fname
                try:
                    rel = str(fpath.relative_to(root)).replace("\\", "/")
                    file_list.append(rel)
                except ValueError:
                    continue

    doc_files = [
        f for f in file_list if Path(f).suffix.lower() in DOC_EXTENSIONS
    ]
    doc_files_set = set(doc_files)

    # Parse docs
    doc_nodes_by_path: dict[str, DocNode] = {}
    edges: list[tuple[str, str]] = []
    in_degrees: dict[str, int] = {f: 0 for f in doc_files}
    out_links_map: dict[str, list[str]] = {f: [] for f in doc_files}

    for path_str in doc_files:
        full_path = root / path_str
        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            content = ""

        title, summary = extract_title_and_summary(content, path_str)
        raw_links = extract_markdown_links(content, path_str)

        valid_targets = []
        for t in raw_links:
            # Check direct match or with .md
            candidate = t if t in doc_files_set else f"{t}.md"
            if candidate in doc_files_set and candidate != path_str:
                valid_targets.append(candidate)
                edges.append((path_str, candidate))
                in_degrees[candidate] += 1

        valid_targets_unique = sorted(set(valid_targets))
        out_links_map[path_str] = valid_targets_unique
        doc_nodes_by_path[path_str] = DocNode(
            path=path_str,
            title=title,
            summary=summary,
            links=valid_targets_unique,
        )

    # Build sequential reading order
    # Priority: README / index, followed by BFS traversal along links, then unvisited by natural sort
    visited: set[str] = set()
    order: list[DocNode] = []

    def visit(path: str):
        if path not in visited and path in doc_nodes_by_path:
            visited.add(path)
            order.append(doc_nodes_by_path[path])

    # Find starting entry points
    def entry_score(path: str) -> tuple[int, int]:
        name_lower = Path(path).name.lower()
        if name_lower in ("readme.md", "index.md"):
            prio = 0
        elif name_lower.startswith(("01-", "00-", "01_", "00_")):
            prio = 1
        elif name_lower.startswith(("intro", "getting-started", "overview")):
            prio = 2
        elif in_degrees.get(path, 0) == 0:
            prio = 3
        else:
            prio = 4
        return (prio, in_degrees.get(path, 0))

    sorted_entries = sorted(doc_files, key=lambda f: (entry_score(f), _natural_key(f)))

    # BFS from entry candidates
    for start in sorted_entries:
        if start in visited:
            continue
        queue = deque([start])
        while queue:
            curr = queue.popleft()
            if curr in visited:
                continue
            visit(curr)
            for neighbor in out_links_map.get(curr, []):
                if neighbor not in visited:
                    queue.append(neighbor)

    # Any remaining documents in natural sort order
    for path in sorted(doc_files, key=_natural_key):
        visit(path)

    return DocsAnalysis(
        documents=[doc_nodes_by_path[p] for p in doc_files],
        links=edges,
        reading_order=order,
    )


def generate_docs_bundle(
    bundle_dir: Path,
    repo_path: Path,
    lens: Lens | None = None,
    files: list[str] | None = None,
) -> str:
    """Generates bundle for docs profile including reading order, document map, and graph."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = bundle_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    analysis = analyze_docs_directory(repo_path, files)

    # Build graph.json
    if lens and lens.target:
        title = f"Topic: {lens.target}"
        topic_intro = f"This topic report focuses on **{lens.target}**.\n\n"
    else:
        title = f"Documentation: {repo_path.name or 'Report'}"
        topic_intro = ""

    nodes = []
    for doc in analysis.documents:
        nodes.append({
            "anchor_id": doc.path,
            "label": doc.title,
            "path": doc.path,
            "kind": "document",
            "summary": doc.summary,
        })

    # Avoid empty graph
    if not nodes:
        nodes.append({
            "anchor_id": "root",
            "label": repo_path.name or "root",
            "path": "README.md",
            "kind": "document",
            "summary": "Documentation root",
        })

    edges = []
    for src, tgt in analysis.links:
        edges.append({
            "source": src,
            "target": tgt,
            "kind": "links_to",
        })

    graph = {
        "schema_version": 1,
        "title": title,
        "nodes": nodes,
        "edges": edges,
    }
    (bundle_dir / "graph.json").write_text(
        json.dumps(graph, indent=2) + "\n", encoding="utf-8"
    )

    # Section 1: Reading Order
    reading_order_lines = [
        f"# Reading Order\n\n{topic_intro}Recommended sequential reading order:\n"
    ]
    for i, doc in enumerate(analysis.reading_order, start=1):
        reading_order_lines.append(
            f"{i}. **[{doc.title}]({doc.path})** (`{doc.path}`)\n   {doc.summary}\n"
        )
    (sections_dir / "01-reading-order.md").write_text(
        "\n".join(reading_order_lines) + "\n", encoding="utf-8"
    )

    # Section 2: Document Map
    doc_map_lines = [
        "# Document Map\n\nThis document map shows the structure and connections between documents:\n"
    ]
    for doc in analysis.reading_order:
        doc_map_lines.append(f"### [{doc.title}]({doc.path}) (`{doc.path}`)\n")
        if doc.links:
            doc_map_lines.append("Links to:")
            for tgt in doc.links:
                doc_map_lines.append(f"- `{tgt}`")
        else:
            doc_map_lines.append("- *(no outgoing document links)*")
        doc_map_lines.append("")
    (sections_dir / "02-document-map.md").write_text(
        "\n".join(doc_map_lines) + "\n", encoding="utf-8"
    )

    if lens and lens.target:
        return (
            f"Docs topic report on {lens.target} covering {len(analysis.documents)} documents "
            f"and {len(analysis.links)} links."
        )
    return (
        f"Docs report covering {len(analysis.documents)} documents "
        f"and {len(analysis.links)} links."
    )
