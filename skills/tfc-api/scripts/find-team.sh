#!/usr/bin/env bash
set -euo pipefail

# Find a TFC team by name (supports q= search, handles pagination)
# Usage: ./find-team.sh <org> <team_name_or_pattern>
# Example: ./find-team.sh {ORGANIZATION} my-team-name
# Example: ./find-team.sh {ORGANIZATION} "partial-name"   # partial match via q=

ORG="${1:-}"
QUERY="${2:-}"

if [ -z "$ORG" ] || [ -z "$QUERY" ]; then
  echo "Usage: $0 <org> <team_name_or_pattern>"
  echo "Example: $0 {ORGANIZATION} my-team-name"
  echo "Example: $0 {ORGANIZATION} partial-name"
  exit 1
fi

TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "${TFC_TOKEN:-}")
if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "❌ TFC token not found. Set TFC_TOKEN or configure ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

BASE="https://app.terraform.io/api/v2"

# Use q= for server-side search (case-insensitive), then filter client-side
ENCODED_QUERY=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
RESPONSE=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  "$BASE/organizations/$ORG/teams?q=${ENCODED_QUERY}&page%5Bsize%5D=100")

TOTAL=$(echo "$RESPONSE" | jq '.meta.pagination."total-count" // (.data | length)')
COUNT=$(echo "$RESPONSE" | jq '.data | length')

if [ "$COUNT" = "0" ]; then
  echo "❌ No teams found matching: $QUERY"
  exit 1
fi

echo "🔍 Teams matching '$QUERY' (showing $COUNT of $TOTAL):"
echo ""
echo "$RESPONSE" | jq -r '.data[] | "\(.id)  \(.attributes.name)  members=\(.attributes."users-count")"' | \
  awk '{printf "%-35s  %-55s  %s\n", $1, $2, $3}'
