"""Load a bundle directory and validate it against the versioned schema (ADR 0001).

Schema version 1:
  graph.json     {"schema_version": 1, "title"?, "nodes": [...], "edges": [...]}
                 node: {"label", "path", "kind"?, "symbol"?, "line"?, "summary"?}
                 edge: {"source", "target", "kind"?}  (source and target are anchor ids)
  anchors.json   optional, {"<id>": {"path", "line"}}: extra cited places
  glossary.json  optional, {"contexts": [{"name", "terms": [{"term", "meaning"}]}]}
  sections/*.md  at least one, ordered by file name
"""
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .anchors import node_anchor_id, section_anchor_id

SCHEMA_VERSION = 1
RENDERER_OWNED_SECTIONS = ("graph", "glossary")


class BundleError(Exception):
    """The bundle cannot be trusted; the message names the faulty part."""


@dataclass(frozen=True)
class Node:
    anchor_id: str
    label: str
    kind: str
    path: str
    symbol: str | None
    line: int | None
    summary: str
    dimmed: bool = False
    hub: bool = False


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str


@dataclass(frozen=True)
class Section:
    anchor_id: str
    filename: str
    title: str
    markdown: str


@dataclass(frozen=True)
class GlossaryTerm:
    term: str
    meaning: str


@dataclass(frozen=True)
class GlossaryContext:
    name: str
    terms: list[GlossaryTerm]


@dataclass(frozen=True)
class CitedPlace:
    path: str
    line: int


@dataclass
class Bundle:
    title: str
    nodes: list[Node]
    edges: list[Edge]
    sections: list[Section]
    glossary_contexts: list[GlossaryContext]
    extra_anchors: dict[str, CitedPlace] = field(default_factory=dict)

    def cited_paths(self):
        paths = {n.path for n in self.nodes} | {c.path for c in self.extra_anchors.values()}
        return sorted(paths)


def load_bundle(directory):
    directory = Path(directory)
    _refuse_html(directory)
    graph = _read_required_json(directory / "graph.json")
    _check_version(graph)
    nodes = _nodes(graph.get("nodes"))
    edges = _edges(graph.get("edges", []), {n.anchor_id for n in nodes})
    return Bundle(
        title=_str(graph, "title", "graph.json", default="Report"),
        nodes=nodes,
        edges=edges,
        sections=_sections(directory / "sections"),
        glossary_contexts=_glossary(_read_optional_json(directory / "glossary.json")),
        extra_anchors=_anchors(_read_optional_json(directory / "anchors.json")),
    )


def _refuse_html(directory):
    for found in sorted(directory.rglob("*.html")):
        raise BundleError(
            f"{found.relative_to(directory)}: a bundle holds no HTML; agents do not write HTML (ADR 0001)")


def _read_required_json(path):
    if not path.is_file():
        raise BundleError(f"{path.name} is missing from the bundle")
    return _parse_json(path)


def _read_optional_json(path):
    return _parse_json(path) if path.is_file() else None


def _parse_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BundleError(f"{path.name} is not valid JSON: {exc}") from exc


def _check_version(graph):
    if not isinstance(graph, dict) or "schema_version" not in graph:
        raise BundleError(f'graph.json has no schema_version; this renderer reads version {SCHEMA_VERSION}')
    version = graph["schema_version"]
    if version != SCHEMA_VERSION or isinstance(version, bool):
        raise BundleError(
            f"graph.json schema_version {version!r} is not supported; this renderer reads version {SCHEMA_VERSION}")


def _optional_str(obj, key, where):
    value = obj.get(key)
    if value is not None and not isinstance(value, str):
        raise BundleError(f"{where}: field {key!r} must be a string")
    return value


def _str(obj, key, where, default):
    return _optional_str(obj, key, where) or default


def _relative_path(value):
    p = PurePosixPath(value)
    return bool(value) and "\\" not in value and not p.is_absolute() and ".." not in p.parts


