# pyright: reportMissingImports=false
"""Unit tests for glossary draft generation."""

from understand_glossary.draft import generate_glossary_draft
from understand_glossary.models import (
    CollisionMeaning,
    GlossaryCollision,
    GlossaryContext,
    GlossaryTerm,
)


def test_empty_contexts_generates_template_draft():
    draft = generate_glossary_draft([])
    assert "# Glossary" in draft
    assert "## " in draft
    assert "**" in draft


def test_contexts_formatted_into_markdown_draft():
    contexts = [
        GlossaryContext("billing", [
            GlossaryTerm("Invoice", "Bill sent to customer."),
            GlossaryTerm("Account", "Payer of invoices."),
        ]),
        GlossaryContext("identity", [
            GlossaryTerm("Account", "Login principal."),
        ]),
    ]
    draft = generate_glossary_draft(contexts)
    assert "# Glossary" in draft
    assert "## billing" in draft
    assert "**Invoice**" in draft
    assert "Bill sent to customer." in draft
    assert "## identity" in draft
    assert "**Account**" in draft
    assert "Login principal." in draft


def test_draft_includes_collisions_section_when_collisions_present():
    contexts = [
        GlossaryContext("billing", [GlossaryTerm("Account", "payer of invoices")]),
        GlossaryContext("identity", [GlossaryTerm("Account", "login principal")]),
    ]
    collisions = [
        GlossaryCollision(
            term="Account",
            meanings=[
                CollisionMeaning("billing", "payer of invoices"),
                CollisionMeaning("identity", "login principal"),
            ],
        )
    ]
    draft = generate_glossary_draft(contexts, collisions=collisions)
    assert "Collisions" in draft
    assert "Account" in draft
    assert "billing" in draft
    assert "identity" in draft
