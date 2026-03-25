---
title: TFC Team & Project Access API Reference
description: CRUD operations for TFC team permissions on projects. Covers discovery patterns, pagination gotchas, the team-projects endpoint, and access level semantics.
---

# TFC Team & Project Access API Reference

## Key Lessons

### 1. Teams API requires `q=` for search — pagination hides results

The `/organizations/:org/teams` endpoint returns only 20 teams by default.
In large orgs with many teams, **always use `q=` for name search**:

```bash
# ✅ Correct — server-side search, handles large orgs
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/{ORGANIZATION}/teams?q=<name_pattern>&page%5Bsize%5D=100" \
  | jq -r '.data[] | "\(.id) \(.attributes.name) members=\(.attributes."users-count")"'

# Also supports filter[names] for exact multi-match
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/{ORGANIZATION}/teams?filter%5Bnames%5D=team-alpha,team-beta" \
  | jq -r '.data[] | "\(.id) \(.attributes.name) members=\(.attributes."users-count")"'
```

### 2. Projects API does NOT support `q=` — must paginate manually

```bash
# ❌ q= silently returns nothing for projects
# ✅ Must paginate all pages and grep client-side

TOTAL_PAGES=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/{ORGANIZATION}/projects?page%5Bsize%5D=100" \
  | jq -r '.meta.pagination."total-pages"')

for page in $(seq 1 "$TOTAL_PAGES"); do
  curl -s -H "Authorization: Bearer $TFC_TOKEN" \
    "https://app.terraform.io/api/v2/organizations/{ORGANIZATION}/projects?page%5Bsize%5D=100&page%5Bnumber%5D=$page" \
    | jq -r '.data[] | select(.attributes.name | test("<name_pattern>")) | "\(.id) \(.attributes.name)"'
done
```

Use `./scripts/find-project.sh {ORGANIZATION} <name_pattern>` to avoid writing this each time.

### 3. `tfe_team_project_access` with `access=admin` may not equal TFC API `access=admin`

The Terraform provider sets `access = "admin"` on `tfe_team_project_access`, but
TFC can silently downgrade or mismatch the stored value. **Always verify via API after provisioning**:

```bash
./scripts/get-team-project-access.sh <project_id> <team_id>
# Check: access == "admin" and workspace_access.runs == "apply"
```

### 4. `workspace_access` lives on `team-projects`, NOT `team-workspaces`

Project-level access (`tfe_team_project_access`) controls workspace permissions for ALL
workspaces in the project via `workspace-access` attributes. Separate `tfe_team_access`
resources are only needed for workspace-specific overrides.

The key workspace permission that blocks users is **`runs`**:
- `read`  → can view runs only (effectively blocked)
- `plan`  → can trigger plans, cannot apply
- `apply` → full plan + apply access ✅

---

## Authentication

```bash
# From standard Terraform credentials file
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

# Or from environment
export TFC_TOKEN=<your-token>
```

---

## Team Discovery

```bash
# Find teams by name pattern (handles large orgs via q=)
./scripts/find-team.sh {ORGANIZATION} <name_pattern>

# Exact multi-name lookup
BASE="https://app.terraform.io/api/v2"
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/{ORGANIZATION}/teams?filter%5Bnames%5D=team-alpha,team-beta" \
  | jq -r '.data[] | "\(.id) \(.attributes.name) members=\(.attributes."users-count")"'
```

---

## Project Discovery

```bash
# Find projects by name fragment (paginates all pages)
./scripts/find-project.sh {ORGANIZATION} <name_pattern>

# Manual single-page (when you know the project name prefix)
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/{ORGANIZATION}/projects?page%5Bsize%5D=100" \
  | jq -r '.data[] | select(.attributes.name | test("<name_pattern>")) | "\(.id) \(.attributes.name)"'
```

---

## Team-Project Access CRUD

### Read — list all teams on a project

```bash
./scripts/list-team-project-access.sh {ORGANIZATION} <project_id>

# Raw API
BASE="https://app.terraform.io/api/v2"
curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/team-projects?filter%5Bproject%5D%5Bid%5D=<project_id>" \
  | jq '.data[] | {
      record_id: .id,
      team: .relationships.team.data.id,
      access: .attributes.access,
      workspace_access: .attributes."workspace-access"
    }'
```

