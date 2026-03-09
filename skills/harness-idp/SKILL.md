---
name: harness-idp
description: Launch and monitor Harness.io IDP Scaffolder workflows. Execute any registered IDP template, manage task execution, and track provisioning status via API.
---

# Harness IDP Skill

Launch and monitor any Harness.io Internal Developer Platform (IDP) Scaffolder workflow programmatically.

## Description

This skill enables programmatic interaction with Harness.io's IDP Scaffolder v2 API for executing any registered IDP template. Create and manage long-running tasks (infrastructure provisioning, workspace setup, configuration workflows, etc.), poll task status, monitor execution progress, and integrate IDP workflows into CI/CD pipelines. Works with any Harness IDP Scaffolder template.

## Triggers

Use this skill when:
- User mentions "Harness", "IDP", "Scaffolder", or "idp.harness.io"
- User wants to execute any Harness IDP Scaffolder template
- User needs to launch workflows programmatically (infrastructure, deployments, configurations, etc.)
- User wants to monitor Harness task execution or check task status
- User needs to integrate IDP workflows into pipelines or automation
- User mentions "Harness template", "Scaffolder task", or "IDP workflow"

## Prerequisites

- Harness.io account with IDP Scaffolder v2 enabled
- Valid credentials: `HARNESS_ACCOUNT_ID` and `HARNESS_API_KEY` environment variables
- Harness API key with Scaffolder permissions
- IDP template already deployed (e.g., TFC workspace provisioning template)

## Core Capabilities

### 1. Create Tasks

Launch a new Scaffolder task with custom parameters. Works with any registered IDP template.

```bash
# Create a task using any IDP template
python3 << 'EOF'
from harness_idp_client import HarnessScaffolderClient
from typing import Dict, Any

client = HarnessScaffolderClient(
    account_id="{HARNESS_ACCOUNT_ID}",
    api_key="{HARNESS_API_KEY}",
    base_url="https://idp.harness.io"  # or your custom Harness instance
)

# Task parameters depend on your IDP template schema
# These are examples - customize for your template
values = {
    "param1": "value1",
    "param2": "value2",
    "param3": "value3",
    # Add all template-specific parameters
}

task = client.create_task(
    template_ref="template:account/{YOUR_TEMPLATE_NAME}",  # Any registered IDP template
    values=values,
    secrets={  # Optional: sensitive parameters (not logged)
        "api_token": "secret-token",
        "password": "secret-password"
    }
)

print(f"Task created: {task.id}")
print(f"Status: {task.status}")
EOF
```

**Parameters:**
- `template_ref`: IDP template reference (format: `template:account/{TemplateName}`)
- `values`: Parameter dictionary (customized for your template)
- `secrets`: Optional sensitive values (not logged, excluded from audit trails)

**Returns:**
- Task object with unique task ID

**Common Use Cases:**
- Infrastructure provisioning (cloud resources, networks, databases)
- Workspace creation (TFC, deployment pipelines, project setup)
- Configuration workflows (deployment configurations, environment setup)
- Application onboarding (service registration, resource allocation)
- Any custom IDP Scaffolder template your organization has registered

### 2. Poll Task Status

Monitor task execution until completion (blocking).

```bash
python3 << 'EOF'
from harness_idp_client import HarnessScaffolderClient
import time

client = HarnessScaffolderClient(
    account_id="{HARNESS_ACCOUNT_ID}",
    api_key="{HARNESS_API_KEY}"
)

# Poll task with callback
def on_status_update(task):
    elapsed = time.time() - start_time
    print(f"[{elapsed:.0f}s] {task.status.upper()}")

start_time = time.time()

try:
    final_task = client.poll_task(
        task_id="{TASK_ID}",
        poll_interval=2,      # Check every 2 seconds
        timeout=3600,         # Max 1 hour wait
        callback=on_status_update
    )
    
    if final_task.is_success():
        print("✅ Task completed successfully")
        print(f"Output: {final_task.spec.get('output')}")
    else:
        print(f"❌ Task failed: {final_task.status}")
        if final_task.spec.get("error"):
            print(f"Error: {final_task.spec['error']}")
except TimeoutError as e:
    print(f"⏱️  {e}")
    print(f"Check task status manually: https://app.harness.io/ng/account/{HARNESS_ACCOUNT_ID}/module/idp/create/tasks/{TASK_ID}")
EOF
```

