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

TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "${TFC_TOKEN:-}")
if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "❌ TFC token not found. Set TFC_TOKEN or configure ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

BASE="https://app.terraform.io/api/v2"

echo "🔍 Finding existing team-project access record..."
RESPONSE=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  "$BASE/team-projects?filter%5Bproject%5D%5Bid%5D=$PROJECT_ID")

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

PATCH_RESPONSE=$(curl -s -X PATCH \
  -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d "{\"data\": {\"type\": \"team-projects\", \"attributes\": {\"access\": \"$ACCESS\"}}}" \
  "$BASE/team-projects/$RECORD_ID")

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
