"""Pytest configuration and shared fixtures for Harness IDP skill tests."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def harness_credentials():
    """Valid Harness credentials for testing."""
    return {
        "account_id": "test-account-123",
        "api_key": "test-api-key-xyz",
    }


@pytest.fixture
def mock_task():
    """Mock Harness task object."""
    task = MagicMock()
    task.id = "task-abc123def456"
    task.status = "processing"
    task.spec = {}
    task.created_at = "2025-03-09T16:00:00Z"
    task.created_by = "user@example.com"
    task.is_terminal = MagicMock(return_value=False)
    task.is_success = MagicMock(return_value=False)
    return task


@pytest.fixture
def mock_completed_task(mock_task):
    """Mock completed Harness task."""
    completed = MagicMock(**vars(mock_task))
    completed.status = "completed"
    completed.spec = {
        "output": {
            "resultLink": "https://app.terraform.io/app/org/workspaces/my-workspace"
        }
    }
    completed.is_terminal = MagicMock(return_value=True)
    completed.is_success = MagicMock(return_value=True)
    return completed


@pytest.fixture
def mock_failed_task(mock_task):
    """Mock failed Harness task."""
    failed = MagicMock(**vars(mock_task))
    failed.status = "failed"
    failed.spec = {
        "error": {
            "message": "Repository already exists"
        }
    }
    failed.is_terminal = MagicMock(return_value=True)
    failed.is_success = MagicMock(return_value=False)
    return failed