### Read — get one team's access on a project

```bash
./scripts/get-team-project-access.sh <project_id> <team_id>
```

### Read — compare two teams side-by-side

```bash
./scripts/compare-team-project-access.sh \
  <project_id_a> <team_id_a> \
  <project_id_b> <team_id_b>

# Example: verify target team matches a known-good reference team
./scripts/compare-team-project-access.sh \
  prj-AAAAAAAAAAAAAAAA team-AAAAAAAAAAAAAAAA \
  prj-BBBBBBBBBBBBBBBB team-BBBBBBBBBBBBBBBB
```

### Update — set access level (admin/maintain/write/read)

```bash
./scripts/set-team-project-access.sh <project_id> <team_id> admin

# Raw PATCH — find record_id first via list or get script
RECORD_ID="tprj-XXXXXXXXXXXX"
curl -s -X PATCH \
  -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{"data": {"type": "team-projects", "attributes": {"access": "admin"}}}' \
  "https://app.terraform.io/api/v2/team-projects/$RECORD_ID" \
  | jq '{access: .data.attributes.access, workspace_access: .data.attributes."workspace-access"}'
```

### Create — add a team to a project

```bash
BASE="https://app.terraform.io/api/v2"
curl -s -X POST \
  -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "team-projects",
      "attributes": {"access": "admin"},
      "relationships": {
        "team":    {"data": {"type": "teams",    "id": "<team_id>"}},
        "project": {"data": {"type": "projects", "id": "<project_id>"}}
      }
    }
  }' \
  "$BASE/team-projects" \
  | jq '{record_id: .data.id, access: .data.attributes.access}'
```

### Delete — remove a team from a project

```bash
RECORD_ID="tprj-XXXXXXXXXXXX"  # from list or get script
curl -s -X DELETE \
  -H "Authorization: Bearer $TFC_TOKEN" \
  "https://app.terraform.io/api/v2/team-projects/$RECORD_ID"
```

---

## Access Level Semantics

When `access` is set to a named level, TFC expands it to these workspace permissions:

| access    | runs    | variables | state-versions | sentinel-mocks | create | delete | move | locking | run-tasks |
|-----------|---------|-----------|----------------|----------------|--------|--------|------|---------|-----------|
| `admin`   | `apply` | `write`   | `write`        | `read`         | ✅     | ✅     | ✅   | ✅      | ✅        |
| `maintain`| `apply` | `write`   | `write`        | `read`         | ✅     | ❌     | ✅   | ✅      | ✅        |
| `write`   | `apply` | `write`   | `read-outputs` | `none`         | ❌     | ❌     | ❌   | ✅      | ❌        |
| `read`    | `read`  | `read`    | `read-outputs` | `none`         | ❌     | ❌     | ❌   | ❌      | ❌        |

> **Critical**: `runs: "read"` = users cannot trigger plans or applies = effectively blocked.

---

## Diagnosis Workflow (for access issues)

```bash
# 1. Find the team IDs
./scripts/find-team.sh {ORGANIZATION} <name_pattern>

# 2. Find the project ID
./scripts/find-project.sh {ORGANIZATION} <name_pattern>

# 3. Check current permissions
./scripts/get-team-project-access.sh <project_id> <team_id>

# 4. Compare against a known-good reference team
./scripts/compare-team-project-access.sh \
  <ref_project_id> <ref_team_id> \
  <target_project_id> <target_team_id>

# 5. Fix if different
./scripts/set-team-project-access.sh <project_id> <team_id> admin

# 6. Verify
./scripts/compare-team-project-access.sh ...  # should show ✅ IDENTICAL
```

---

## References

- [TFC API: Team Project Access](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/project-team-access)
- [TFC API: Teams (with q= filter)](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/teams#list-teams)
- [TFC API: Projects](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/projects)
- [go-tfe TeamProjectAccess source](https://github.com/hashicorp/go-tfe/blob/main/team_project_access.go)
- [terraform-provider-tfe resource docs](https://github.com/hashicorp/terraform-provider-tfe/blob/main/website/docs/r/team_project_access.html.markdown)
