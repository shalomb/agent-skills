# pyright: reportMissingImports=false
"""Glossary draft generation for repository reports."""

from __future__ import annotations

from .models import GlossaryCollision, GlossaryContext


def generate_glossary_draft(
    contexts: list[GlossaryContext],
    collisions: list[GlossaryCollision] | None = None,
) -> str:
    """Generates a clean Markdown glossary draft that the user can apply as GLOSSARY.md."""
    lines: list[str] = ["# Glossary\n"]

    valid_contexts = [c for c in contexts if c.terms]
    if not valid_contexts:
        lines.append(
            "## domain\n\n"
            "**Term**:\n"
            "Definition of term.\n"
        )
        return "\n".join(lines).strip() + "\n"

    for ctx in valid_contexts:
        lines.append(f"## {ctx.name}\n")
        for t in ctx.terms:
            lines.append(f"**{t.term}**:\n{t.meaning}\n")

    if collisions:
        lines.append("## Collisions\n")
        for col in collisions:
            contexts_str = ", ".join(f'"{m.context}" ({m.meaning})' for m in col.meanings)
            lines.append(f"- **{col.term}**: multiple meanings in {contexts_str}\n")

    return "\n".join(lines).strip() + "\n"
