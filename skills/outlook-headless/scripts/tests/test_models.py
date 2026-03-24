from src.models import SearchCriteria, EmailMessage, EmailSearchResult

def test_search_criteria_query():
    sc = SearchCriteria(query="urgent")
    assert sc.to_outlook_query() == "urgent"

def test_search_criteria_sender():
    sc = SearchCriteria(from_sender="boss@example.com")
    assert sc.to_outlook_query() == "from:boss@example.com"

def test_search_criteria_subject():
    sc = SearchCriteria(subject="Project Update")
    assert sc.to_outlook_query() == "subject:\"Project Update\""

def test_search_criteria_date_range():
    sc = SearchCriteria(after="2024-01-01", before="2024-01-31")
    assert sc.to_outlook_query() == "received:2024-01-01..2024-01-31"

def test_search_criteria_combined():
    sc = SearchCriteria(
        query="report",
        from_sender="alice@example.com",
        unread_only=True
    )
    assert "report" in sc.to_outlook_query()
    assert "from:alice@example.com" in sc.to_outlook_query()
    assert "isread:no" in sc.to_outlook_query()

def test_email_message_model():
    msg = EmailMessage(
        subject="Hello",
        sender="bob@example.com",
        body="This is a test body"
    )
    assert msg.subject == "Hello"
    assert msg.sender == "bob@example.com"
    assert msg.body == "This is a test body"

def test_email_search_result_model():
    msg = EmailMessage(body="Test")
    result = EmailSearchResult(items=[msg], total_count=1)
    assert len(result.items) == 1
    assert result.total_count == 1
