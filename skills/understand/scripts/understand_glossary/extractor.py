# pyright: reportMissingImports=false
"""Bounded context and domain term extractor (Spec Unit 5)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .collisions import detect_collisions
from .draft import generate_glossary_draft
from .models import GlossaryContext, GlossaryResult, GlossaryTerm

IGNORED_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".cache",
    "tests",
    "test",
    "assets",
}

MAP_NAMES = [
    "GLOSSARY-MAP.md",
    "glossary-map.md",
    "GLOSSARY_MAP.md",
    "glossary_map.md",
    "GLOSSARY.md",
    "glossary.md",
    "glossary-map.json",
    "glossary.json",
]


def find_glossary_map(root: Path) -> Path | None:
    """Finds an existing glossary map or glossary file in root or docs/."""
    # 1. Check root
    for name in MAP_NAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate

    # 2. Check docs/
    docs = root / "docs"
    if docs.is_dir():
        for name in MAP_NAMES:
            candidate = docs / name
            if candidate.is_file():
                return candidate
        for curr, dirs, filenames in os.walk(docs):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in filenames:
                if f.upper() in {"GLOSSARY-MAP.MD", "GLOSSARY.MD", "GLOSSARY_MAP.MD"}:
                    return Path(curr) / f

    # 3. Recursive search (up to depth 2)
    for curr, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        rel = Path(curr).relative_to(root)
        if len(rel.parts) > 2:
            dirs.clear()
            continue
        for f in filenames:
            if f.upper() in {"GLOSSARY-MAP.MD", "GLOSSARY.MD"}:
                return Path(curr) / f

    return None


def parse_glossary_map(path: Path) -> list[GlossaryContext]:
    """Parses contexts and terms from a markdown or JSON glossary map file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        raw_contexts = data.get("contexts", [])
        result = []
        for c in raw_contexts:
            terms = [GlossaryTerm(t["term"], t["meaning"]) for t in c.get("terms", [])]
            result.append(GlossaryContext(c["name"], terms))
        return result

    # Markdown parsing
    lines = text.splitlines()
    contexts: list[GlossaryContext] = []
    current_context_name: str | None = None
    current_terms: list[GlossaryTerm] = []

    def flush_context():
        nonlocal current_context_name, current_terms
        if current_context_name:
            contexts.append(GlossaryContext(current_context_name, list(current_terms)))
            current_terms = []
            current_context_name = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Heading detection: e.g. ## billing or ### billing
        h_match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if h_match:
            heading_title = h_match.group(2).strip()
            # Skip document title if it's general
            if heading_title.lower() in {"glossary", "glossary map", "table of contents", "overview"}:
                i += 1
                continue

            # Strip leading "Context: " if present
            if heading_title.lower().startswith("context:"):
                heading_title = heading_title.split(":", 1)[1].strip()

            flush_context()
            current_context_name = heading_title
            i += 1
            continue

        # Term pattern: **Term**: Meaning or - **Term**: Meaning
        term_match = re.match(r"^(?:[-*]\s*)?\*\*([^*:]+)\*\*\s*[:\-]?\s*(.*)$", line)
        if term_match:
            term_name = term_match.group(1).strip()
            meaning_text = term_match.group(2).strip()
            # If meaning is empty, check next non-empty lines
            if not meaning_text:
                meaning_lines = []
                j = i + 1
                while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(("#", "**", "- **")):
                    meaning_lines.append(lines[j].strip())
                    j += 1
                meaning_text = " ".join(meaning_lines)
                i = j - 1

            if term_name and meaning_text:
                if not current_context_name:
                    current_context_name = "general"
                current_terms.append(GlossaryTerm(term_name, meaning_text))
            i += 1
            continue

        # Bullet term pattern: - Term: Meaning
        bullet_match = re.match(r"^[-*]\s+([A-Z][a-zA-Z0-9_]+)\s*[:\-]\s*(.+)$", line)
        if bullet_match:
            t_name = bullet_match.group(1).strip()
            t_meaning = bullet_match.group(2).strip()
            if not current_context_name:
                current_context_name = "general"
            current_terms.append(GlossaryTerm(t_name, t_meaning))
            i += 1
            continue

        i += 1

    flush_context()
    return contexts


