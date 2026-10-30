# pyright: reportMissingImports=false
"""Data models for glossary extraction, collision detection, and drafting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GlossaryTerm:
    """A single glossary term and its definition."""

    term: str
    meaning: str


@dataclass(frozen=True)
class GlossaryContext:
    """A bounded context containing glossary terms."""

    name: str
    terms: list[GlossaryTerm] = field(default_factory=list)


@dataclass(frozen=True)
class CollisionMeaning:
    """One meaning of a collided term in a specific bounded context."""

    context: str
    meaning: str


@dataclass(frozen=True)
class GlossaryCollision:
    """A term appearing in two or more contexts with differing meanings."""

    term: str
    meanings: list[CollisionMeaning] = field(default_factory=list)


@dataclass(frozen=True)
class GlossaryResult:
    """Complete glossary result for a repository report."""

    contexts: list[GlossaryContext] = field(default_factory=list)
    collisions: list[GlossaryCollision] = field(default_factory=list)
    draft: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        """Serializes to a schema-compatible glossary.json structure."""
        return {
            "contexts": [
                {
                    "name": ctx.name,
                    "terms": [
                        {"term": t.term, "meaning": t.meaning}
                        for t in ctx.terms
                    ],
                }
                for ctx in self.contexts
            ],
            "collisions": [
                {
                    "term": col.term,
                    "meanings": [
                        {"context": m.context, "meaning": m.meaning}
                        for m in col.meanings
                    ],
                }
                for col in self.collisions
            ],
            "draft": self.draft,
        }
