# pyright: reportMissingImports=false
"""Understand glossary extraction, collision detection, and drafting (Step 6)."""

from .collisions import detect_collisions
from .draft import generate_glossary_draft
from .extractor import (
    extract_glossary,
    find_glossary_map,
    infer_contexts_from_areas,
    parse_glossary_map,
)
from .models import (
    CollisionMeaning,
    GlossaryCollision,
    GlossaryContext,
    GlossaryResult,
    GlossaryTerm,
)

__all__ = [
    "CollisionMeaning",
    "GlossaryCollision",
    "GlossaryContext",
    "GlossaryResult",
    "GlossaryTerm",
    "detect_collisions",
    "extract_glossary",
    "find_glossary_map",
    "generate_glossary_draft",
    "infer_contexts_from_areas",
    "parse_glossary_map",
]
