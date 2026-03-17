---
title: GitHub Team Management Operations
description: Add teams to repositories, manage permissions, and handle repository redirects
---

# GitHub Team Management Operations Guide

## Overview

This guide covers managing GitHub organization teams' access to repositories, including handling permission levels, repository redirects, and bulk operations.

## Prerequisites

- GitHub CLI (`gh`) authenticated with sufficient permissions
- User must have **admin** or **maintain** role on target repositories
- Knowledge of team slugs and repository names
- Understanding of GitHub permission levels

## Core Concepts

### Permission Levels

| Permission | Capabilities | Use Case |
|-----------|---|---|
| `pull` | View repository, clone, read issues/PRs | Read-only access |
| `triage` | All pull + manage labels, milestones | Testing/QA teams |
| `push` | All pull + push code, merge PRs | Development teams |
| `maintain` | All push + manage repository settings | Tech leads |
| `admin` | All maintain + delete repository | Admins only |

### Team vs. User Permissions
- **Team permissions**: Apply to all team members at specified level
- **User permissions**: Individual permissions (override team if higher)
- **Precedence**: Higher permission level wins (e.g., user with `admin` beats team with `push`)

### Repository Redirects

When a repository is renamed in GitHub:
- Old repository URL still works via HTTP 301 redirect
- API calls to old name automatically resolve to new name
- Team management operations **may fail** on old repo names depending on endpoint

## Adding Team to Repository

### Method 1: GitHub REST API (Recommended)
```bash
# Add team to repository with specified permission
gh api -X PUT \
  /orgs/{org}/teams/{team-slug}/repos/{org}/{repo} \
  -f permission={permission-level}

# Returns: Empty response on success (HTTP 204)
# On error: JSON error object

# Example:
gh api -X PUT \
  /orgs/oneTakeda/teams/gmsgq-dad-clouddevsecops-iac-reveng/repos/oneTakeda/my-repo \
  -f permission=push
```

### Method 2: cURL with Bearer Token
```bash
TOKEN=$(gh auth token)

curl -s -X PUT \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/orgs/{org}/teams/{team-slug}/repos/{org}/{repo}" \
  -d "{\"permission\":\"push\"}"
```

### Method 3: Via tmux Session (For Elevated Credentials)
```bash
# When standard credentials have insufficient permissions
tmux-exec.sh "{session}:{window}.{pane}" \
  'gh api -X PUT /orgs/{org}/teams/{team-slug}/repos/{org}/{repo} -f permission=push'
```

## Handling Repository Redirects

### Detecting Redirects
```bash
# Check if repository was renamed
ACTUAL_NAME=$(gh api repos/{org}/{repo-name} --jq '.name')

if [ "$ACTUAL_NAME" != "{repo-name}" ]; then
  echo "Repository was renamed: {repo-name} → $ACTUAL_NAME"
fi
```

### Working with Redirects
```bash
# Old repo name (before rename)
OLD_REPO="old-repository-name"

# Method A: Use canonical name
CANONICAL=$(gh api repos/{org}/$OLD_REPO --jq '.name')
gh api -X PUT \
  /orgs/{org}/teams/{team-slug}/repos/{org}/$CANONICAL \
  -f permission=push

# Method B: Add to both (in case old name still used)
for repo in $OLD_REPO $CANONICAL; do
  gh api -X PUT \
    /orgs/{org}/teams/{team-slug}/repos/{org}/$repo \
    -f permission=push 2>/dev/null || true
done
```

## Verifying Team Access

### Check Team Access on Specific Repository
```bash
# List all teams with access to repository
gh api repos/{org}/{repo}/teams --jq '.[] | {slug, permission}'

# Check specific team
gh api repos/{org}/{repo}/teams \
  --jq '.[] | select(.slug == "{team-slug}") | .permission'

# Returns: "pull", "push", "maintain", "admin", or nothing (no access)
```

### List All Repositories for Team
```bash
# Get all repositories team has access to
gh api --paginate orgs/{org}/teams/{team-slug}/repos \
  --jq '.[] | {name, permission}'

# Count repositories
gh api --paginate orgs/{org}/teams/{team-slug}/repos \
  --jq '.[] | .name' | wc -l
```

## Common Issues & Solutions

