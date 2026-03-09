#!/usr/bin/env python3
"""
Harness IDP Scaffolder v2 API Client

Programmatic access to Harness.io IDP Scaffolder workflows.
Supports task creation, status polling, event streaming, and error handling.

Usage:
    from harness_idp_client import HarnessScaffolderClient

    client = HarnessScaffolderClient(
        account_id="your-account-id",
        api_key="your-api-key"
    )

    # Create task
    task = client.create_task(
        template_ref="template:account/MyTemplate",
        values={"param": "value"}
    )

    # Poll until complete
    final_task = client.poll_task(task.id)
    if final_task.is_success():
        print("Success!")
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, Iterator
from urllib.parse import urljoin
from enum import Enum
from dataclasses import dataclass


class TaskStatus(str, Enum):
    """Task execution status enumeration."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Scaffolder task representation."""

    id: str
    spec: Dict[str, Any]
    status: str = TaskStatus.PROCESSING.value
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    last_heartbeat_at: Optional[str] = None

    def is_terminal(self) -> bool:
        """Check if task has reached terminal state."""
        return self.status in (
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.CANCELLED.value,
        )

    def is_success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED.value

    def __repr__(self) -> str:
        return f"Task(id={self.id}, status={self.status})"


class HarnessScaffolderClient:
    """HTTP client for Harness IDP Scaffolder v2 API."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://idp.harness.io",
    ):
        """Initialize Harness API client.

        Args:
            account_id: Harness account ID (defaults to HARNESS_ACCOUNT_ID env var)
            api_key: Harness API key (defaults to HARNESS_API_KEY env var)
            base_url: Base URL for Harness API (default: https://idp.harness.io)

        Raises:
            ValueError: If credentials are not provided
        """
        self.account_id = account_id or os.environ.get("HARNESS_ACCOUNT_ID")
        self.api_key = api_key or os.environ.get("HARNESS_API_KEY")

        if not self.account_id:
            raise ValueError(
                "HARNESS_ACCOUNT_ID not found. "
                "Set via environment variable or parameter."
            )
        if not self.api_key:
            raise ValueError(
                "HARNESS_API_KEY not found. "
                "Set via environment variable or parameter."
            )

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        })

    def _build_url(self, path: str) -> str:
        """Build full API URL.

        Args:
            path: API path (e.g., "/idp/api/scaffolder/v2/tasks")

        Returns:
            Full URL with account ID included
        """
        account_path = f"/{self.account_id}"
        if not path.startswith("/"):
            path = "/" + path
        return urljoin(self.base_url, account_path + path)

    def create_task(
        self,
        template_ref: str,
        values: Dict[str, Any],
        secrets: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Create a scaffolder task.

        Args:
            template_ref: Template reference (e.g., "template:account/TemplateNameV3")
            values: Parameter values for the template
            secrets: Optional sensitive parameters (not logged)

        Returns:
            Task object with task ID

        Raises:
            requests.RequestException: If API call fails
            ValueError: If template_ref or values is invalid
        """
        if not template_ref:
            raise ValueError("template_ref is required")
        if not values:
            raise ValueError("values dict is required")

        url = self._build_url("/idp/api/scaffolder/v2/tasks")

        payload = {
            "templateRef": template_ref,
            "values": values,
            "secrets": secrets or {},
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError(
                    "401 Unauthorized: Check HARNESS_ACCOUNT_ID and HARNESS_API_KEY"
                ) from e
            elif response.status_code == 422:
                try:
                    error_body = response.json()
                    error_msg = error_body.get("message", str(error_body))
                except Exception:
                    error_msg = response.text[:200]
                raise ValueError(f"Invalid parameters: {error_msg}") from e
            else:
                raise

        data = response.json()
        return Task(id=data["id"], spec={}, status=TaskStatus.PROCESSING.value)

    def get_task(self, task_id: str) -> Task:
        """Get task status and details.

        Args:
            task_id: Task UUID

        Returns:
            Task object with current status and spec

        Raises:
            requests.RequestException: If API call fails
            ValueError: If task doesn't exist
        """
        if not task_id:
            raise ValueError("task_id is required")

        url = self._build_url(f"/idp/api/scaffolder/v2/tasks/{task_id}")

        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError(
                    "401 Unauthorized: Check HARNESS_API_KEY"
                ) from e
            elif response.status_code == 404:
                raise ValueError(f"Task not found: {task_id}") from e
            else:
                raise

        data = response.json()
        return Task(
            id=data["id"],
            spec=data.get("spec", {}),
            status=data.get("status", TaskStatus.PROCESSING.value),
            created_at=data.get("createdAt"),
            created_by=data.get("createdBy"),
            last_heartbeat_at=data.get("lastHeartbeatAt"),
        )

    def stream_events(self, task_id: str) -> Iterator[Dict[str, Any]]:
        """Stream task events via Server-Sent Events.

        Args:
            task_id: Task UUID

        Yields:
            Event dictionaries as they arrive

        Raises:
            requests.RequestException: If connection fails
            ValueError: If task_id is invalid
        """
        if not task_id:
            raise ValueError("task_id is required")

        url = self._build_url(f"/idp/api/scaffolder/v2/tasks/{task_id}/eventstream")

        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"Task not found: {task_id}") from e
            raise

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8") if isinstance(line, bytes) else line

            # Parse SSE format: data: {json}
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                try:
                    yield json.loads(data_str)
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    pass

    def poll_task(
        self,
        task_id: str,
        poll_interval: int = 2,
        timeout: int = 3600,
        callback=None,
    ) -> Task:
        """Poll task until completion.

        Args:
            task_id: Task UUID
            poll_interval: Seconds between API calls (default: 2)
            timeout: Maximum seconds to wait (default: 3600 = 1 hour)
            callback: Optional callback function called after each poll.
                     Signature: callback(task: Task) -> None

        Returns:
            Final task in terminal state (COMPLETED, FAILED, or CANCELLED)

        Raises:
            TimeoutError: If task doesn't complete within timeout
            requests.RequestException: If API calls fail
            ValueError: If task_id is invalid
        """
        if not task_id:
            raise ValueError("task_id is required")

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout} seconds"
                )

            try:
                task = self.get_task(task_id)
            except Exception as e:
                # Retry on transient errors
                time.sleep(poll_interval)
                continue

            if callback:
                try:
                    callback(task)
                except Exception:
                    # Prevent callback errors from breaking polling
                    pass

            if task.is_terminal():
                return task

            time.sleep(poll_interval)


# Note: Template parameters are org-specific.
# Customize parameter validation based on your template schemas.


if __name__ == "__main__":
    # Quick test
    import sys

    if len(sys.argv) < 3:
        print("Usage: python harness_idp_client.py <account_id> <task_id> [get|poll]")
        print("")
        print("Examples:")
        print("  python harness_idp_client.py my-account task-123 get")
        print("  python harness_idp_client.py my-account task-123 poll")
        sys.exit(1)

    account_id, task_id, action = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "get"

    try:
        client = HarnessScaffolderClient(account_id=account_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if action == "get":
            task = client.get_task(task_id)
            print(f"Task: {task}")
            print(f"Status: {task.status}")
            print(f"Is Success: {task.is_success()}")
        elif action == "poll":
            print(f"Polling task {task_id}...")
            task = client.poll_task(task_id, callback=lambda t: print(f"  {t.status}"))
            print(f"Final: {task}")
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
