# pyright: reportMissingImports=false
"""Dependency and topology extraction module for /understand.

Extracts repository dependency flow graphs using codemap as primary tool
and AST/regex static analysis for Python and JS/TS as fallback.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
from typing import Any

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

JS_IMPORT_RE = re.compile(
    r"""(?:import|export)\s+(?:(?:(?:\*|[\w{}\s,*$]+)\s+from\s+)?['"]([^'"]+)['"]|(?:['"]([^'"]+)['"]))"""
    r"""|"""
    r"""(?:require|import)\s*\(\s*['"]([^'"]+)['"]\s*\)"""
)

VALID_KINDS = {"imports", "calls", "depends_on"}


@dataclass
class DependencyGraph:
    """Dependency graph and topology metrics for codebase files."""

    edges: list[tuple[str, str, str]] = field(default_factory=list)
    hubs: list[str] = field(default_factory=list)
    metrics: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serializes graph to a dictionary."""
        return {
            "edges": [
                {"source": s, "target": t, "kind": k}
                for s, t, k in self.edges
            ],
            "hubs": list(self.hubs),
            "metrics": {
                k: dict(v) for k, v in self.metrics.items()
            },
        }


def strip_ansi(text: str) -> str:
    """Removes ANSI color and control escape sequences from text."""
    return ANSI_ESCAPE_RE.sub("", text)


def _normalize_name(name: str) -> str:
    """Strips parenthetical annotations, quotes, and whitespace from a token."""
    cleaned = re.sub(r"\s*\([^)]*\)", "", name)
    cleaned = cleaned.strip().strip("'\"`")
    cleaned = cleaned.replace("\\", "/")
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.strip()


class FileResolver:
    """Resolves short names, stems, and relative paths to repository files."""

    def __init__(self, files: list[str]) -> None:
        self.files = sorted({f.replace("\\", "/").lstrip("./") for f in files})
        self.files_set = set(self.files)
        self.without_ext: dict[str, list[str]] = {}
        self.by_stem: dict[str, list[str]] = {}
        self.by_name: dict[str, list[str]] = {}

        for f in self.files:
            p = Path(f)
            no_ext = str(p.with_suffix("")).replace("\\", "/")
            self.without_ext.setdefault(no_ext, []).append(f)
            self.by_stem.setdefault(p.stem, []).append(f)
            self.by_name.setdefault(p.name, []).append(f)

    def resolve(self, name: str, current_section: str | None = None) -> str | None:
        """Resolves a raw name or short name back to an exact path in files."""
        clean = _normalize_name(name)
        if not clean:
            return None

        # 1. Exact match
        if clean in self.files_set:
            return clean

        # 2. Path without extension match
        if clean in self.without_ext:
            matches = self.without_ext[clean]
            if len(matches) == 1:
                return matches[0]
            if current_section:
                sec_lower = current_section.strip("/").lower()
                sec_matches = [m for m in matches if m.lower().startswith(sec_lower + "/")]
                if len(sec_matches) == 1:
                    return sec_matches[0]
            return matches[0]

        # 3. Section prefix match
        if current_section and current_section not in (".", "", "/"):
            sec_clean = current_section.strip("/")
            for prefix in (sec_clean.lower(), sec_clean):
                cand = f"{prefix}/{clean}"
                if cand in self.files_set:
                    return cand
                if cand in self.without_ext:
                    return self.without_ext[cand][0]

        # 4. Suffix match if path has slashes
        if "/" in clean:
            suffix = "/" + clean
            suffix_matches = [
                f for f in self.files
                if f.endswith(suffix) or str(Path(f).with_suffix("")).endswith(suffix)
            ]
            if len(suffix_matches) == 1:
                return suffix_matches[0]
            if len(suffix_matches) > 1 and current_section:
                sec_lower = current_section.strip("/").lower()
                sec_m = [m for m in suffix_matches if m.lower().startswith(sec_lower + "/")]
                if len(sec_m) == 1:
                    return sec_m[0]

        # 5. Stem / filename match
        stem_candidates = self.by_stem.get(clean) or self.by_name.get(clean) or []
        if len(stem_candidates) == 1:
            return stem_candidates[0]
        if len(stem_candidates) > 1 and current_section:
            sec_lower = current_section.strip("/").lower()
            sec_m = [m for m in stem_candidates if m.lower().startswith(sec_lower + "/")]
            if len(sec_m) == 1:
                return sec_m[0]

        return None


