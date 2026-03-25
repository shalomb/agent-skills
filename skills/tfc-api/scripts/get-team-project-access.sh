#!/usr/bin/env bash
set -euo pipefail

# Get team-project access for a specific team within a project
# Usage: ./get-team-project-access.sh <project_id> <team_id>
# Example: ./get-team-project-access.sh prj-XvGpyMLBwcJivdt6 team-47uU6YqcjaMzRPtA

PROJECT_ID="${1:-}"
TEAM_ID="${2:-}"

if [ -z "$PROJECT_ID" ] || [ -z "$TEAM_ID" ]; then
  echo "Usage: $0 <project_id> <team_id>"
  echo "Example: $0 prj-XvGpyMLBwcJivdt6 team-47uU6YqcjaMzRPtA"
  exit 1
fi

TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "${TFC_TOKEN:-}")
if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "❌ TFC token not found. Set TFC_TOKEN or configure ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

BASE="https://app.terraform.io/api/v2"

RESPONSE=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  "$BASE/team-projects?filter%5Bproject%5D%5Bid%5D=$PROJECT_ID")

RECORD=$(echo "$RESPONSE" | jq --arg tid "$TEAM_ID" '.data[] | select(.relationships.team.data.id == $tid)')

if [ -z "$RECORD" ]; then
  echo "❌ No access record found for team $TEAM_ID in project $PROJECT_ID"
  exit 1
fi

echo "$RECORD" | jq '{
  record_id: .id,
  team_id: .relationships.team.data.id,
  access: .attributes.access,
  project_access: .attributes."project-access",
  workspace_access: .attributes."workspace-access"
}'
