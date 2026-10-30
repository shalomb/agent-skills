"""One render run: validate the bundle, then write the report, source views and anchors index."""
import json
import re
from pathlib import Path

from .bundle import load_bundle
from .diagrams import DiagramRenderer
from .report import render_report, view_href
from .sourceview import render_source_view

LINE_FRAGMENT = re.compile(r"^L(\d+)$")


def render_run(bundle_dir, source_root, out_dir, mmdc_path, chromium_path, log):
    """Render `bundle_dir` into `out_dir`. Raises BundleError before anything is written."""
    bundle = load_bundle(bundle_dir)
    out_dir = Path(out_dir)
    source_root = Path(source_root) if source_root else None
    log_lines = []

    def record(message):
        log_lines.append(message)
        log(message)

    diagrams = DiagramRenderer(mmdc_path, chromium_path, record)
    viewed = set(bundle.cited_paths())

    def rewrite_link(target):
        path, _, fragment = target.partition("#")
        if not (path in viewed or _is_source_file(source_root, path)):
            return target
        viewed.add(path)
        line = LINE_FRAGMENT.match(fragment)
        return view_href(path, int(line.group(1)) if line else None)

    report = render_report(bundle, diagram=diagrams.render, rewrite_link=rewrite_link,
                           uses_in_page_mermaid=diagrams.uses_in_page_mermaid)
    diagrams.log_summary()

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.html").write_text(report, encoding="utf-8")
    for path in sorted(viewed):
        target = out_dir / "src" / f"{path}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        depth = path.count("/") + 1
        target.write_text(
            render_source_view(path, _read_source(source_root, path), report_href="../" * depth + "report.html"),
            encoding="utf-8")
    (out_dir / "anchors.json").write_text(
        json.dumps(_anchor_index(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "render.log").write_text("".join(f"{line}\n" for line in log_lines), encoding="utf-8")


def _anchor_index(bundle):
    index = {n.anchor_id: {"url": f"report.html#{n.anchor_id}", "path": n.path, "line": n.line or 1}
             for n in bundle.nodes}
    for anchor_id, place in bundle.extra_anchors.items():
        index[anchor_id] = {"url": f"report.html#{anchor_id}", "path": place.path, "line": place.line}
    return index


def _inside_root(source_root, path):
    """The real file for `path` when it lies inside `source_root`, else None."""
    if source_root is None or not path or path.startswith("/") or ".." in path.split("/"):
        return None
    candidate = (source_root / path).resolve()
    root = source_root.resolve()
    return candidate if candidate.is_file() and root in candidate.parents else None


def _is_source_file(source_root, path):
    return _inside_root(source_root, path) is not None


def _read_source(source_root, path):
    found = _inside_root(source_root, path)
    return found.read_text(encoding="utf-8", errors="replace") if found else None
