---
name: tfc-api
description: Query Terraform Cloud (TFC) workspaces, runs, plans, and logs via API. Use for inspecting TFC workspace state, run history, plan output, apply logs, and infrastructure changes.
---

# Terraform Cloud API

Query Terraform Cloud workspaces, runs, plans, and logs programmatically.

## Prerequisites

- TFC token at `~ ~/.terraform.d/credentials.tfrc.json`
- `jq` for JSON parsing
- `curl` for API requests

## Authentication

The skill reads your TFC token from the standard Terraform credentials file:

```bash
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)
```

## Common Patterns

### 0. Auto-Detect Workspace from Repository

```bash
# Extract workspace info from terraform configuration
WORKSPACE_INFO=$(./scripts/get-workspace-info.sh .)
ORG=$(echo "$WORKSPACE_INFO" | jq -r '.organization')
WORKSPACE=$(echo "$WORKSPACE_INFO" | jq -r '.workspace')
```

### 1. Trigger a Run (Normal or Destroy)

```bash
# Trigger a normal run
./scripts/trigger-run.sh {ORG} {WORKSPACE} false "My run message"

# Trigger a destroy run
./scripts/trigger-run.sh {ORG} {WORKSPACE} true "Decommissioning infrastructure"
```

Manual API call for triggering a run:
```bash
curl -s -X POST \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "attributes": {
        "is-destroy": true,
        "message": "Destroy run via API"
      },
      "type": "runs",
      "relationships": {
        "workspace": {
          "data": {
            "type": "workspaces",
            "id": "{WORKSPACE_ID}"
          }
        }
      }
    }
  }' \
  "https://app.terraform.io/api/v2/runs" | jq -r '.data.id'
```

### 2. Confirm (Apply) a Planned Run

If a workspace is configured for manual approval, you must confirm the plan:

```bash
./scripts/apply-run.sh {RUN_ID} "Approving decommissioning"
```

### 3. Wait for Run Completion

```bash
# Poll until terminal status (applied, errored, canceled, etc.)
./scripts/wait-for-run.sh {RUN_ID}
```

### 4. Read Plan and Apply Logs (Manual)

If you don't want to use helper scripts, you can fetch logs directly:

```bash
# Get plan ID from run
PLAN_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/runs/$RUN_ID" \
  | jq -r '.data.relationships.plan.data.id')

# Get plan log URL
LOG_URL=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/plans/$PLAN_ID" \
  | jq -r '.data.attributes["log-read-url"]')

# Download logs (JSON Lines format)
curl -s "$LOG_URL" > /tmp/plan-log.jsonl

# Extract planned changes
grep '"type":"planned_change"' /tmp/plan-log.jsonl | jq -r '."@message"'
```

## Helper Scripts

| Script | Purpose |
|----------|---------|
| `get-workspace-info.sh` | Detect ORG and Workspace from local TF config |
| `trigger-run.sh` | Trigger a new run (supports destroy) |
| `apply-run.sh` | Confirm/Apply a planned run |
| `wait-for-run.sh` | Poll status until terminal state |
| `list-runs.sh` | List recent runs for a workspace |
| `get-plan.sh` | Download and parse plan logs |
| `get-apply.sh` | Download and parse apply logs |
| `set-workspace-branch.sh` | Update VCS branch for speculative plans |
| `open-workspace.sh` | Open TFC workspace in browser |
| `open-registry.sh` | Open Module Registry in browser |
| `delete-registry-module.sh` | Delete a registry module by organization/namespace/name/provider |
| `publish-registry-module-vcs.sh` | Publish a registry module via VCS integration (GitHub) |
| `check-registry-module-status.sh` | Check the status of a registry module |

## Registry Module Operations

### 5. Publish a Registry Module via VCS

Publish a Terraform module to Terraform Cloud's private registry with automatic VCS integration. This is the recommended approach as it enables automatic module publishing from Git tags.

```bash
# Publish a module with VCS integration
./scripts/publish-registry-module-vcs.sh {ORG} {GITHUB_REPO} {OAUTH_TOKEN_ID}

# Example: Publish MSKProvisioned module
./scripts/publish-registry-module-vcs.sh example-org example-org/terraform-aws-MSKProvisioned ot-EXAMPLE-OAUTH-TOKEN-ID
```