**Parameters:**
- `task_id`: UUID of task to monitor
- `poll_interval`: Seconds between API calls (default: 2)
- `timeout`: Maximum seconds to wait (default: 3600)
- `callback`: Optional function called after each poll: `def callback(task): ...`

**Returns:**
- Final Task object (terminal state: COMPLETED, FAILED, or CANCELLED)

**Raises:**
- `TimeoutError`: If task exceeds timeout
- `requests.RequestException`: If API call fails

### 3. Get Task Status (Non-Blocking)

Fetch current task state without blocking.

```bash
python3 << 'EOF'
from harness_idp_client import HarnessScaffolderClient

client = HarnessScaffolderClient(
    account_id="{HARNESS_ACCOUNT_ID}",
    api_key="{HARNESS_API_KEY}"
)

task = client.get_task("{TASK_ID}")

print(f"Task ID:        {task.id}")
print(f"Status:         {task.status}")
print(f"Created At:     {task.created_at}")
print(f"Created By:     {task.created_by}")
print(f"Last Heartbeat: {task.last_heartbeat_at}")

if task.is_terminal():
    print("Terminal state reached")
    if task.is_success():
        print(f"Success! Output: {task.spec.get('output')}")
    else:
        print(f"Failed: {task.spec.get('error')}")
EOF
```

**Returns:**
- Task object with current status and metadata

### 4. Stream Task Events (Real-Time)

Monitor task execution via Server-Sent Events (streaming).

```bash
python3 << 'EOF'
from harness_idp_client import HarnessScaffolderClient

client = HarnessScaffolderClient(
    account_id="{HARNESS_ACCOUNT_ID}",
    api_key="{HARNESS_API_KEY}"
)

# Stream events in real-time
for event in client.stream_events("{TASK_ID}"):
    event_type = event.get("type")
    message = event.get("message", "")
    timestamp = event.get("timestamp")
    
    if event_type == "log":
        print(f"[{timestamp}] {message}")
    elif event_type == "status_changed":
        new_status = event.get("status")
        print(f"[{timestamp}] Status changed to: {new_status}")
    elif event_type == "error":
        error_msg = event.get("error", {}).get("message", "Unknown error")
        print(f"[{timestamp}] ❌ {error_msg}")
    elif event_type == "completed":
        output = event.get("output", {})
        print(f"[{timestamp}] ✅ Task completed")
        print(f"Output: {output}")
        break
EOF
```

**Yields:**
- Event dictionaries as they arrive (real-time streaming)

**Event Types:**
- `log`: Task execution log message
- `status_changed`: Task status update
- `error`: Error event
- `completed`: Task completion

### 5. Generic Workflow Example (Customizable)

Complete workflow for executing any IDP Scaffolder template.

