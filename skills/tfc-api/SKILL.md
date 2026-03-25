---
name: tfc-api
description: Query Terraform Cloud (TFC) workspaces, runs, plans, logs, and team/project access via API. Use when inspecting TFC workspace state, checking run history, analyzing plan output, reviewing apply logs, managing team permissions, or diagnosing access issues in a Terraform Cloud organization.
---

# Terraform Cloud API

Query TFC workspaces, runs, logs, and team permissions without leaving the terminal.

## Authentication

```bash
# Standard credentials file
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

# Elevated token (for admin operations) — set via environment
export TFC_TOKEN=<your-token>
```

## Team & Project Access (permissions management)

**Read the reference first**: `references/tfc-team-project-access.md`

Key gotchas:
- Teams API supports `q=` search — always use it (large orgs may have 1000+ teams)
- Projects API does NOT support `q=` — must paginate manually via `find-project.sh`
- `tfe_team_project_access` with `access=admin` in Terraform ≠ guaranteed `admin` in TFC API — always verify
- `workspace_access.runs = "read"` = users are blocked; must be `"apply"` for full access

```bash
# Full diagnosis + fix workflow
./scripts/find-team.sh {ORGANIZATION} <name_pattern>              # find team IDs
./scripts/find-project.sh {ORGANIZATION} <name_pattern>           # find project ID
./scripts/get-team-project-access.sh <project_id> <team_id>       # current perms
./scripts/compare-team-project-access.sh <proj_a> <team_a> \
                                         <proj_b> <team_b>        # diff vs reference
./scripts/set-team-project-access.sh <project_id> <team_id> admin # fix
```

## Workspace Discovery

```bash
# Search by name pattern
BASE="https://app.terraform.io/api/v2"
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/{ORGANIZATION}/workspaces?search[name]=<pattern>" \
  | jq '.data[] | {id, name: .attributes.name}'

# Get workspace by exact name
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/{ORGANIZATION}/workspaces/<workspace-name>" \
  | jq '{id: .data.id, name: .data.attributes.name}'
```

## Run Management

```bash
# List recent runs
./scripts/list-runs.sh {ORGANIZATION} <workspace-name>

# Trigger a run
./scripts/trigger-run.sh {ORGANIZATION} <workspace-name> false "message"

# Wait for completion
./scripts/wait-for-run.sh <run-id>

# Approve a planned run
./scripts/apply-run.sh <run-id> "Approving"
```

## Workspace State Inspection

```bash
# Get plan/apply logs
./scripts/get-plan.sh <run-id>
./scripts/get-apply.sh <run-id>
```

## Helper Scripts

| Script | Purpose |
|--------|---------|
| `find-team.sh` | Find teams by name pattern using `q=` (handles 1000+ teams) |
| `find-project.sh` | Find projects by name fragment (paginates all pages) |
| `list-team-project-access.sh` | List all team access entries for a project |
| `get-team-project-access.sh` | Get one team's access record for a project |
| `compare-team-project-access.sh` | Diff permissions between two teams |
| `set-team-project-access.sh` | Update team access level on a project |
| `list-runs.sh` | List recent runs for a workspace |
| `trigger-run.sh` | Trigger a new run (supports destroy) |
| `apply-run.sh` | Confirm/apply a planned run |
| `wait-for-run.sh` | Poll status until terminal state |
| `get-plan.sh` | Download and parse plan logs |
| `get-apply.sh` | Download and parse apply logs |
| `get-workspace-info.sh` | Detect ORG and Workspace from local TF config |
| `set-workspace-branch.sh` | Update VCS branch for speculative plans |
| `open-workspace.sh` | Open TFC workspace in browser |
| `publish-registry-module-vcs.sh` | Publish a registry module via VCS |
| `check-registry-module-status.sh` | Check registry module status |
| `delete-registry-module.sh` | Delete a registry module |

## References

- `references/tfc-team-project-access.md` — Team permissions CRUD, pagination gotchas, access level semantics
- `references/tfc-api-reference.md` — Workspace/run/plan/log operations
- `references/tfc-vcs-validation.md` — VCS configuration validation
- [TFC API Docs](https://developer.hashicorp.com/terraform/cloud-docs/api-docs)
