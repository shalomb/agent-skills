"""Unit tests for Harness IDP Scaffolder API client."""

import pytest
import os
from unittest.mock import MagicMock, patch, ANY
import requests
import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from harness_idp_client import (
    HarnessScaffolderClient,
    Task,
    TaskStatus,
)


class TestTaskStatus:
    """Test TaskStatus enumeration."""

    def test_status_values(self):
        """Verify TaskStatus enum values."""
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTask:
    """Test Task data class."""

    def test_task_creation(self):
        """Create a task instance."""
        task = Task(id="task-123", spec={"key": "value"}, status="processing")
        assert task.id == "task-123"
        assert task.spec == {"key": "value"}
        assert task.status == "processing"

    def test_is_terminal_false_on_processing(self):
        """Task in processing state is not terminal."""
        task = Task(id="task-123", spec={}, status="processing")
        assert task.is_terminal() is False

    def test_is_terminal_true_on_completed(self):
        """Task in completed state is terminal."""
        task = Task(id="task-123", spec={}, status="completed")
        assert task.is_terminal() is True

    def test_is_terminal_true_on_failed(self):
        """Task in failed state is terminal."""
        task = Task(id="task-123", spec={}, status="failed")
        assert task.is_terminal() is True

    def test_is_terminal_true_on_cancelled(self):
        """Task in cancelled state is terminal."""
        task = Task(id="task-123", spec={}, status="cancelled")
        assert task.is_terminal() is True

    def test_is_success_true_on_completed(self):
        """Task is successful only when completed."""
        task = Task(id="task-123", spec={}, status="completed")
        assert task.is_success() is True

    def test_is_success_false_on_failed(self):
        """Task is not successful when failed."""
        task = Task(id="task-123", spec={}, status="failed")
        assert task.is_success() is False

    def test_is_success_false_on_processing(self):
        """Task is not successful when still processing."""
        task = Task(id="task-123", spec={}, status="processing")
        assert task.is_success() is False


class TestHarnessScaffolderClientInit:
    """Test HarnessScaffolderClient initialization."""

    def test_init_with_explicit_credentials(self):
        """Initialize with explicit credentials."""
        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )
        assert client.account_id == "account-123"
        assert client.api_key == "key-xyz"

    def test_init_with_env_vars(self):
        """Initialize using environment variables."""
        with patch.dict(
            os.environ,
            {
                "HARNESS_ACCOUNT_ID": "account-env",
                "HARNESS_API_KEY": "key-env",
            },
        ):
            client = HarnessScaffolderClient()
            assert client.account_id == "account-env"
            assert client.api_key == "key-env"

    def test_init_missing_account_id_raises(self):
        """Initialization fails if account_id is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HARNESS_ACCOUNT_ID"):
                HarnessScaffolderClient(api_key="key-xyz")

    def test_init_missing_api_key_raises(self):
        """Initialization fails if api_key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HARNESS_API_KEY"):
                HarnessScaffolderClient(account_id="account-123")

    def test_custom_base_url(self):
        """Initialize with custom base URL."""
        client = HarnessScaffolderClient(
            account_id="account-123",
            api_key="key-xyz",
            base_url="https://harness.example.com",
        )
        assert client.base_url == "https://harness.example.com"