def compute_metrics(
    files: list[str], edges: list[tuple[str, str, str]]
) -> dict[str, dict[str, int]]:
    """Computes in-degree and out-degree metrics for all files."""
    metrics: dict[str, dict[str, int]] = {
        f: {"in_degree": 0, "out_degree": 0, "in": 0, "out": 0}
        for f in files
    }

    for src, tgt, _ in edges:
        if src in metrics:
            metrics[src]["out_degree"] += 1
            metrics[src]["out"] += 1
        else:
            metrics[src] = {"in_degree": 0, "out_degree": 1, "in": 0, "out": 1}

        if tgt in metrics:
            metrics[tgt]["in_degree"] += 1
            metrics[tgt]["in"] += 1
        else:
            metrics[tgt] = {"in_degree": 1, "out_degree": 0, "in": 1, "out": 0}

    return metrics


def detect_hubs(
    metrics: dict[str, dict[str, int]], threshold: int = 3
) -> list[str]:
    """Identifies hub files whose in-degree meets or exceeds threshold.

    Returns hubs sorted descending by in-degree, then alphabetically by file path.
    """
    hubs = [
        f for f, m in metrics.items()
        if m.get("in_degree", 0) >= threshold
    ]
    hubs.sort(key=lambda f: (-metrics[f].get("in_degree", 0), f))
    return hubs


def normalize_edges(
    raw_edges: list[tuple[str, str, str]], files: list[str]
) -> list[tuple[str, str, str]]:
    """Resolves endpoints against files, removes self-loops and duplicates, and validates kind."""
    resolver = FileResolver(files)
    normalized: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for s_raw, t_raw, k_raw in raw_edges:
        src = resolver.resolve(s_raw)
        tgt = resolver.resolve(t_raw)
        if not src or not tgt or src == tgt:
            continue
        if src not in resolver.files_set or tgt not in resolver.files_set:
            continue

        kind = k_raw if k_raw in VALID_KINDS else "imports"
        edge = (src, tgt, kind)
        if edge not in seen:
            seen.add(edge)
            normalized.append(edge)

    return normalized


def parse_codemap_deps(output: str, files: list[str]) -> DependencyGraph:
    """Parses `codemap --deps` output into a DependencyGraph."""
    clean_text = strip_ansi(output)
    resolver = FileResolver(files)
    raw_edges: list[tuple[str, str, str]] = []
    codemap_hubs: list[str] = []
    current_section: str | None = None

    arrow_pattern = re.compile(r"\s*(?:───▶|──▶|-->|->|→)\s*")
    section_pattern = re.compile(r"^([\w.\-_/]+)\s+═{3,}")

    for line in clean_text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue

        # Check section header (e.g., "Src ═══════════════" or ". ═══════════════")
        m_sec = section_pattern.match(trimmed)
        if m_sec:
            current_section = m_sec.group(1)
            continue

        # Check HUBS header (e.g., "HUBS: src/utils (3←), src/h1 (3←)")
        if trimmed.startswith("HUBS:"):
            hubs_content = trimmed[len("HUBS:"):].strip()
            for hub_token in hubs_content.split(","):
                resolved_hub = resolver.resolve(hub_token, current_section)
                if resolved_hub and resolved_hub not in codemap_hubs:
                    codemap_hubs.append(resolved_hub)
            continue

        # Check dependency arrow lines
        if arrow_pattern.search(trimmed):
            parts = arrow_pattern.split(trimmed, maxsplit=1)
            if len(parts) == 2:
                src_raw = parts[0].strip()
                dests_raw = parts[1].strip()
                resolved_src = resolver.resolve(src_raw, current_section)
                if not resolved_src:
                    continue

                for dest_token in dests_raw.split(","):
                    resolved_dest = resolver.resolve(dest_token, current_section)
                    if resolved_dest and resolved_dest != resolved_src:
                        raw_edges.append((resolved_src, resolved_dest, "imports"))

    edges = normalize_edges(raw_edges, files)
    metrics = compute_metrics(files, edges)

    # Detect any additional hubs meeting the threshold
    detected_hubs = detect_hubs(metrics, threshold=3)
    final_hubs: list[str] = []
    for h in codemap_hubs + detected_hubs:
        if h in resolver.files_set and h not in final_hubs:
            final_hubs.append(h)

    return DependencyGraph(edges=edges, hubs=final_hubs, metrics=metrics)


