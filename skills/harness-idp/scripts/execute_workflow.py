#!/usr/bin/env python3
"""
Generic Harness IDP Scaffolder Workflow Execution

Execute any registered IDP Scaffolder template with custom parameters.
Handles credential validation, task creation, monitoring, and error reporting.

Usage:
    export HARNESS_ACCOUNT_ID="your-account-id"
    export HARNESS_API_KEY="your-api-key"

    python execute_workflow.py \\
        --template MyTemplate \\
        --param1 value1 \\
        --param2 value2

    # With watch disabled (background task)
    python execute_workflow.py \\
        --template MyTemplate \\
        --param1 value1 \\
        --param2 value2 \\
        --no-watch

    # Custom Harness instance
    python execute_workflow.py \\
        --template MyTemplate \\
        --param1 value1 \\
        --harness-base-url https://harness.example.com
"""

import argparse
import logging
import os
import sys
import time
import json
from typing import Optional, Dict, Any
from pathlib import Path

# Import client from same directory
sys.path.insert(0, str(Path(__file__).parent))
from harness_idp_client import HarnessScaffolderClient


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure logging.

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def ephemeral_message(message: str) -> None:
    """Display an ephemeral message (will be cleared later).

    Args:
        message: Message to display
    """
    sys.stdout.write(f"\r{message:<80}")
    sys.stdout.flush()


def clear_ephemeral() -> None:
    """Clear the ephemeral message line."""
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()


class WorkflowExecutor:
    """Generic Harness IDP Scaffolder workflow executor."""

    def __init__(self, logger: logging.Logger, base_url: Optional[str] = None):
        """Initialize executor.

        Args:
            logger: Configured logger
            base_url: Optional custom Harness base URL

        Raises:
            ValueError: If credentials are not available
        """
        self.logger = logger
        try:
            self.client = HarnessScaffolderClient(base_url=base_url) if base_url else HarnessScaffolderClient()
        except ValueError as e:
            logger.error(f"Failed to initialize Harness client: {e}")
            logger.error("Set HARNESS_ACCOUNT_ID and HARNESS_API_KEY environment variables")
            raise

    def execute(
        self,
        template: str,
        parameters: Dict[str, Any],
        watch: bool = True,
        timeout: int = 3600,
    ) -> bool:
        """Execute a Scaffolder workflow.

        Args:
            template: Template name (e.g., "MyTemplateV3")
            parameters: Dictionary of template parameters
            watch: If True, wait for completion
            timeout: Maximum seconds to wait (default: 1 hour)

        Returns:
            True if execution succeeded, False otherwise
        """
        # Display workflow details
        print(f"\n🚀 Executing IDP Template: {template}")
        print(f"   Parameters: {json.dumps(parameters, indent=6)}")

        # Create task
        ephemeral_message("📤 Submitting workflow to Harness...")

        try:
            task = self.client.create_task(
                template_ref=f"template:account/{template}",
                values=parameters,
            )
        except ValueError as e:
            clear_ephemeral()
            self.logger.error(f"Workflow submission failed: {e}")
            return False
        except Exception as e:
            clear_ephemeral()
            self.logger.error(f"Unexpected error during submission: {e}")
            return False

        clear_ephemeral()
        print(f"✅ Workflow started: {task.id}")

        # Show Harness UI link
        harness_url = self._get_task_url(task.id)
        print(f"📊 Monitor progress: {harness_url}")

        if not watch:
            print("💡 Workflow is running in background. Use --watch to monitor.")
            return True

        # Monitor execution
        return self._monitor_workflow(task.id, timeout)

    def _monitor_workflow(self, task_id: str, timeout: int) -> bool:
        """Monitor workflow execution until completion.

        Args:
            task_id: Task UUID
            timeout: Maximum seconds to wait

        Returns:
            True if workflow succeeded, False otherwise
        """
        print("⏳ Monitoring workflow execution...")

        start_time = time.time()

        def print_status(task):
            elapsed = time.time() - start_time
            ephemeral_message(f"   [{elapsed:3.0f}s] {task.status.upper():<10}")

        try:
            task = self.client.poll_task(
                task_id,
                callback=print_status,
                timeout=timeout
            )
        except TimeoutError as e:
            clear_ephemeral()
            self.logger.error(f"Workflow monitoring timed out: {e}")
            print(f"⚠️  Workflow exceeded {timeout} second timeout")
            print(f"   Task ID: {task_id}")
            print(f"   Check progress: {self._get_task_url(task_id)}")
            return False
        except Exception as e:
            clear_ephemeral()
            self.logger.error(f"Workflow monitoring failed: {e}")
            print(f"⚠️  Could not monitor workflow status")
            print(f"   Error: {e}")
            print(f"   Task ID: {task_id}")
            print(f"   Check progress: {self._get_task_url(task_id)}")
            return False

        clear_ephemeral()

        # Report result
        if task.is_success():
            print(f"✅ Workflow completed successfully!")
            if task.spec and "output" in task.spec:
                output = task.spec.get("output", {})
                if output:
                    print(f"   Output: {json.dumps(output, indent=6)}")
            return True
        else:
            print(f"❌ Workflow failed with status: {task.status}")
            print(f"   Task ID: {task_id}")
            print(f"   Check details: {self._get_task_url(task_id)}")

            if task.spec:
                error = task.spec.get("error")
                if error:
                    if isinstance(error, dict):
                        msg = error.get("message", str(error))
                    else:
                        msg = str(error)
                    print(f"   Error: {msg}")

            return False

    def _get_task_url(self, task_id: str) -> str:
        """Get Harness UI URL for task.

        Args:
            task_id: Task UUID

        Returns:
            Full Harness UI URL
        """
        try:
            account_id = self.client.account_id
            base_url = self.client.base_url
        except Exception:
            return "{HARNESS_BASE_URL}/ui/accounts/{HARNESS_ACCOUNT_ID}/idp/tasks/{task_id}"

        return f"{base_url}/{account_id}/ui/accounts/{account_id}/idp/tasks/{task_id}"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute Harness IDP Scaffolder Workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute workflow with parameters
  %(prog)s --template MyTemplate --param1 value1 --param2 value2

  # Background execution (no monitoring)
  %(prog)s --template MyTemplate --param1 value1 --no-watch

  # Custom Harness instance
  %(prog)s --template MyTemplate --param1 value1 --harness-base-url https://harness.example.com

