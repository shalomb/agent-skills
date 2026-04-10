import os
import pytest
from src.parser import OutlookParser

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")


def get_snapshot(name):
    path = os.path.join(SNAPSHOT_DIR, name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None


def test_parse_single_forwarded_message():
    html = get_snapshot("forwarded_single.html")
    if not html:
        pytest.skip("Snapshot not found")

    messages = OutlookParser.parse_forwarded_chain(html, parent_id="0-5")
    assert len(messages) == 1
    msg = messages[0]
    assert "Neuber, Anton" in msg.sender
    assert "anton.neuber@vendor.com" in msg.sender
    assert "October 27, 2025" in msg.timestamp or "2025" in msg.timestamp
    assert "jack.ribinin@takeda.com" in str(msg.to)
    assert "LIP AWS Migration" in msg.subject
    assert "infrastructure requirements" in msg.body.lower()
    assert msg.id == "0-5-fwd-0"


def test_empty_body_returns_empty_list():
    html = "<div><p>Just a plain message with no forwarded content.</p></div>"
    messages = OutlookParser.parse_forwarded_chain(html)
    assert messages == []


def test_parse_chain_of_three():
    html = get_snapshot("forwarded_chain_3.html")
    if not html:
        pytest.skip("Snapshot not found")

    messages = OutlookParser.parse_forwarded_chain(html, parent_id="0-0")
    assert len(messages) == 3

    # Most recent first (top of chain)
    assert "Ribinin, Jack" in messages[0].sender
    assert "October 24, 2025" in messages[0].timestamp
    assert "Windows Server 2022" in messages[0].body

    assert "Neuber, Anton" in messages[1].sender
    assert "October 22, 2025" in messages[1].timestamp
    assert "$700/month" in messages[1].body

    assert "Krejci, Iris" in messages[2].sender
    assert "October 20, 2025" in messages[2].timestamp
    assert "budget approval" in messages[2].body

    # Each should have a distinct body
    bodies = [m.body for m in messages]
    assert len(set(bodies)) == 3

    # IDs should be sequential
    assert messages[0].id == "0-0-fwd-0"
    assert messages[1].id == "0-0-fwd-1"
    assert messages[2].id == "0-0-fwd-2"


def test_parse_regex_fallback_no_divrplyfwdmsg():
    """When there are no divRplyFwdMsg markers, fall back to regex header splitting."""
    html = get_snapshot("forwarded_regex_chain.html")
    if not html:
        pytest.skip("Snapshot not found")

    messages = OutlookParser.parse_forwarded_chain(html, parent_id="1-0")
    assert len(messages) == 2

    assert "Ribinin, Jack" in messages[0].sender
    assert "October 24, 2025" in messages[0].timestamp
    assert "Budget approved" in messages[0].body

    assert "Neuber, Anton" in messages[1].sender
    assert "October 22, 2025" in messages[1].timestamp
    assert "EUR 8,400" in messages[1].body

    assert messages[0].id == "1-0-fwd-0"
    assert messages[1].id == "1-0-fwd-1"


def test_parse_deep_chain_of_ten():
    html = get_snapshot("forwarded_chain_10.html")
    if not html:
        pytest.skip("Snapshot not found")

    messages = OutlookParser.parse_forwarded_chain(html, parent_id="0-0")
    assert len(messages) == 10

    # First message (most recent in chain)
    assert "Ribinin, Jack" in messages[0].sender
    assert "Deployment starts" in messages[0].body

    # Last message (oldest — Anton's initial proposal)
    assert "Neuber, Anton" in messages[9].sender
    assert "initial infrastructure proposal" in messages[9].body

    # All bodies should be distinct
    bodies = [m.body for m in messages]
    assert len(set(bodies)) == 10

    # Multilingual headers (message 8 uses French: De/Envoyé/À/Objet)
    assert "Dattenny" in messages[7].sender
    assert "cutover window" in messages[7].body
    assert messages[7].timestamp  # Should have parsed "mardi 21 octobre 2025 16:45"


def test_multilingual_headers_inline():
    """Test French headers parsed correctly."""
    html = """<div>
    <div id="divRplyFwdMsg">
    <b>De :</b> Dupont, Marie &lt;marie@example.fr&gt;<br>
    <b>Envoyé :</b> lundi 15 mars 2026 14:30<br>
    <b>À :</b> Équipe &lt;equipe@example.fr&gt;<br>
    <b>Objet :</b> Mise à jour du projet<br>
    </div>
    <p>Bonjour, voici la mise à jour.</p>
    </div>"""
    messages = OutlookParser.parse_forwarded_chain(html)
    assert len(messages) == 1
    assert "Dupont, Marie" in messages[0].sender
    assert "mars 2026" in messages[0].timestamp
    assert "Mise à jour" in messages[0].subject


def test_body_content_between_headers_extracted():
    """Body text between two forwarded header blocks should be captured."""
    html = get_snapshot("forwarded_chain_3.html")
    if not html:
        pytest.skip("Snapshot not found")

    messages = OutlookParser.parse_forwarded_chain(html)
    # Each message should have substantive body content
    for msg in messages:
        assert len(msg.body.strip()) > 10, f"Message {msg.id} has too-short body: {msg.body!r}"


def test_partial_headers_handled_gracefully():
    """Forwarded block missing Subject: line should still parse."""
    html = """<div>
    <div id="divRplyFwdMsg">
    <b>From:</b> Smith, Jane &lt;jane@example.com&gt;<br>
    <b>Sent:</b> Tuesday, March 3, 2026 9:00 AM<br>
    <b>To:</b> Team &lt;team@example.com&gt;<br>
    </div>
    <p>Please review the attached document.</p>
    </div>"""
    messages = OutlookParser.parse_forwarded_chain(html)
    assert len(messages) == 1
    assert "Smith, Jane" in messages[0].sender
    assert messages[0].subject is None or messages[0].subject == ""
    assert "review" in messages[0].body.lower()