def _build_python_module_index(py_files: list[str]) -> dict[str, str]:
    """Maps dotted module paths to repository-relative python file paths."""
    index: dict[str, str] = {}
    for f in py_files:
        p = Path(f)
        parts = list(p.parts)
        if not parts:
            continue

        # Remove extension from last part
        stem = p.stem
        dir_parts = parts[:-1]

        if stem == "__init__":
            mod_parts = dir_parts
        else:
            mod_parts = dir_parts + [stem]

        dotted = ".".join(mod_parts)
        if dotted:
            index[dotted] = f

        # If repo uses src/ or lib/ prefix, register without prefix as well
        if dir_parts and dir_parts[0] in ("src", "lib"):
            if stem == "__init__":
                sub_mod = dir_parts[1:]
            else:
                sub_mod = dir_parts[1:] + [stem]
            sub_dotted = ".".join(sub_mod)
            if sub_dotted:
                index[sub_dotted] = f

    return index


def extract_python_dependencies(
    root: Path, files: list[str]
) -> list[tuple[str, str, str]]:
    """Extracts internal python import edges using Python AST static analysis."""
    py_files = [f for f in files if f.endswith(".py")]
    py_set = set(py_files)
    module_index = _build_python_module_index(py_files)
    edges: list[tuple[str, str, str]] = []

    for f in py_files:
        file_path = root / f
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            continue

        cur_path = Path(f)
        cur_dir = cur_path.parent

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imp_name = alias.name
                    # Try resolving directly or prefix
                    target = module_index.get(imp_name)
                    if not target and "." in imp_name:
                        parts = imp_name.split(".")
                        for i in range(len(parts) - 1, 0, -1):
                            prefix = ".".join(parts[:i])
                            if prefix in module_index:
                                target = module_index[prefix]
                                break
                    if target and target != f:
                        edges.append((f, target, "imports"))

            elif isinstance(node, ast.ImportFrom):
                level = node.level
                mod = node.module or ""

                if level > 0:
                    # Relative import
                    base_dir = cur_dir
                    for _ in range(level - 1):
                        base_dir = base_dir.parent

                    rel_base = base_dir / mod.replace(".", "/") if mod else base_dir
                    rel_base_str = str(rel_base).replace("\\", "/").lstrip("./")

                    cand_py = (rel_base_str + ".py").lstrip("/")
                    cand_init = (rel_base_str.rstrip("/") + "/__init__.py").lstrip("/")

                    found_target: str | None = None
                    if cand_py in py_set:
                        found_target = cand_py
                    elif cand_init in py_set:
                        found_target = cand_init

                    if found_target and found_target != f:
                        edges.append((f, found_target, "imports"))
                    else:
                        # Check imported names as submodules
                        for alias in node.names:
                            sub = f"{rel_base_str}/{alias.name}".lstrip("/")
                            sub_py = sub + ".py"
                            sub_init = sub + "/__init__.py"
                            if sub_py in py_set and sub_py != f:
                                edges.append((f, sub_py, "imports"))
                            elif sub_init in py_set and sub_init != f:
                                edges.append((f, sub_init, "imports"))
                else:
                    # Absolute import within repo
                    if mod:
                        target = module_index.get(mod)
                        if target and target != f:
                            edges.append((f, target, "imports"))
                        else:
                            for alias in node.names:
                                full_mod = f"{mod}.{alias.name}"
                                target_sub = module_index.get(full_mod)
                                if target_sub and target_sub != f:
                                    edges.append((f, target_sub, "imports"))

    return normalize_edges(edges, files)


