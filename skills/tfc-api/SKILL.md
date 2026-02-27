---
name: tfc-api
description: Query Terraform Cloud (TFC) workspaces, runs, plans, and logs via API. Use for inspecting TFC workspace state, run history, plan output, apply logs, and infrastructure changes.
---

# Terraform Cloud API

Query Terraform Cloud workspaces, runs, plans, and logs programmatically.

## Prerequisites

- TFC token at `~/.terraform.d/credentials.tfrc.json`
- `jq` for JSON parsing
- `curl` for API requests

## Authentication

The skill reads your TFC token from the standard Terraform credentials file:

```bash
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)
```

All API requests use this token for authentication.

## Common Patterns

### 0. Auto-Detect Workspace from Repository

```bash
# Extract workspace info from terraform configuration
WORKSPACE_INFO=$(./scripts/get-workspace-info.sh .)
ORG=$(echo "$WORKSPACE_INFO" | jq -r '.organization')
WORKSPACE=$(echo "$WORKSPACE_INFO" | jq -r '.workspace')

echo "Organization: $ORG"
echo "Workspace: $WORKSPACE"
```

This reads the backend configuration from terraform files:

```hcl
backend "remote" {
  hostname     = "app.terraform.io"
  organization = "my-org"
  workspaces {
    name = "my-workspace"
  }
}
```

### 1. Get Workspace Information

```bash
# Get workspace ID from organization and name
WORKSPACE_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/my-org/workspaces/my-workspace" \
  | jq -r '.data.id')

echo "Workspace ID: $WORKSPACE_ID"
```

### 2. List Recent Runs

```bash
# List last 20 runs for a workspace
curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/workspaces/$WORKSPACE_ID/runs?page%5Bsize%5D=20" \
  | jq -r '.data[] | "\(.id) | \(.attributes.status) | \(.attributes.message)"'
```

### 3. Get Run Details

```bash
# Get detailed information about a specific run
RUN_ID="run-2rzGeZbvRwLRCQgQ"

curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/runs/$RUN_ID?include=plan" \
  | jq '.data.attributes | {status, message, "created-at", "has-changes"}'
```

### 4. Read Plan Logs

```bash
# Get plan ID from run
PLAN_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/runs/$RUN_ID" \
  | jq -r '.data.relationships.plan.data.id')

# Get plan log URL and download logs
LOG_URL=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/plans/$PLAN_ID" \
  | jq -r '.data.attributes["log-read-url"]')

# Download logs (JSON Lines format)
curl -s "$LOG_URL" > /tmp/plan-log.jsonl

# Extract planned changes
grep '"type":"planned_change"' /tmp/plan-log.jsonl | jq -r '."@message"'

# Extract change summary
grep '"type":"change_summary"' /tmp/plan-log.jsonl | jq -r '."@message"'
```

### 5. Read Apply Logs

```bash
# Get apply ID from run
APPLY_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/runs/$RUN_ID" \
  | jq -r '.data.relationships.apply.data.id')

# Get apply log URL
LOG_URL=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/applies/$APPLY_ID" \
  | jq -r '.data.attributes["log-read-url"]')

# Download and parse apply logs
curl -s "$LOG_URL" > /tmp/apply-log.jsonl
```

## Helper Scripts

Use the provided helper scripts for common operations:

### Auto-Detect Workspace (Recommended)

The skill can automatically detect workspace information from your terraform configuration:

```bash
./scripts/get-workspace-info.sh [terraform-config-dir]
```

This reads the `backend "remote"` configuration from:
- `terraform.tf`
- `backend.tf`
- `main.tf`
- `.terraform/terraform.tfstate`

Example:
```bash
cd /path/to/terraform/config
./scripts/get-workspace-info.sh
# Output: {"organization": "my-org", "workspace": "my-workspace", ...}
```

### List Runs (Auto-Detect)

List runs for the current workspace (auto-detected from terraform config):

```bash
./scripts/list-runs-auto.sh [terraform-config-dir] [limit]
```

Example:
```bash
cd /path/to/terraform/config
./scripts/list-runs-auto.sh . 10
```

### List Runs (Explicit)

```bash
./scripts/list-runs.sh <org> <workspace> [limit]
```

Example:
```bash
./scripts/list-runs.sh my-org my-workspace 10
```

### Get Plan Output

```bash
./scripts/get-plan.sh <run-id>
```

Example:
```bash
./scripts/get-plan.sh run-2rzGeZbvRwLRCQgQ
```

### Get Apply Output

```bash
./scripts/get-apply.sh <run-id>
```

### Set Workspace VCS Branch

Update the VCS branch that TFC monitors for speculative plans:

```bash
./scripts/set-workspace-branch.sh <organization> <workspace> <branch-name>
```

**Auto-Detect Mode** (recommended):