def _extract_terms_from_code(content: str, context_name: str) -> list[GlossaryTerm]:
    """Extracts terms and meanings from source code comments, docstrings, and declarations."""
    terms: dict[str, str] = {}

    # 1. Comment definitions: // Term: meaning or # Term: meaning or /* Term - meaning */
    comment_pattern = re.compile(
        r"(?:/{2}|#|\*)\s*([A-Z][a-zA-Z0-9_]+)\s*[:\-]\s*([^\n\r]+)"
    )
    for m in comment_pattern.finditer(content):
        term = m.group(1).strip()
        meaning = m.group(2).strip()
        if term and meaning and len(meaning) > 3 and not meaning.startswith(("http", "eslint", "type:", "TODO")):
            terms[term] = meaning

    # 2. Class/interface docstrings:
    # class Account: """payer of invoices"""
    py_class = re.compile(
        r"class\s+([A-Z][a-zA-Z0-9_]+)(?:\([^)]*\))?\s*:\s*[\"']{3}([\s\S]*?)[\"']{3}"
    )
    for m in py_class.finditer(content):
        term = m.group(1).strip()
        doc = m.group(2).strip().splitlines()[0].strip()
        if term and doc and term not in terms:
            terms[term] = doc

    ts_class = re.compile(
        r"/\*\*([\s\S]*?)\*/\s*(?:export\s+)?(?:class|interface|type)\s+([A-Z][a-zA-Z0-9_]+)"
    )
    for m in ts_class.finditer(content):
        doc = m.group(1).replace("*", "").strip().splitlines()[0].strip()
        term = m.group(2).strip()
        if term and doc and term not in terms:
            terms[term] = doc

    # 3. Standalone class/interface exports
    declarations = re.compile(
        r"(?:export\s+)?(?:class|interface|type)\s+([A-Z][a-zA-Z0-9_]+)"
    )
    for m in declarations.finditer(content):
        term = m.group(1).strip()
        if term not in terms:
            terms[term] = f"Domain concept in {context_name}."

    return [GlossaryTerm(t, m) for t, m in sorted(terms.items())]


def infer_contexts_from_areas(root: Path) -> list[GlossaryContext]:
    """Infers bounded contexts heuristically from top-level modules/directories and domain terms."""
    areas: dict[str, list[Path]] = {}

    # Look for candidate areas in src/, lib/, or root
    candidates: list[Path] = []
    for prefix in ("src", "lib", "pkg", "services", "apps", "packages"):
        prefix_dir = root / prefix
        if prefix_dir.is_dir():
            for child in prefix_dir.iterdir():
                if child.is_dir() and child.name not in IGNORED_DIRS and not child.name.startswith("."):
                    candidates.append(child)

    # If no standard prefix dirs, use top-level dirs
    if not candidates:
        for child in root.iterdir():
            if child.is_dir() and child.name not in IGNORED_DIRS and not child.name.startswith("."):
                candidates.append(child)

    for area_dir in sorted(candidates):
        context_name = area_dir.name
        files: list[Path] = []
        for curr, dirs, filenames in os.walk(area_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in sorted(filenames):
                if not f.startswith("."):
                    files.append(Path(curr) / f)
        if files:
            areas[context_name] = files

    contexts: list[GlossaryContext] = []
    for ctx_name, files in sorted(areas.items()):
        all_terms: dict[str, str] = {}
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            if f.suffix in {".md", ".markdown"}:
                # Parse markdown definitions
                md_contexts = parse_glossary_map(f)
                for c in md_contexts:
                    for t in c.terms:
                        all_terms[t.term] = t.meaning
            else:
                code_terms = _extract_terms_from_code(content, ctx_name)
                for t in code_terms:
                    # Specific comments override fallback definitions
                    if t.term not in all_terms or "Domain concept in" in all_terms[t.term]:
                        all_terms[t.term] = t.meaning

        term_list = [GlossaryTerm(term, meaning) for term, meaning in sorted(all_terms.items())]
        contexts.append(GlossaryContext(ctx_name, term_list))

    return contexts


def extract_glossary(root: Path) -> GlossaryResult:
    """Extracts bounded contexts, detects term collisions, and drafts GLOSSARY.md."""
    map_file = find_glossary_map(root)
    if map_file is not None:
        contexts = parse_glossary_map(map_file)
    else:
        contexts = infer_contexts_from_areas(root)

    collisions = detect_collisions(contexts)
    draft = generate_glossary_draft(contexts, collisions)
    return GlossaryResult(contexts=contexts, collisions=collisions, draft=draft)
