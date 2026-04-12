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

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

BASE="https://app.terraform.io/api/v2"

echo "🔍 Team-project access for project: $PROJECT_ID"
echo ""

RESPONSE=$(http --ignore-stdin --quiet GET "$BASE/team-projects" \
  "filter[project][id]==$PROJECT_ID" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json")

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
