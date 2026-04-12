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

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

BASE="https://app.terraform.io/api/v2"

RESPONSE=$(http --ignore-stdin --quiet GET "$BASE/team-projects" \
  "filter[project][id]==$PROJECT_ID" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json")

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