### Issue 1: "You must have administrative rights"
**Symptom**: HTTP 403 error when trying to add team
**Root Cause**: User has read-only or triage permissions on repository

**Solution**:
```bash
# Check current permission
gh api repos/{org}/{repo} --jq '.permissions | to_entries[] | select(.value==true) | .key'

# Options:
# 1. Request admin/maintain role from repo owner
# 2. Use elevated credentials (service account)
# 3. Try from tmux session with different authentication
```

### Issue 2: "Team not found"
**Symptom**: HTTP 404 when trying to add team
**Root Cause**: Team slug incorrect or team deleted

**Solution**:
```bash
# List all teams in organization
gh api orgs/{org}/teams --jq '.[] | {slug, name}'

# Verify team slug matches exactly (case-sensitive)
```

### Issue 3: Repository Doesn't Exist (404)
**Symptom**: HTTP 404 on team add operation
**Root Cause**: Repository was deleted or renamed, old name doesn't exist

**Solution**:
```bash
# Follow redirect to canonical name
CANONICAL=$(gh api repos/{org}/{old-repo-name} --jq '.name' 2>/dev/null)

if [ -z "$CANONICAL" ]; then
  echo "Repository does not exist"
  # Options: Check different org, restore from backup, create new repo
else
  # Add team to canonical repo name
  gh api -X PUT \
    /orgs/{org}/teams/{team-slug}/repos/{org}/$CANONICAL \
    -f permission=push
fi
```

## Bulk Operations Pattern

### Add Team to Multiple Repositories
```bash
#!/bin/bash
ORG="oneTakeda"
TEAM="gmsgq-dad-clouddevsecops-iac-reveng"
PERMISSION="push"

# Array of repository names
REPOS=(
  "repo-1"
  "repo-2"
  "repo-3"
)

echo "Adding team $TEAM to ${#REPOS[@]} repositories..."
echo "=================================================="

SUCCESS=0
FAILED=0

for repo in "${REPOS[@]}"; do
  echo -n "$repo: "
  
  if gh api -X PUT \
      /orgs/$ORG/teams/$TEAM/repos/$ORG/$repo \
      -f permission=$PERMISSION >/dev/null 2>&1; then
    echo "✓"
    ((SUCCESS++))
  else
    # Try with canonical name
    CANONICAL=$(gh api repos/$ORG/$repo --jq '.name' 2>/dev/null)
    if [ -n "$CANONICAL" ] && [ "$CANONICAL" != "$repo" ]; then
      if gh api -X PUT \
          /orgs/$ORG/teams/$TEAM/repos/$ORG/$CANONICAL \
          -f permission=$PERMISSION >/dev/null 2>&1; then
        echo "✓ (via redirect: $CANONICAL)"
        ((SUCCESS++))
      else
        echo "✗"
        ((FAILED++))
      fi
    else
      echo "✗"
      ((FAILED++))
    fi
  fi
done

echo "=================================================="
echo "Result: $SUCCESS succeeded, $FAILED failed"
```

## Permission Level Decision Tree

```
Is this a production infrastructure repo?
├─ YES
│  ├─ Is it DevOps/Platform team? → admin/maintain
│  ├─ Is it application team? → push
│  └─ Is it security/compliance? → push + read audits
│
└─ NO (development/experimental)
   ├─ Is it a testing/sandbox repo? → push
   └─ Is it read-only reference? → pull
```

## Best Practices

1. **Verify Before Acting**: Always check repository exists and you have permissions
2. **Use Canonical Names**: Prefer actual repo names over redirects
3. **Test with One Repo**: Before bulk operations, test with single repo
4. **Document Changes**: Keep audit trail of team permissions changes
5. **Handle Redirects Gracefully**: Detect renamed repos and suggest updates
6. **Use Appropriate Levels**: Prefer `push` over `maintain`/`admin` for least privilege
7. **Monitor Failures**: Log and report repos that fail to add team

## References

- [GitHub API: Add or Update Team Repository Permissions](https://docs.github.com/en/rest/teams/teams?apiVersion=2022-11-28#add-or-update-team-repository-permissions)
- [GitHub Teams Documentation](https://docs.github.com/en/organizations/organizing-members-into-teams)
- [GitHub Repository Permissions](https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-roles-for-an-organization)
