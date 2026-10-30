# pyright: reportMissingImports=false
"""Unit tests for glossary term collision detection."""

from understand_glossary.collisions import detect_collisions
from understand_glossary.models import GlossaryContext, GlossaryTerm


def test_no_collision_when_terms_unique_across_contexts():
    contexts = [
        GlossaryContext("billing", [GlossaryTerm("Invoice", "A bill sent to a customer.")]),
        GlossaryContext("identity", [GlossaryTerm("User", "An authenticated person.")]),
    ]
    collisions = detect_collisions(contexts)
    assert collisions == []


def test_collision_detected_when_term_has_different_meanings_in_multiple_contexts():
    contexts = [
        GlossaryContext("billing", [
            GlossaryTerm("Account", "payer of invoices"),
        ]),
        GlossaryContext("identity", [
            GlossaryTerm("Account", "login principal"),
        ]),
    ]
    collisions = detect_collisions(contexts)
    assert len(collisions) == 1
    col = collisions[0]
    assert col.term == "Account"
    assert len(col.meanings) == 2
    contexts_found = {m.context: m.meaning for m in col.meanings}
    assert contexts_found == {
        "billing": "payer of invoices",
        "identity": "login principal",
    }


def test_collision_detection_is_case_insensitive():
    contexts = [
        GlossaryContext("billing", [
            GlossaryTerm("account", "payer of invoices"),
        ]),
        GlossaryContext("identity", [
            GlossaryTerm("Account", "login principal"),
        ]),
    ]
    collisions = detect_collisions(contexts)
    assert len(collisions) == 1
    assert collisions[0].term.lower() == "account"


def test_no_collision_when_meanings_are_identical():
    contexts = [
        GlossaryContext("billing", [
            GlossaryTerm("Tenant", "An isolated organization."),
        ]),
        GlossaryContext("identity", [
            GlossaryTerm("Tenant", "An isolated organization."),
        ]),
    ]
    collisions = detect_collisions(contexts)
    assert collisions == []


def test_collision_supports_three_or_more_contexts():
    contexts = [
        GlossaryContext("billing", [GlossaryTerm("Account", "payer of invoices")]),
        GlossaryContext("identity", [GlossaryTerm("Account", "login principal")]),
        GlossaryContext("crm", [GlossaryTerm("Account", "business relationship")]),
    ]
    collisions = detect_collisions(contexts)
    assert len(collisions) == 1
    assert len(collisions[0].meanings) == 3
