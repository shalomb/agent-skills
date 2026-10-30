# pyright: reportMissingImports=false
"""Unit tests for renderer glossary collisions and draft rendering."""

from understand_render.bundle import Bundle, GlossaryContext, GlossaryTerm
from understand_render.report import render_report


def _make_bundle(glossary_contexts):
    return Bundle(
        title="Test Report",
        nodes=[],
        edges=[],
        sections=[],
        glossary_contexts=glossary_contexts,
        extra_anchors={},
    )


def test_renderer_flags_collision_with_links_to_each_meaning():
    contexts = [
        GlossaryContext("billing", [GlossaryTerm("Account", "payer of invoices")]),
        GlossaryContext("identity", [GlossaryTerm("Account", "login principal")]),
    ]
    bundle = _make_bundle(contexts)
    html = render_report(
        bundle,
        diagram=lambda s: "",
        rewrite_link=lambda link: link,
        uses_in_page_mermaid=lambda: False,
    )
    glossary = html.split('id="glossary"', 1)[1].split("</section>", 1)[0]

    # Flagged as collision
    assert "collision" in glossary.lower()
    assert "Account" in glossary

    # Has links to each meaning
    assert 'href="#term-billing-account"' in glossary or 'href="#glossary-billing-account"' in glossary
    assert 'href="#term-identity-account"' in glossary or 'href="#glossary-identity-account"' in glossary

    # Meanings are present
    assert "payer of invoices" in glossary
    assert "login principal" in glossary


def test_renderer_offers_glossary_draft():
    contexts = [
        GlossaryContext("billing", [GlossaryTerm("Invoice", "Bill sent to customer")]),
    ]
    bundle = _make_bundle(contexts)
    html = render_report(
        bundle,
        diagram=lambda s: "",
        rewrite_link=lambda link: link,
        uses_in_page_mermaid=lambda: False,
    )
    glossary = html.split('id="glossary"', 1)[1].split("</section>", 1)[0]
    assert "draft" in glossary.lower()
    assert "GLOSSARY.md" in glossary or "# Glossary" in glossary
    assert "billing" in glossary
    assert "Invoice" in glossary