Environment Variables:
  HARNESS_ACCOUNT_ID    Harness account ID (required)
  HARNESS_API_KEY       Harness API key (required, treat as secret)
  HARNESS_BASE_URL      Optional custom Harness base URL
        """,
    )

    parser.add_argument(
        "--template",
        required=True,
        help="IDP Scaffolder template name (e.g., MyTemplateV3)",
    )
    parser.add_argument(
        "--no-watch",
        action="store_false",
        dest="watch",
        default=True,
        help="Don't wait for completion (submit in background)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Maximum seconds to wait (default: 3600)",
    )
    parser.add_argument(
        "--harness-base-url",
        help="Custom Harness base URL (default: https://idp.harness.io)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    # Parse known args to handle dynamic parameters
    args, remaining = parser.parse_known_args()

    # Convert remaining args to parameters (--param-name value)
    parameters = {}
    i = 0
    while i < len(remaining):
        arg = remaining[i]
        if arg.startswith("--"):
            param_name = arg[2:]  # Remove "--"
            if i + 1 < len(remaining) and not remaining[i + 1].startswith("--"):
                param_value = remaining[i + 1]
                parameters[param_name] = param_value
                i += 2
            else:
                print(f"Error: {arg} requires a value", file=sys.stderr)
                return 1
        else:
            i += 1

    if not parameters:
        print("Error: At least one parameter is required (--param-name value)", file=sys.stderr)
        return 1

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(level=log_level)

    # Validate environment
    if not os.environ.get("HARNESS_ACCOUNT_ID"):
        logger.error("HARNESS_ACCOUNT_ID environment variable not set")
        return 1
    if not os.environ.get("HARNESS_API_KEY"):
        logger.error("HARNESS_API_KEY environment variable not set")
        return 1

    try:
        executor = WorkflowExecutor(logger, base_url=args.harness_base_url)
        success = executor.execute(
            template=args.template,
            parameters=parameters,
            watch=args.watch,
            timeout=args.timeout,
        )
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 2


if __name__ == "__main__":
    sys.exit(main())