```bash
#!/bin/bash

set -e

HARNESS_ACCOUNT_ID="${HARNESS_ACCOUNT_ID:?Missing HARNESS_ACCOUNT_ID}"
HARNESS_API_KEY="${HARNESS_API_KEY:?Missing HARNESS_API_KEY}"
HARNESS_BASE_URL="${HARNESS_BASE_URL:-https://idp.harness.io}"

TEMPLATE_NAME="$1"        # e.g., MyTemplateV3
PARAM1="$2"               # Template parameter 1
PARAM2="$3"               # Template parameter 2
PARAM3="$4"               # Template parameter 3

if [ -z "$TEMPLATE_NAME" ] || [ -z "$PARAM1" ] || [ -z "$PARAM2" ] || [ -z "$PARAM3" ]; then
    echo "Usage: $0 <template_name> <param1> <param2> <param3>"
    echo "Example: $0 ProvisionWorkspaceV3 workspace-name team-name owner@example.com"
    exit 1
fi

python3 << PYTHON_EOF
import os
import sys
import time
from harness_idp_client import HarnessScaffolderClient

# Initialize client
client = HarnessScaffolderClient(
    account_id="${HARNESS_ACCOUNT_ID}",
    api_key="${HARNESS_API_KEY}",
    base_url="${HARNESS_BASE_URL}"
)

# Prepare template parameters (customize for your template)
params = {
    "param1": "${PARAM1}",
    "param2": "${PARAM2}",
    "param3": "${PARAM3}",
    # Add more parameters as needed
}

# 1. Create task
print(f"🚀 Executing template: ${TEMPLATE_NAME}")
try:
    task = client.create_task(
        template_ref="template:account/${TEMPLATE_NAME}",
        values=params
    )
    print(f"✅ Task created: {task.id}")
except Exception as e:
    print(f"❌ Failed to create task: {e}", file=sys.stderr)
    sys.exit(1)

# 2. Monitor execution
print("⏳ Monitoring task execution...")
task_url = f"${HARNESS_BASE_URL}/{HARNESS_ACCOUNT_ID}/ui/accounts/{HARNESS_ACCOUNT_ID}/idp/tasks/{task.id}"
print(f"📊 Dashboard: {task_url}")

def print_progress(t):
    elapsed = time.time() - start_time
    sys.stdout.write(f"\\r   [{elapsed:3.0f}s] {t.status.upper():<10}   ")
    sys.stdout.flush()

start_time = time.time()
try:
    final_task = client.poll_task(
        task_id=task.id,
        poll_interval=5,
        timeout=3600,
        callback=print_progress
    )
except TimeoutError:
    print(f"\\n⏱️  Task exceeded timeout")
    print(f"Check status manually: {task_url}")
    sys.exit(1)

print()  # Newline after progress

# 3. Report result
if final_task.is_success():
    print(f"🎉 Task completed successfully!")
    output = final_task.spec.get("output", {})
    if output:
        print(f"   Output: {output}")
    sys.exit(0)
else:
    print(f"❌ Task failed: {final_task.status}")
    if final_task.spec.get("error"):
        error = final_task.spec["error"]
        if isinstance(error, dict):
            print(f"   Error: {error.get('message', str(error))}")
        else:
            print(f"   Error: {error}")
    print(f"   Check task details: {task_url}")
    sys.exit(1)
PYTHON_EOF
```

**Customize for your templates:**
1. Replace `${TEMPLATE_NAME}` with your actual IDP template name
2. Update parameter names/values to match your template schema
3. Adjust `HARNESS_BASE_URL` if using a custom Harness instance
4. Adjust timeout/polling interval as needed for your workflow duration

## Authentication

### Environment Variables (Recommended)

```bash
export HARNESS_ACCOUNT_ID="your-account-id"
export HARNESS_API_KEY="your-api-key"  # Treat as secret
```

### Programmatic (Alternative)

```python
from harness_idp_client import HarnessScaffolderClient

client = HarnessScaffolderClient(
    account_id="account-id",
    api_key="api-key",
    base_url="https://app.harness.io"  # Optional: custom instance
)
```

### Vault Integration (Enterprise)

For secure credential management in CI/CD:

```bash
# Retrieve from HashiCorp Vault
export HARNESS_API_KEY=$(vault kv get -field=api_key secret/harness/credentials)
export HARNESS_ACCOUNT_ID=$(vault kv get -field=account_id secret/harness/credentials)
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid credentials | Check `HARNESS_ACCOUNT_ID` and `HARNESS_API_KEY` |
| `404 Not Found` | Task doesn't exist | Verify task ID and account ID |
| `422 Unprocessable Entity` | Invalid template parameters | Validate `values` dict against template schema |
| `TimeoutError` | Task exceeded timeout | Check Harness UI for long-running operations |
| Connection errors | Network issues | Check network connectivity and firewall rules |

### Robust Implementation

```python
import logging
from harness_idp_client import HarnessScaffolderClient
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = HarnessScaffolderClient()