def _nodes(raw):
    if not isinstance(raw, list):
        raise BundleError("graph.json: 'nodes' must be a list")
    nodes, seen = [], {}
    for i, item in enumerate(raw):
        where = f"graph.json nodes[{i}]"
        if not isinstance(item, dict):
            raise BundleError(f"{where}: must be an object")
        if isinstance(item.get("label"), str) and item["label"]:
            where += f' "{item["label"]}"'
        for key in ("label", "path"):
            if not isinstance(item.get(key), str) or not item[key]:
                raise BundleError(f'{where}: missing required field "{key}"')
        if not _relative_path(item["path"]):
            raise BundleError(
                f'{where}: field "path" must be a relative path inside the repository, got {item["path"]!r}')
        line = item.get("line")
        if line is not None and (not isinstance(line, int) or isinstance(line, bool) or line < 1):
            raise BundleError(f'{where}: field "line" must be a positive integer')
        symbol = _optional_str(item, "symbol", where)
        dimmed = bool(item.get("dimmed", False))
        hub = bool(item.get("hub", False))
        node = Node(
            anchor_id=node_anchor_id(item["path"], symbol), label=item["label"],
            kind=_str(item, "kind", where, default="file"), path=item["path"],
            symbol=symbol, line=line, summary=_str(item, "summary", where, default=""),
            dimmed=dimmed, hub=hub)
        if node.anchor_id in seen:
            raise BundleError(f'{where}: duplicate anchor {node.anchor_id!r}, already used by nodes[{seen[node.anchor_id]}]')
        seen[node.anchor_id] = i
        nodes.append(node)
    return nodes


def _edges(raw, node_ids):
    if not isinstance(raw, list):
        raise BundleError("graph.json: 'edges' must be a list")
    edges = []
    for i, item in enumerate(raw):
        where = f"graph.json edges[{i}]"
        if not isinstance(item, dict):
            raise BundleError(f"{where}: must be an object")
        for key in ("source", "target"):
            if not isinstance(item.get(key), str):
                raise BundleError(f'{where}: missing required field "{key}"')
            if item[key] not in node_ids:
                raise BundleError(f'{where}: {key} {item[key]!r} is not a node anchor')
        edges.append(Edge(item["source"], item["target"], _str(item, "kind", where, default="")))
    return edges


def _sections(directory):
    files = sorted(directory.glob("*.md")) if directory.is_dir() else []
    if not files:
        raise BundleError("sections/ has no .md files; a bundle needs at least one section")
    sections, seen = [], set()
    for f in files:
        anchor_id = section_anchor_id(f.name)
        if anchor_id in RENDERER_OWNED_SECTIONS:
            raise BundleError(f"sections/{f.name}: the name {anchor_id!r} belongs to the renderer")
        if anchor_id in seen:
            raise BundleError(f"sections/{f.name}: duplicate section name {anchor_id!r}")
        seen.add(anchor_id)
        text = f.read_text(encoding="utf-8")
        sections.append(Section(anchor_id, f.name, _first_heading(text) or anchor_id.replace("-", " ").title(), text))
    return sections


def _first_heading(text):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _glossary(raw):
    if raw is None:
        return []
    contexts = raw.get("contexts") if isinstance(raw, dict) else None
    if not isinstance(contexts, list):
        raise BundleError("glossary.json: 'contexts' must be a list")
    result = []
    for i, ctx in enumerate(contexts):
        if not isinstance(ctx, dict) or not isinstance(ctx.get("name"), str):
            raise BundleError(f'glossary.json contexts[{i}]: missing required field "name"')
        terms = []
        for j, t in enumerate(ctx.get("terms", [])):
            where = f'glossary.json contexts[{i}] "{ctx["name"]}" terms[{j}]'
            if not isinstance(t, dict) or not isinstance(t.get("term"), str):
                raise BundleError(f'{where}: missing required field "term"')
            where += f' "{t["term"]}"'
            if not isinstance(t.get("meaning"), str):
                raise BundleError(f'{where}: missing required field "meaning"')
            terms.append(GlossaryTerm(t["term"], t["meaning"]))
        result.append(GlossaryContext(ctx["name"], terms))
    return result


def _anchors(raw):
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise BundleError("anchors.json must be an object that maps ids to places")
    places = {}
    for anchor_id, entry in raw.items():
        where = f"anchors.json {anchor_id!r}"
        if not isinstance(entry, dict):
            raise BundleError(f"{where}: must be an object")
        if not isinstance(entry.get("path"), str) or not _relative_path(entry["path"]):
            raise BundleError(f'{where}: field "path" must be a relative path inside the repository')
        line = entry.get("line")
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            raise BundleError(f'{where}: missing required field "line" (a positive integer)')
        places[anchor_id] = CitedPlace(entry["path"], line)
    return places