class TestHarnessScaffolderClientCreateTask:
    """Test task creation."""

    @patch("harness_idp_client.requests.Session.post")
    def test_create_task_success(self, mock_post):
        """Create task successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "task-abc123"}
        mock_post.return_value = mock_response

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        task = client.create_task(
            template_ref="template:account/MyTemplate",
            values={"param1": "value1"},
        )

        assert task.id == "task-abc123"
        assert task.status == "processing"
        mock_post.assert_called_once()

    @patch("harness_idp_client.requests.Session.post")
    def test_create_task_with_secrets(self, mock_post):
        """Create task with sensitive parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "task-xyz789"}
        mock_post.return_value = mock_response

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        task = client.create_task(
            template_ref="template:account/MyTemplate",
            values={"param1": "value1"},
            secrets={"api_token": "secret-token"},
        )

        assert task.id == "task-xyz789"
        # Verify secrets were passed
        call_args = mock_post.call_args
        assert call_args[1]["json"]["secrets"] == {"api_token": "secret-token"}

    def test_create_task_missing_template_ref_raises(self):
        """Create task fails if template_ref is missing."""
        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(ValueError, match="template_ref"):
            client.create_task(template_ref="", values={"param": "value"})

    def test_create_task_missing_values_raises(self):
        """Create task fails if values is empty."""
        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(ValueError, match="values"):
            client.create_task(template_ref="template:account/Foo", values={})

    @patch("harness_idp_client.requests.Session.post")
    def test_create_task_unauthorized(self, mock_post):
        """Create task fails with 401 Unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="bad-key"
        )

        with pytest.raises(ValueError, match="Unauthorized"):
            client.create_task(
                template_ref="template:account/Foo", values={"p": "v"}
            )

    @patch("harness_idp_client.requests.Session.post")
    def test_create_task_invalid_parameters(self, mock_post):
        """Create task fails with 422 Unprocessable Entity."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "message": "Invalid parameter: param1"
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(ValueError, match="Invalid parameters"):
            client.create_task(
                template_ref="template:account/Foo", values={"param1": "bad"}
            )


class TestHarnessScaffolderClientGetTask:
    """Test task retrieval."""

    @patch("harness_idp_client.requests.Session.get")
    def test_get_task_success(self, mock_get):
        """Get task successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "task-abc123",
            "status": "processing",
            "spec": {"key": "value"},
            "createdAt": "2025-03-09T16:00:00Z",
        }
        mock_get.return_value = mock_response

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        task = client.get_task("task-abc123")

        assert task.id == "task-abc123"
        assert task.status == "processing"
        assert task.spec == {"key": "value"}
        mock_get.assert_called_once()

    @patch("harness_idp_client.requests.Session.get")
    def test_get_task_not_found(self, mock_get):
        """Get task fails if task doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(ValueError, match="Task not found"):
            client.get_task("nonexistent-task")

    def test_get_task_missing_id_raises(self):
        """Get task fails if task_id is missing."""
        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(ValueError, match="task_id"):
            client.get_task("")


class TestHarnessScaffolderClientPollTask:
    """Test task polling."""

    @patch("harness_idp_client.requests.Session.get")
    @patch("harness_idp_client.time.sleep")
    def test_poll_task_success(self, mock_sleep, mock_get):
        """Poll task until completion."""
        # First call returns processing, second returns completed
        processing_response = MagicMock()
        processing_response.json.return_value = {
            "id": "task-abc123",
            "status": "processing",
            "spec": {},
        }

        completed_response = MagicMock()
        completed_response.json.return_value = {
            "id": "task-abc123",
            "status": "completed",
            "spec": {"output": "success"},
        }

        mock_get.side_effect = [processing_response, completed_response]

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        task = client.poll_task("task-abc123", poll_interval=1, timeout=10)

        assert task.id == "task-abc123"
        assert task.status == "completed"
        assert task.is_success() is True
        mock_sleep.assert_called()

    @patch("harness_idp_client.requests.Session.get")
    @patch("harness_idp_client.time.time")
    def test_poll_task_timeout(self, mock_time, mock_get):
        """Poll task times out."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "task-abc123",
            "status": "processing",
            "spec": {},
        }
        mock_get.return_value = mock_response

        # Simulate time progression
        mock_time.side_effect = [0, 5, 10, 15]

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(TimeoutError):
            client.poll_task("task-abc123", poll_interval=1, timeout=10)

    def test_poll_task_missing_id_raises(self):
        """Poll task fails if task_id is missing."""
        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        with pytest.raises(ValueError, match="task_id"):
            client.poll_task("")

    @patch("harness_idp_client.requests.Session.get")
    @patch("harness_idp_client.time.sleep")
    def test_poll_task_with_callback(self, mock_sleep, mock_get):
        """Poll task with callback function."""
        completed_response = MagicMock()
        completed_response.json.return_value = {
            "id": "task-abc123",
            "status": "completed",
            "spec": {},
        }
        mock_get.return_value = completed_response

        callback = MagicMock()

        client = HarnessScaffolderClient(
            account_id="account-123", api_key="key-xyz"
        )

        task = client.poll_task(
            "task-abc123", poll_interval=1, timeout=10, callback=callback
        )

        callback.assert_called()
        assert task.is_success() is True



