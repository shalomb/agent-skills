#!/usr/bin/env bash
set -euo pipefail

# Compare team-project access between two teams (across their respective projects)
# Usage: ./compare-team-project-access.sh <project_id_a> <team_id_a> <project_id_b> <team_id_b>
# Example: ./compare-team-project-access.sh \
#   prj-AAAAAAAAAAAAAAAA team-AAAAAAAAAAAAAAAA \
#   prj-BBBBBBBBBBBBBBBB team-BBBBBBBBBBBBBBBB

PROJECT_A="${1:-}"
TEAM_A="${2:-}"
PROJECT_B="${3:-}"
TEAM_B="${4:-}"

if [ -z "$PROJECT_A" ] || [ -z "$TEAM_A" ] || [ -z "$PROJECT_B" ] || [ -z "$TEAM_B" ]; then
  echo "Usage: $0 <project_id_a> <team_id_a> <project_id_b> <team_id_b>"
  echo "Example: $0 prj-AAAAAAAAAAAAAAAA team-AAAAAAAAAAAAAAAA prj-BBBBBBBBBBBBBBBB team-BBBBBBBBBBBBBBBB"
  exit 1
fi

# Prefer TFC_TOKEN env var; fall back to credentials file
if [ -z "${TFC_TOKEN:-}" ] || [ "${TFC_TOKEN:-}" = "null" ]; then
  TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "")
fi
if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "❌ TFC token not found. Set TFC_TOKEN or configure ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

BASE="https://app.terraform.io/api/v2"

fetch_access() {
  local project_id="$1"
  local team_id="$2"
  curl -s -H "Authorization: Bearer $TFC_TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    "$BASE/team-projects?filter%5Bproject%5D%5Bid%5D=$project_id" \
    | jq --arg tid "$team_id" '.data[] | select(.relationships.team.data.id == $tid)'
}

echo "🔍 Fetching access records..."
RECORD_A=$(fetch_access "$PROJECT_A" "$TEAM_A")
RECORD_B=$(fetch_access "$PROJECT_B" "$TEAM_B")

if [ -z "$RECORD_A" ]; then echo "❌ No record found for team $TEAM_A in project $PROJECT_A"; exit 1; fi
if [ -z "$RECORD_B" ]; then echo "❌ No record found for team $TEAM_B in project $PROJECT_B"; exit 1; fi

echo ""
echo "=== Team A: $TEAM_A (project: $PROJECT_A) ==="
echo "$RECORD_A" | jq '{access: .attributes.access, project_access: .attributes."project-access", workspace_access: .attributes."workspace-access"}'

echo ""
echo "=== Team B: $TEAM_B (project: $PROJECT_B) ==="
echo "$RECORD_B" | jq '{access: .attributes.access, project_access: .attributes."project-access", workspace_access: .attributes."workspace-access"}'

echo ""
echo "=== Diff (A vs B) ==="
PERMS_A=$(echo "$RECORD_A" | jq -S '{access: .attributes.access, project_access: .attributes."project-access", workspace_access: .attributes."workspace-access"}')
PERMS_B=$(echo "$RECORD_B" | jq -S '{access: .attributes.access, project_access: .attributes."project-access", workspace_access: .attributes."workspace-access"}')

if [ "$PERMS_A" = "$PERMS_B" ]; then
  echo "✅ Permissions are IDENTICAL"
else
  echo "❌ Permissions DIFFER:"
  diff <(echo "$PERMS_A") <(echo "$PERMS_B") | grep '^[<>]' | \
    sed 's/^< /  A: /' | sed 's/^> /  B: /'
fi
