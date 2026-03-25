import os
import pytest
from src.parser import OutlookParser

SNAPSHOT_DIR = os.path.expanduser("~/.gemini/skills/outlook-headless/scripts/tests/snapshots")

def get_snapshot(name):
    path = os.path.join(SNAPSHOT_DIR, name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None

def test_parse_item_0():
    text = get_snapshot("item_0.txt")
    if not text: pytest.skip("Snapshot not found")
    
    msg = OutlookParser.parse_list_item(text, 0)
    assert msg is not None
    assert msg.sender == "Doe, John"
    assert "moved a file" in msg.subject
    assert msg.timestamp == "Fri 3:16 PM"
    assert "Doe, John moved" in msg.body

def test_parse_item_1():
    text = get_snapshot("item_1.txt")
    if not text: pytest.skip("Snapshot not found")
    
    msg = OutlookParser.parse_list_item(text, 1)
    assert msg is not None
    assert msg.sender == "Smith, Jane"
    assert msg.subject == "Lunch :)"
    assert msg.timestamp == "Fri 1:09 PM"
    assert "No preview is available" in msg.body

def test_parse_item_3_myaccess():
    text = get_snapshot("item_3.txt")
    if not text: pytest.skip("Snapshot not found")
    
    msg = OutlookParser.parse_list_item(text, 3)
    assert msg is not None
    assert msg.sender == "AccessPortal (Do Not Reply)"
    assert "Request Submitted" in msg.subject
    assert msg.timestamp == "Fri 11:27 AM"

def test_parse_document_with_headers():
    doc_html = """<div>
From: Dattenny, Steve <steve.manager@example.com><br>
Sent: Thursday, March 5, 2026 11:13 PM<br>
To: Brown, Charlie (ext) <charlie.brown@example.com>; White, Bob <bob.white@example.com><br>
Subject: Re: CORPUNIT EHS: Alignment on S3 EventBridge Migration<br>
<br>
Hi Charlie,
This is the body content.
</div>"""
    msg = OutlookParser.parse_document(
        doc_html=doc_html, 
        message_id="id-123",
        sender="Dattenny, Steve <steve.manager@example.com>",
        subject="Re: CORPUNIT EHS: Alignment on S3 EventBridge Migration",
        timestamp="Thursday, March 5, 2026 11:13 PM",
        to=["Brown, Charlie (ext) <charlie.brown@example.com>", "White, Bob <bob.white@example.com>"]
    )
    assert msg.sender == "Dattenny, Steve <steve.manager@example.com>"
    assert msg.subject == "Re: CORPUNIT EHS: Alignment on S3 EventBridge Migration"
    assert msg.timestamp == "Thursday, March 5, 2026 11:13 PM"
    assert len(msg.to) == 2
    assert "Brown, Charlie" in msg.to[0]
    assert "White, Bob" in msg.to[1]
    assert "Hi Charlie" in msg.body
