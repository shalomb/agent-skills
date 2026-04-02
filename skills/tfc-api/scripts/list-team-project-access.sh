#!/usr/bin/env bash
set -euo pipefail

# List all team-project access entries for a TFC project
# Usage: ./list-team-project-access.sh <org> <project_id>
# Example: ./list-team-project-access.sh {ORGANIZATION} prj-XXXXXXXXXXXXXXXX

ORG="${1:-}"
PROJECT_ID="${2:-}"

if [ -z "$ORG" ] || [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <org> <project_id>"
  echo "Example: $0 {ORGANIZATION} prj-XXXXXXXXXXXXXXXX"
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

echo "🔍 Team-project access for project: $PROJECT_ID"
echo ""

RESPONSE=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  "$BASE/team-projects?filter%5Bproject%5D%5Bid%5D=$PROJECT_ID")

COUNT=$(echo "$RESPONSE" | jq '.data | length')
if [ "$COUNT" = "0" ]; then
  echo "⚠️  No team access entries found for project $PROJECT_ID"
  exit 0
fi

echo "$RESPONSE" | jq -r '
  .data[] |
  "Team ID:    \(.relationships.team.data.id)
Record ID:  \(.id)
Access:     \(.attributes.access)
Project:    settings=\(.attributes."project-access".settings) teams=\(.attributes."project-access".teams) variable-sets=\(.attributes."project-access"."variable-sets")
Workspace:  runs=\(.attributes."workspace-access".runs) variables=\(.attributes."workspace-access".variables) state=\(.attributes."workspace-access"."state-versions") create=\(.attributes."workspace-access".create) delete=\(.attributes."workspace-access".delete) move=\(.attributes."workspace-access".move) locking=\(.attributes."workspace-access".locking) run-tasks=\(.attributes."workspace-access"."run-tasks") sentinel=\(.attributes."workspace-access"."sentinel-mocks")
---"
'

echo "📊 Total: $COUNT team access entries"
