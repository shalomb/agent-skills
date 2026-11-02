# pyright: reportMissingImports=false
"""Architectural Synthesizer and C4 Generator module for /understand."""

from __future__ import annotations

from .c4 import (
    generate_c4_container,
    generate_c4_context,
)
from .sections import (
    format_file_citation,
    synthesize_sections,
)

__all__ = [
    "format_file_citation",
    "generate_c4_container",
    "generate_c4_context",
    "synthesize_sections",
]
