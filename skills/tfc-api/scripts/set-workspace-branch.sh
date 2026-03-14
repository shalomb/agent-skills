#!/bin/bash
set -euo pipefail

# Set Terraform Cloud workspace VCS branch
# Usage: ./set-workspace-branch.sh <org> <workspace> <branch>
# Auto-detect mode: ./set-workspace-branch.sh . <branch>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Get TFC token
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "Error: TFC token not found in ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

# Handle auto-detect mode
if [ "${1:-.}" = "." ]; then
  # Auto-detect from terraform config
  CONFIG_DIR="${1:-.}"
  BRANCH="${2:-}"
  
  if [ -z "$BRANCH" ]; then
    echo "Error: Branch name required (Usage: $0 . <branch>)"
    exit 1
  fi
  
  # Use get-workspace-info script to extract org/workspace
  if [ ! -f "$SCRIPT_DIR/get-workspace-info.sh" ]; then
    echo "Error: get-workspace-info.sh not found"
    exit 1
  fi
  
  WORKSPACE_INFO=$("$SCRIPT_DIR/get-workspace-info.sh" "$CONFIG_DIR")
  ORG=$(echo "$WORKSPACE_INFO" | jq -r '.organization')
  WORKSPACE=$(echo "$WORKSPACE_INFO" | jq -r '.workspace')
else
  # Manual mode
  ORG="$1"
  WORKSPACE="$2"
  BRANCH="$3"
  
  if [ -z "$BRANCH" ]; then
    echo "Error: Usage: $0 <org> <workspace> <branch>"
    echo "Or:     $0 . <branch>"
    exit 1
  fi
fi

echo "Fetching workspace ID for: $ORG/$WORKSPACE"

# Get workspace ID
WORKSPACE_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/$ORG/workspaces/$WORKSPACE" \
  | jq -r '.data.id')

if [ -z "$WORKSPACE_ID" ] || [ "$WORKSPACE_ID" = "null" ]; then
  echo "Error: Could not find workspace $WORKSPACE in organization $ORG"
  exit 1
fi

echo "Workspace ID: $WORKSPACE_ID"
echo "Updating VCS branch to: $BRANCH"

# Update workspace VCS branch
RESPONSE=$(curl -s -X PATCH \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/workspaces/$WORKSPACE_ID" \
  -d '{"data": {"type": "workspaces", "attributes": {"vcs-repo": {"branch": "'"$BRANCH"'"}}}}')

# Check for errors
ERROR=$(echo "$RESPONSE" | jq -r '.errors[] | .title // empty' 2>/dev/null || echo "")

if [ -n "$ERROR" ]; then
  echo "Error: $ERROR"
  echo "Full response:"
  echo "$RESPONSE" | jq '.'
  exit 1
fi

# Extract and display result
CURRENT_BRANCH=$(echo "$RESPONSE" | jq -r '.data.attributes["vcs-repo"].branch // "unknown"')
WORKSPACE_NAME=$(echo "$RESPONSE" | jq -r '.data.attributes.name')

echo ""
echo "✅ Success!"
echo "Workspace: $WORKSPACE_NAME (ID: $WORKSPACE_ID)"
echo "VCS Branch: $CURRENT_BRANCH"
echo ""
echo "TFC will now queue speculative plans against the '$CURRENT_BRANCH' branch."
