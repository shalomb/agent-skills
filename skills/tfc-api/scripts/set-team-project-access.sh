#!/usr/bin/env bash
set -euo pipefail

# Update team-project access level for a team on a project
# Finds the existing record and patches it to the desired access level.
# Usage: ./set-team-project-access.sh <project_id> <team_id> <access>
# Access levels: admin | maintain | write | read
# Example: ./set-team-project-access.sh prj-XXXXXXXXXXXXXXXX team-XXXXXXXXXXXXXXXX admin

PROJECT_ID="${1:-}"
TEAM_ID="${2:-}"
ACCESS="${3:-}"

if [ -z "$PROJECT_ID" ] || [ -z "$TEAM_ID" ] || [ -z "$ACCESS" ]; then
  echo "Usage: $0 <project_id> <team_id> <access>"
  echo "Access levels: admin | maintain | write | read"
  echo "Example: $0 prj-XXXXXXXXXXXXXXXX team-XXXXXXXXXXXXXXXX admin"
  exit 1
fi

case "$ACCESS" in
  admin|maintain|write|read) ;;
  *)
    echo "❌ Invalid access level: $ACCESS"
    echo "Valid values: admin | maintain | write | read"
    exit 1
    ;;
esac

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

BASE="https://app.terraform.io/api/v2"

echo "🔍 Finding existing team-project access record..."
RESPONSE=$(http --ignore-stdin --quiet GET "$BASE/team-projects" \
  "filter[project][id]==$PROJECT_ID" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json")

RECORD_ID=$(echo "$RESPONSE" | jq -r --arg tid "$TEAM_ID" \
  '.data[] | select(.relationships.team.data.id == $tid) | .id')

if [ -z "$RECORD_ID" ] || [ "$RECORD_ID" = "null" ]; then
  echo "❌ No existing access record for team $TEAM_ID in project $PROJECT_ID"
  echo "   Use add-team-project-access.sh to create a new record"
  exit 1
fi

CURRENT_ACCESS=$(echo "$RESPONSE" | jq -r --arg tid "$TEAM_ID" \
  '.data[] | select(.relationships.team.data.id == $tid) | .attributes.access')

echo "📋 Record ID:      $RECORD_ID"
echo "   Current access: $CURRENT_ACCESS"
echo "   New access:     $ACCESS"
echo ""

PATCH_RESPONSE=$(http --ignore-stdin --quiet PATCH "$BASE/team-projects/$RECORD_ID" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json" \
  data:="{\"type\": \"team-projects\", \"attributes\": {\"access\": \"$ACCESS\"}}")

NEW_ACCESS=$(echo "$PATCH_RESPONSE" | jq -r '.data.attributes.access')

if [ "$NEW_ACCESS" = "$ACCESS" ]; then
  echo "✅ Access updated successfully to: $NEW_ACCESS"
  echo ""
  echo "$PATCH_RESPONSE" | jq '{
    access: .data.attributes.access,
    project_access: .data.attributes."project-access",
    workspace_access: .data.attributes."workspace-access"
  }'
else
  echo "❌ Update may have failed. Response:"
  echo "$PATCH_RESPONSE" | jq '.'
  exit 1
fi
