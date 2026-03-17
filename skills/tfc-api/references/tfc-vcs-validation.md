---
title: Terraform Cloud VCS Configuration Validation
description: Validate workspace VCS configurations point to correct GitHub repositories
---

# TFC VCS Configuration Validation Guide

## Overview

This guide covers validating that Terraform Cloud workspace VCS configurations correctly point to existing GitHub repositories, handling repository redirects, and identifying misconfigurations.

## Key Concepts

### VCS Identifier
The repository identifier in TFC format: `{owner}/{repo-name}` (e.g., `oneTakeda/my-terraform-repo`)

### Canonical vs. Renamed Repositories
- **Canonical name**: Current official repository name in GitHub
- **Renamed repo**: Repo that was renamed, but old name still works via GitHub's 301 redirect
- **Issue**: TFC may reference old/renamed repo names without issue until team operations fail

### Repository Redirect
When a GitHub repository is renamed, the old URL still works but returns HTTP 301 redirect to canonical URL.
- Old URL: `https://api.github.com/repos/oneTakeda/old-repo-name`
- New URL: `https://api.github.com/repos/oneTakeda/new-repo-name` (returned in redirect)

## Validation Checklist

Before bulk operations on workspaces, validate:

### 1. Repository Exists
```bash
# Check if repo exists
gh api repos/{org}/{repo-name} --jq '.name'

# If 404, check for redirect
curl -sI https://api.github.com/repos/{org}/{repo-name} | grep -i location
  # Returns: location: https://api.github.com/repositories/{id}
  # Follow redirect to get canonical name
```

### 2. Get Canonical Repository Name
```bash
# Get actual current repository name (after redirects)
gh api repos/{org}/{repo-name} --jq '.name'

# If differs from VCS config, repository was renamed
```

### 3. Validate User Has Required Permissions
```bash
# Check user's permission on repository
gh api repos/{org}/{repo-name} --jq '.permissions'

# Required for team management: admin or maintain
```

### 4. Validate Workspace VCS Configuration
```bash
# Get workspace VCS configuration
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  https://app.terraform.io/api/v2/organizations/{org}/workspaces/{ws-name} | \
  jq '.data.attributes."vcs-repo" | {identifier, branch, oauth-token-id}'

# Compare vcs-repo.identifier against actual repository name
```

## Common Issues & Solutions

### Issue 1: Repository Renamed (HTTP 301 Redirect)
**Symptom**: Repository operations fail mysteriously, but repo exists
**Root Cause**: TFC workspace points to old repo name; GitHub redirects to new name

**Solution**:
```bash
# 1. Discover canonical name
CANONICAL=$(gh api repos/{org}/{old-repo-name} --jq '.name')

# 2. Check if TFC uses old name
OLD_VCS=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  https://app.terraform.io/api/v2/organizations/Takeda/workspaces/{ws-name} | \
  jq -r '.data.attributes."vcs-repo".identifier')

# 3. If different, update TFC workspace
if [ "$OLD_VCS" != "oneTakeda/$CANONICAL" ]; then
  curl -X PATCH -H "Authorization: Bearer $TFC_TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    -d '{
      "data": {
        "type": "workspaces",
        "attributes": {
          "vcs-repo": {
            "identifier": "oneTakeda/'$CANONICAL'",
            "branch": "{branch}",
            "oauth-token-id": "{oauth-token-id}"
          }
        }
      }
    }' \
    https://app.terraform.io/api/v2/organizations/Takeda/workspaces/{ws-name}
fi
```

### Issue 2: Repository Does Not Exist (404)
**Symptom**: TFC references non-existent repository
**Root Cause**: Repo deleted, moved to different org, or misconfigured name

**Solution**:
```bash
# Verify the repo actually doesn't exist
gh api repos/{org}/{repo-name} 2>&1 | grep "404\|Not Found"

# Options:
# 1. Check if repo exists under different name/org
# 2. Create repository if intentionally missing
# 3. Update TFC workspace to correct repository
# 4. Remove/disable workspace if no longer needed
```

### Issue 3: Insufficient User Permissions
**Symptom**: Cannot add teams to repository (HTTP 403)
**Root Cause**: User has read-only access; team management requires admin/maintain

**Solution**:
```bash
# Check user's current permission
gh api repos/{org}/{repo-name} --jq '.permissions | to_entries[] | select(.value==true) | .key'

# If result is only "pull", user is read-only
# Workaround: Use elevated credentials (e.g., service account via tmux session)
```

## Bulk Validation Script Pattern

```bash
#!/bin/bash
# Validate all workspace VCS configs in organization

ORG="Takeda"
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

# List all workspaces
WORKSPACES=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  https://app.terraform.io/api/v2/organizations/$ORG/workspaces | \
  jq -r '.data[].attributes.name')

echo "Validating $ORG workspace VCS configurations"
echo "=================================================="

for ws in $WORKSPACES; do
  # Get VCS identifier
  VCS=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
    https://app.terraform.io/api/v2/organizations/$ORG/workspaces/$ws | \
    jq -r '.data.attributes."vcs-repo".identifier // "NONE"')
  
  if [ "$VCS" == "NONE" ] || [ -z "$VCS" ]; then
    echo "⚠️  $ws: No VCS configured"
    continue
  fi
  
  # Parse repo name
  REPO=$(echo $VCS | cut -d'/' -f2)
  
  # Check if repo exists
  if gh api repos/oneTakeda/$REPO --jq '.name' >/dev/null 2>&1; then
    CANONICAL=$(gh api repos/oneTakeda/$REPO --jq '.name')
    if [ "$CANONICAL" != "$REPO" ]; then
      echo "⚠️  $ws: Points to renamed repo ($REPO → $CANONICAL)"
    else
      echo "✓ $ws: OK ($VCS)"
    fi
  else
    echo "✗ $ws: Repo not found ($VCS)"
  fi
done
```

## Prevention Tips

1. **Regular Audits**: Run bulk validation monthly to catch renamed repos early
2. **Monitor Webhooks**: TFC webhooks may fail if repo is renamed
3. **Track Redirects**: When repos are renamed, update all TFC references immediately
4. **Document Renames**: Keep audit trail of which repos were renamed and when
5. **Pre-flight Checks**: Always validate repo existence before team operations

## References

- [TFC API: Workspaces](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces)
- [GitHub API: Repositories](https://docs.github.com/en/rest/repos)
- [GitHub Redirects](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api?apiVersion=2022-11-28#error-cannot-GET)
