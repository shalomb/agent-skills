---
name: tfc-api
description: Query Terraform Cloud (TFC) workspaces, runs, plans, logs, and team/project access via API. Use when inspecting TFC workspace state, checking run history, analyzing plan output, reviewing apply logs, managing team permissions, or diagnosing access issues in a Terraform Cloud organization.
---

# Terraform Cloud API

Query TFC workspaces, runs, logs, and team permissions without leaving the terminal.

## Authentication

All scripts use a **two-tier token resolution**: `TFC_TOKEN` env var takes precedence, falling back to `~/.terraform.d/credentials.tfrc.json`. This matters because personal tokens often lack org-level permissions (e.g. team management) that automation tokens have.

```bash
# Option 1: Environment variable (preferred for automation/elevated ops)
export TFC_TOKEN=<your-token>

# Option 2: Credentials file (automatic fallback)
# ~/.terraform.d/credentials.tfrc.json — used if TFC_TOKEN is unset

# Typical workflow: source an env file with the automation token
source /tmp/env.sh  # sets TFC_TOKEN
```

> **Gotcha**: A personal token may return 404 or empty results for team/project
> operations that an automation token can see. If `find-team.sh` returns no
> results but you know teams exist, try an elevated token.

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
# Search by name pattern (fuzzy)
BASE="https://app.terraform.io/api/v2"
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/{ORGANIZATION}/workspaces?search[name]=<pattern>" \
  | jq '.data[] | {id, name: .attributes.name}'

# Search by wildcard name pattern (prefix, suffix, or substring)
# Note: square brackets should be percent-encoded in URLs: [ as %5B and ] as %5D
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/{ORGANIZATION}/workspaces?search%5Bwildcard-name%5D=*<pattern>*" \
  | jq '.data[] | {id, name: .attributes.name}'

# Using httpie (modern replacement for curl)
# httpie handles encoding and provides cleaner syntax
http GET "$BASE/organizations/{ORGANIZATION}/workspaces" \
  "Authorization: Bearer $TFC_TOKEN" \
  "search[wildcard-name]==*<pattern>*" \
  | jq '.data[] | {id, name: .attributes.name}'

# Get workspace by exact name
```
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

### Unlocking a workspace blocked by old runs

Workspaces lock on `cost_estimated` or `pending` runs. To unblock:

```bash
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)
BASE="https://app.terraform.io/api/v2"

# Discard a planned/cost_estimated run
curl -s -X POST -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{"comment":"Discarding to re-plan"}' \
  "$BASE/runs/<run-id>/actions/discard"

# Cancel a pending/planning run (discard won't work on pending)
curl -s -X POST -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{"comment":"Cancelling"}' \
  "$BASE/runs/<run-id>/actions/cancel"
```

**Gotcha**: If the workspace is locked by run A and run B is queued behind it,
you must discard/cancel A first — B won't start until A releases the lock.
Check `locked-by` on the workspace to find the blocking run:
```bash
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/{ORG}/workspaces/<name>" \
  | jq '.data.relationships["locked-by"].data.id'
```

### Switching VCS branch for speculative plans

```bash
./scripts/set-workspace-branch.sh {ORGANIZATION} <workspace-name> <branch>
```

Useful for testing a consolidated branch (`iac-reveng`) against workspaces
that normally point at per-env branches (`iac-reveng-dev`). Remember to
reset the branch after validation.

## Workspace State Inspection

```bash
# Get plan/apply logs
./scripts/get-plan.sh <run-id>
./scripts/get-apply.sh <run-id>
```

## Helper Scripts

| Script | Purpose |
|--------|---------|
| `find-workspace.sh` | Find workspaces by name or wildcard pattern (prefix/suffix/substring) |
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
