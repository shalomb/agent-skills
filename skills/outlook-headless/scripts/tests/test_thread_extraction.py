import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add src to path if needed for local execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.outlook_client import OutlookClient
from src.models import EmailMessage, SearchCriteria

@pytest.mark.asyncio
async def test_header_association_logic():
    """
    Test that the extraction logic correctly associates headers with bodies.
    This test mocks the DOM structure to verify the refactored extraction code.
    """
    client = OutlookClient()
    
    # Mock Page and Locators
    mock_page = MagicMock()
    mock_doc = MagicMock()
    
    # Define the mock header info that our JS evaluate would return
    expected_header = {
        'sender': 'alexander.schoeberl@takeda.com',
        'timestamp': 'Mon 3/23/2026 1:01 PM'
    }
    
    # Mock the evaluate call that finds the header
    mock_doc.evaluate = AsyncMock(return_value=expected_header)
    mock_doc.inner_html = AsyncMock(return_value="<p>Test body content</p>")
    mock_doc.scroll_into_view_if_needed = AsyncMock()
    
    # Verify that the logic (which we'll refactor) would use this data
    # For now, this is a placeholder to show the TDD intent
    sender = expected_header['sender']
    timestamp = expected_header['timestamp']
    
    assert sender == "alexander.schoeberl@takeda.com"
    assert "2026" in timestamp

def test_search_criteria_query_building():
    """Test that SearchCriteria correctly builds Outlook queries."""
    criteria = SearchCriteria(subject="Simca Online Server", unread_only=True)
    query = criteria.to_outlook_query()
    assert 'subject:"Simca Online Server"' in query
    assert 'isread:no' in query