**Prerequisites:**
- GitHub repository must exist
- `@terraform` team must have admin access to the GitHub repository
- OAuth token ID must be configured in TFC (get from https://app.terraform.io/app/settings/tokens)

**Expected Output:**
- `status: "setup_complete"` - Module is ready for use
- `publishing_mechanism: "git_tag"` - Module auto-publishes from Git tags
- `vcs_repo.identifier: "owner/repo"` - VCS repository is configured

### 6. Check Registry Module Status

Monitor the status and configuration of a published module:

```bash
# Check module status
./scripts/check-registry-module-status.sh {ORG} {NAMESPACE} {NAME} {PROVIDER}

# Example: Check MSKProvisioned module status
./scripts/check-registry-module-status.sh example-org example-org MSKProvisioned aws
```

**Module Statuses:**
- `setup_complete` - Ready for use
- `pending` - Module is processing (may indicate missing VCS configuration)
- `archived` - Module is archived

### 7. Delete a Registry Module

Remove a module from the private registry:

```bash
# Delete a module
./scripts/delete-registry-module.sh {ORG} {NAMESPACE} {NAME} {PROVIDER}

# Example: Delete module with incorrect case
./scripts/delete-registry-module.sh example-org example-org mskprovisioned aws
```

**Use Cases:**
- Removing modules with incorrect case naming
- Cleaning up duplicate modules
- Removing modules stuck in pending status due to misconfiguration

### Complete Module Lifecycle Example

Resolve a module stuck in pending status:

```bash
# 1. Check current status
./scripts/check-registry-module-status.sh example-org example-org mskprovisioned aws

# 2. Delete the module (incorrect case)
./scripts/delete-registry-module.sh example-org example-org mskprovisioned aws

# 3. Verify deletion
./scripts/check-registry-module-status.sh example-org example-org mskprovisioned aws  # Should error (not found)

# 4. Publish with correct case and VCS configuration
./scripts/publish-registry-module-vcs.sh example-org example-org/terraform-aws-MSKProvisioned ot-EXAMPLE-OAUTH-TOKEN-ID

# 5. Verify new status
./scripts/check-registry-module-status.sh example-org example-org MSKProvisioned aws

# 6. Confirm VCS integration is working
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/example-org/registry-modules/private/example-org/MSKProvisioned/aws" \
  | jq '.data.attributes.vcs_repo'
```

## Run Statuses

- `pending` - Queued, not started
- `planning` - Plan in progress
- `planned` - Plan complete, awaiting approval
- `cost_estimated` - Cost estimation complete (often follows `planned`)
- `policy_checked` - Policy checks complete
- `applying` - Apply in progress
- `applied` - Successfully applied
- `planned_and_finished` - Plan-only run complete
- `errored` - Run failed
- `canceled` - Run canceled
- `discarded` - Run discarded

## Parsing Tips

### Extract Resource Changes

```bash
# Get resources being destroyed from plan log
/path/to/tfc-api/scripts/get-plan.sh {RUN_ID} | grep "DESTROY:"

# Get resource change summary
grep '"type":"change_summary"' /tmp/plan-log.jsonl | jq -r '.changes | "Add: \(.add) | Change: \(.change) | Destroy: \(.remove)"'
```

### Extract Warnings and Errors

```bash
# Get all errors
grep '"severity":"error"' /tmp/plan-log.jsonl \
  | jq -r '.diagnostic.summary + ": " + .diagnostic.detail'
```

## References

- [TFC API Documentation](https://developer.hashicorp.com/terraform/cloud-docs/api-docs)
- [Run API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run)
- [Plan API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/plans)
- [Apply API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/applies)
- [Private Registry Modules API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/modules)
- [KEDB: TFC Registry Module Stuck in Pending](https://github.com/example-org/terraform-example-org-KEDB/blob/main/kedb/terraform-cloud/tfc-registry-module-stuck-pending-vcs-configuration.md) - Knowledge Engineering Database for module publishing troubleshooting
