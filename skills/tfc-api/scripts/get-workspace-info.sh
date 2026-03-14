#!/usr/bin/env bash
set -euo pipefail

# Extract TFC workspace information from terraform configuration
# Usage: ./get-workspace-info.sh [terraform-config-dir]

CONFIG_DIR="${1:-.}"

# Look for terraform backend configuration
BACKEND_FILES=(
  "$CONFIG_DIR/terraform.tf"
  "$CONFIG_DIR/backend.tf"
  "$CONFIG_DIR/main.tf"
)

ORG=""
WORKSPACE=""

for file in "${BACKEND_FILES[@]}"; do
  if [ -f "$file" ]; then
    # Extract organization
    if [ -z "$ORG" ]; then
      ORG=$(grep -A 10 'backend "remote"' "$file" 2>/dev/null | grep 'organization' | sed 's/.*organization.*=.*"\(.*\)".*/\1/' | tr -d ' ')
    fi
    
    # Extract workspace name
    if [ -z "$WORKSPACE" ]; then
      WORKSPACE=$(grep -A 10 'backend "remote"' "$file" 2>/dev/null | grep -A 3 'workspaces' | grep 'name' | sed 's/.*name.*=.*"\(.*\)".*/\1/' | tr -d ' ')
    fi
    
    # Break if we found both
    if [ -n "$ORG" ] && [ -n "$WORKSPACE" ]; then
      break
    fi
  fi
done

# If not found in backend, check .terraform directory
if [ -z "$ORG" ] || [ -z "$WORKSPACE" ]; then
  if [ -f "$CONFIG_DIR/.terraform/terraform.tfstate" ]; then
    if [ -z "$ORG" ]; then
      ORG=$(jq -r '.backend.config.organization // empty' "$CONFIG_DIR/.terraform/terraform.tfstate" 2>/dev/null)
    fi
    if [ -z "$WORKSPACE" ]; then
      WORKSPACE=$(jq -r '.backend.config.workspaces.name // empty' "$CONFIG_DIR/.terraform/terraform.tfstate" 2>/dev/null)
    fi
  fi
fi

# Output results
if [ -z "$ORG" ] || [ -z "$WORKSPACE" ]; then
  echo "❌ Could not find TFC workspace configuration" >&2
  echo "" >&2
  echo "Searched in:" >&2
  for file in "${BACKEND_FILES[@]}"; do
    if [ -f "$file" ]; then
      echo "  ✓ $file" >&2
    else
      echo "  ✗ $file (not found)" >&2
    fi
  done
  if [ -f "$CONFIG_DIR/.terraform/terraform.tfstate" ]; then
    echo "  ✓ $CONFIG_DIR/.terraform/terraform.tfstate" >&2
  fi
  echo "" >&2
  echo "💡 Expected backend \"remote\" configuration with organization and workspace name" >&2
  exit 1
fi

# Output as JSON for easy parsing
jq -n --arg org "$ORG" --arg workspace "$WORKSPACE" '{
  organization: $org,
  workspace: $workspace,
  url: "https://app.terraform.io/app/\($org)/workspaces/\($workspace)"
}'
