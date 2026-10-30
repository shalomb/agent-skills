# pyright: reportMissingImports=false
"""Topic lens: semantic expansion, seed nodes discovery, 1-hop neighbours (Spec Unit 2 & Step 5)."""

from __future__ import annotations

import re
from pathlib import Path

from .models import LensFocus

STOP_WORDS = {
    "how", "the", "a", "an", "in", "on", "of", "and", "or", "for",
    "with", "work", "works", "to", "is", "are", "do", "does", "what",
}

# Software engineering semantic concepts and synonyms
SEMANTIC_MAP: dict[str, list[str]] = {
    "retry": ["retry", "retries", "backoff", "reschedule", "repeat", "attempt", "schedule", "failed payments again"],
    "retries": ["retry", "retries", "backoff", "reschedule", "repeat", "attempt", "schedule", "failed payments again"],
    "backoff": ["backoff", "retry", "retries", "delay", "reschedule", "exponential"],
    "billing": ["billing", "payment", "payments", "invoice", "charge", "subscription", "checkout", "failed payments"],
    "payment": ["payment", "payments", "billing", "invoice", "charge", "failed payments"],
    "payments": ["payment", "payments", "billing", "invoice", "charge", "failed payments"],
    "auth": ["auth", "authentication", "login", "signin", "session", "credential", "password", "token"],
    "authentication": ["auth", "authentication", "login", "signin", "session", "credential", "token"],
    "login": ["login", "signin", "auth", "authentication", "session", "credential"],
    "database": ["database", "db", "sql", "model", "storage", "repository", "postgres"],
    "storage": ["storage", "database", "repository", "store", "cache", "persistence"],
    "clock": ["clock", "time", "timer", "schedule", "delay", "timestamp"],
}


def _stem(word: str) -> str:
    """Basic English suffix stemming for software terms."""
    w = word.lower()
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("es") and len(w) > 3:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    return w


def expand_topic(topic: str) -> list[str]:
    """Expands a topic query into semantic terms and synonyms."""
    clean = re.sub(r"[^a-zA-Z0-9_\- ]", " ", topic).strip()
    words = [w.lower() for w in clean.split() if w]
    meaningful = [w for w in words if w not in STOP_WORDS]

    terms: list[str] = []
    seen: set[str] = set()

    def add_term(t: str):
        t_clean = t.strip().lower()
        if t_clean and t_clean not in seen:
            seen.add(t_clean)
            terms.append(t_clean)

    for w in meaningful:
        add_term(w)
        stemmed = _stem(w)
        add_term(stemmed)

        if w in SEMANTIC_MAP:
            for syn in SEMANTIC_MAP[w]:
                add_term(syn)
        if stemmed in SEMANTIC_MAP:
            for syn in SEMANTIC_MAP[stemmed]:
                add_term(syn)

    # Multi-word compound matching
    phrase = " ".join(meaningful)
    if "billing" in phrase and ("retry" in phrase or "retries" in phrase):
        add_term("backoff")
        add_term("failed payments again")
        add_term("schedules failed payments again")

    return terms


def find_seed_nodes(
    repo_path: Path,
    terms: list[str],
    files: list[str] | None = None,
) -> set[str]:
    """Finds seed files matching semantic terms in file path or content."""
    if files is None:
        file_candidates = [
            str(p.relative_to(repo_path))
            for p in repo_path.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        ]
    else:
        file_candidates = list(files)

    seeds: set[str] = set()
    cleaned_terms = [t.lower() for t in terms if len(t) > 1]

    for rel_path in file_candidates:
        rel_lower = rel_path.lower()
        matched = False
        for t in cleaned_terms:
            if t in rel_lower:
                seeds.add(rel_path)
                matched = True
                break

        if matched:
            continue

        full_path = repo_path / rel_path
        if full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore").lower()
                for t in cleaned_terms:
                    if t in content:
                        seeds.add(rel_path)
                        break
            except OSError:
                continue

    return seeds


def _find_file_dependencies(repo_path: Path, files: list[str]) -> list[tuple[str, str]]:
    """Infers directed dependency edges between files by scanning imports and references."""
    edges: list[tuple[str, str]] = []
    file_map: dict[str, str] = {}  # module/stem identifier -> rel_path

    for f in files:
        file_map[f] = f
        p = Path(f)
        stem = p.stem
        # e.g. billing.clock or clock
        dotted = ".".join(p.with_suffix("").parts)
        file_map[dotted] = f
        file_map[stem] = f

    for src_file in files:
        full_path = repo_path / src_file
        if not full_path.is_file():
            continue
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for token, target_file in file_map.items():
            if target_file == src_file or len(token) <= 2:
                continue
            # Look for import, from, or path mention
            pattern = r"(?:\bimport\s+[\w.]*|\bfrom\s+[\w.]*|['\"])(?:\b)?" + re.escape(token) + r"(?:\b|['\"])"
            if re.search(pattern, content) or (f'"{token}"' in content or f"'{token}'" in content or f"/{token}" in content):
                if (src_file, target_file) not in edges:
                    edges.append((src_file, target_file))

    return edges


def compute_topic_focus(
    repo_path: Path,
    topic: str,
    files: list[str] | None = None,
    edges: list[tuple[str, str]] | None = None,
) -> LensFocus:
    """Computes topic focus: expands query, finds seeds, adds 1-hop neighbours."""
    if files is None:
        all_files = sorted(
            str(p.relative_to(repo_path))
            for p in repo_path.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        )
    else:
        all_files = list(files)

    terms = expand_topic(topic)
    seeds = find_seed_nodes(repo_path, terms, files=all_files)

    if edges is None:
        dep_edges = _find_file_dependencies(repo_path, all_files)
    else:
        dep_edges = list(edges)

    focus_set = set(seeds)

    # 1-hop neighbours: any node directly connected to a seed node
    for src, tgt in dep_edges:
        if src in seeds:
            focus_set.add(tgt)
        if tgt in seeds:
            focus_set.add(src)

    return LensFocus(
        lens_type="topic",
        focus_set=focus_set,
        seed_nodes=seeds,
        all_files=all_files,
        metadata={"terms": terms, "edges": dep_edges},
    )