def extract_js_ts_dependencies(
    root: Path, files: list[str]
) -> list[tuple[str, str, str]]:
    """Extracts internal JS/TS import edges using regex matching and module resolution."""
    js_exts = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
    js_files = [f for f in files if Path(f).suffix.lower() in js_exts]
    files_set = set(files)
    edges: list[tuple[str, str, str]] = []

    for f in js_files:
        file_path = root / f
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        dir_posix = str(Path(f).parent).replace("\\", "/")
        if dir_posix == ".":
            dir_posix = ""

        for m in JS_IMPORT_RE.finditer(content):
            specifier = m.group(1) or m.group(2) or m.group(3)
            if not specifier:
                continue

            specifier = specifier.strip()
            # We only care about relative imports or root-aliased imports
            if specifier.startswith(("./", "../")):
                joined = posixpath.normpath(posixpath.join(dir_posix, specifier))
            elif specifier.startswith(("@/", "~/")):
                joined = specifier[2:]
            else:
                # Could be a direct relative path like "components/Button"
                joined = specifier

            joined = joined.lstrip("./")

            # Check exact match
            matched_file: str | None = None
            if joined in files_set:
                matched_file = joined
            else:
                for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json"):
                    cand = joined + ext
                    if cand in files_set:
                        matched_file = cand
                        break

            if not matched_file:
                for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
                    cand_idx = f"{joined}/index{ext}"
                    if cand_idx in files_set:
                        matched_file = cand_idx
                        break

            # Also check if joined matches within src/
            if not matched_file and not joined.startswith("src/"):
                src_cand = f"src/{joined}"
                if src_cand in files_set:
                    matched_file = src_cand
                else:
                    for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json"):
                        cand = src_cand + ext
                        if cand in files_set:
                            matched_file = cand
                            break

            if matched_file and matched_file != f:
                edges.append((f, matched_file, "imports"))

    return normalize_edges(edges, files)


def extract_fallback_dependencies(
    root: Path, files: list[str]
) -> DependencyGraph:
    """Fallback extraction combining Python AST analysis and JS/TS regex parsing."""
    py_edges = extract_python_dependencies(root, files)
    js_edges = extract_js_ts_dependencies(root, files)
    combined = normalize_edges(py_edges + js_edges, files)
    metrics = compute_metrics(files, combined)
    hubs = detect_hubs(metrics, threshold=3)
    return DependencyGraph(edges=combined, hubs=hubs, metrics=metrics)


def extract_dependencies(
    root: Path,
    files: list[str],
    codemap_bin: str | None = "codemap",
) -> DependencyGraph:
    """Extracts dependency graph and topology metrics for codebase files.

    Runs `codemap --deps <root>` if available. If codemap is not found, fails,
    or yields no edges, falls back to Python AST and JS/TS regex analysis.
    Guaranteed never to crash on syntax errors or subprocess issues.
    """
    try:
        if codemap_bin and shutil.which(codemap_bin):
            try:
                proc = subprocess.run(
                    [codemap_bin, "--deps", str(root)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if proc.returncode == 0 and proc.stdout:
                    graph = parse_codemap_deps(proc.stdout, files)
                    if graph.edges:
                        return graph
            except (subprocess.SubprocessError, OSError, Exception):
                pass

        return extract_fallback_dependencies(root, files)
    except Exception:
        metrics = compute_metrics(files, [])
        return DependencyGraph(edges=[], hubs=[], metrics=metrics)
