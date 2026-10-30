# pyright: reportMissingImports=false
"""Understand glossary extraction, collision detection, and drafting (Step 6)."""

from .collisions import detect_collisions
from .draft import generate_glossary_draft
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
    "generate_glossary_draft",
]