try:
    # Create task
    task = client.create_task(
        template_ref="template:account/MyTemplate",
        values={"param": "value"}
    )
    logger.info(f"Task created: {task.id}")
    
    # Poll with timeout
    final_task = client.poll_task(
        task.id,
        timeout=3600,
        poll_interval=5
    )
    
    if final_task.is_success():
        logger.info("Task succeeded")
    else:
        logger.error(f"Task failed: {final_task.status}")
        
except requests.exceptions.HTTPError as e:
    logger.error(f"API error: {e}")
    # Task might still be running; provide manual check link
    
except TimeoutError as e:
    logger.warning(f"Task monitoring timed out: {e}")
    # Task might complete later; don't fail hard
    
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Performance & Scaling

### Polling Optimization

- **Default interval**: 2 seconds (reasonable for most tasks)
- **For long operations**: Use 5-10 second interval to reduce API load
- **Real-time monitoring**: Use `stream_events()` instead of polling

```python
# Efficient polling for long task
final_task = client.poll_task(
    task_id,
    poll_interval=10,  # Less frequent checks
    timeout=7200       # 2 hour timeout
)

# Real-time streaming (no polling overhead)
for event in client.stream_events(task_id):
    process_event(event)
```

### Rate Limiting

- Harness API imposes rate limits
- Polling interval of 2-10 seconds is safe
- Use callbacks to avoid tight loops

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
- name: Provision Infrastructure
  env:
    HARNESS_ACCOUNT_ID: ${{ secrets.HARNESS_ACCOUNT_ID }}
    HARNESS_API_KEY: ${{ secrets.HARNESS_API_KEY }}
  run: |
    python scripts/provision_workspace.py \
      --resource-id ${{ inputs.resource-id }} \
      --environment dev \
      --github-team platform-eng \
      --okta-owner admin@example.com
```

### Python Script with Logging

```python
#!/usr/bin/env python3
import sys
import logging
from harness_idp_client import HarnessScaffolderClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

client = HarnessScaffolderClient()

try:
    # Create and monitor task
    task = client.create_task(...)
    final_task = client.poll_task(task.id)
    
    sys.exit(0 if final_task.is_success() else 1)
except Exception as e:
    logging.error(f"Provisioning failed: {e}")
    sys.exit(2)
```

## Troubleshooting

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = HarnessScaffolderClient()
# Requests will now show full HTTP details
```

### Manual Task Inspection

```bash
# Get task URL for manual review
echo "https://app.harness.io/ng/account/{HARNESS_ACCOUNT_ID}/module/idp/create/tasks/{TASK_ID}"

# Query task API directly
curl -H "x-api-key: {HARNESS_API_KEY}" \
  https://idp.harness.io/{HARNESS_ACCOUNT_ID}/idp/api/scaffolder/v2/tasks/{TASK_ID}
```

### Event Streaming Debugging

```python
# Print all events
for event in client.stream_events(task_id):
    print(f"Event: {json.dumps(event, indent=2)}")
```

## References

- [Harness IDP Documentation](https://developer.harness.io/)
- [Scaffolder API v2 Reference](https://developer.harness.io/docs/internal-developer-platform/apis/)
- [Getting Started with Harness IDP](https://developer.harness.io/docs/internal-developer-platform/getting-started/)

## Privacy & Security

- **Never commit API keys** to version control
- **Use environment variables** for all credentials
- **Rotate API keys** regularly
- **Mask sensitive parameters** in logs (especially `secrets` field)
- **Use Vault or similar** for secure credential storage in CI/CD

## Version History

- **v1.0** (2025-03-09): Initial release. Supports Harness IDP Scaffolder v2 API, task creation, polling, and event streaming.