```bash
# From terraform config directory, automatically set branch
cd /path/to/terraform/config
./scripts/set-workspace-branch.sh . feature/my-branch
```

Example:
```bash
# Set workspace to feature branch for speculative plan
./scripts/set-workspace-branch.sh my-org my-project feature/my-branch

# Output:
# Workspace: my-project (ID: ws-nNUGnzdxgBoruzzc)
# Updated VCS branch to: feature/my-branch
# TFC will now queue speculative plans against this branch
```

**Manual Invocation**:

```bash
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

# Get workspace ID
WORKSPACE_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/my-org/workspaces/my-workspace" \
  | jq -r '.data.id')

# Update VCS branch
curl -s -X PATCH \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/workspaces/$WORKSPACE_ID" \
  -d '{
    "data": {
      "type": "workspaces",
      "attributes": {
        "vcs-repo": {
          "branch": "feature/my-feature-branch"
        }
      }
    }
  }' | jq '.data.attributes | {name, "vcs-repo": .vcs_repo}'
```

## Log Format

TFC logs use JSON Lines format (one JSON object per line). Common event types:

- `refresh_start` / `refresh_complete` - Resource state refresh
- `planned_change` - Resources being created/updated/destroyed
- `change_summary` - Total resources affected
- `apply_start` / `apply_complete` - Apply operations
- `diagnostic` - Warnings and errors
- `resource_drift` - Detected infrastructure drift

## API Endpoints

Base URL: `https://app.terraform.io/api/v2`

| Endpoint | Purpose |
|----------|---------|
| `/organizations/{org}/workspaces/{name}` | Get workspace details |
| `/workspaces/{id}/runs` | List workspace runs |
| `/runs/{id}` | Get run details |
| `/plans/{id}` | Get plan details |
| `/applies/{id}` | Get apply details |

## Run Statuses

- `pending` - Queued, not started
- `plan_queued` - Plan queued
- `planning` - Plan in progress
- `planned` - Plan complete, awaiting approval
- `cost_estimated` - Cost estimation complete
- `policy_checked` - Policy checks complete
- `policy_override` - Policy override required
- `apply_queued` - Apply queued
- `applying` - Apply in progress
- `applied` - Successfully applied
- `planned_and_finished` - Plan-only run complete
- `errored` - Run failed
- `canceled` - Run canceled
- `discarded` - Run discarded

## Parsing Tips

### Extract Resource Changes

```bash
# Get resources being created
grep '"type":"planned_change"' /tmp/plan-log.jsonl \
  | jq -r 'select(.change.action == "create") | "CREATE: " + .change.resource.addr'

# Get resources being destroyed
grep '"type":"planned_change"' /tmp/plan-log.jsonl \
  | jq -r 'select(.change.action == "delete") | "DESTROY: " + .change.resource.addr'

# Get resources being moved (no downtime)
grep '"type":"planned_change"' /tmp/plan-log.jsonl \
  | jq -r 'select(.change.action == "move") | "MOVE: " + .change.resource.addr'
```

### Extract Warnings and Errors

```bash
# Get all warnings
grep '"severity":"warning"' /tmp/plan-log.jsonl \
  | jq -r '.diagnostic.summary + ": " + .diagnostic.detail'

# Get all errors
grep '"severity":"error"' /tmp/plan-log.jsonl \
  | jq -r '.diagnostic.summary + ": " + .diagnostic.detail'
```

### Get Change Summary

```bash
# Get plan summary
grep '"type":"change_summary"' /tmp/plan-log.jsonl \
  | jq -r '.changes | "Add: \(.add) | Change: \(.change) | Destroy: \(.remove)"'
```

## References

- [TFC API Documentation](https://developer.hashicorp.com/terraform/cloud-docs/api-docs)
- [Run API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run)
- [Plan API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/plans)
- [Apply API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/applies)

### Open Workspace in Browser

Automatically detect and open the TFC workspace in your browser:

```bash
./scripts/open-workspace.sh
```

This script:
1. Tries `.terraform/terraform.tfstate` first (if `terraform init` has run)
2. Falls back to parsing `terraform.tf` for backend configuration
3. Opens `https://app.terraform.io/app/{org}/workspaces/{workspace}` in default browser

### Open Module Registry

When working in a Terraform module repository, open the TFC private registry page:

```bash
./scripts/open-registry.sh
```

This script:
1. Extracts module name from git remote origin
2. Detects organization from terraform backend or git remote
3. Opens `https://app.terraform.io/app/{org}/registry/modules/private/{org}/{module}/aws`

Useful for quickly viewing module documentation, versions, and usage in TFC.

## Browser Integration

Both `open-workspace.sh` and `open-registry.sh` work cross-platform:
- Linux: Uses `x-www-browser` or `xdg-open`
- macOS: Uses `open`
- Respects your default browser settings

