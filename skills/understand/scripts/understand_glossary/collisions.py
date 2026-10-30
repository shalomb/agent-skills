# pyright: reportMissingImports=false
"""Collision detection across bounded contexts."""

from __future__ import annotations

from .models import CollisionMeaning, GlossaryCollision, GlossaryContext


def detect_collisions(contexts: list[GlossaryContext]) -> list[GlossaryCollision]:
    """Finds terms that appear in two or more contexts with differing meanings."""
    term_occurrences: dict[str, list[tuple[str, str, str]]] = {}
    for ctx in contexts:
        for t in ctx.terms:
            key = t.term.strip().lower()
            if not key:
                continue
            term_occurrences.setdefault(key, []).append((ctx.name, t.term.strip(), t.meaning.strip()))

    collisions: list[GlossaryCollision] = []
    for _, occurrences in sorted(term_occurrences.items()):
        contexts_seen = {ctx_name for ctx_name, _, _ in occurrences}
        if len(contexts_seen) < 2:
            continue

        meanings_set = {meaning for _, _, meaning in occurrences}
        if len(meanings_set) <= 1:
            continue

        canonical_term = occurrences[0][1]

        meanings_list: list[CollisionMeaning] = []
        seen_ctx: set[str] = set()
        for ctx_name, _, meaning in occurrences:
            if ctx_name not in seen_ctx:
                seen_ctx.add(ctx_name)
                meanings_list.append(CollisionMeaning(context=ctx_name, meaning=meaning))

        collisions.append(GlossaryCollision(term=canonical_term, meanings=meanings_list))

    return collisions
