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

# Prefer TFC_TOKEN env var; fall back to credentials file
if [ -z "${TFC_TOKEN:-}" ] || [ "${TFC_TOKEN:-}" = "null" ]; then
  TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "")
fi
if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "❌ TFC token not found. Set TFC_TOKEN or configure ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

BASE="https://app.terraform.io/api/v2"

# Use q= for server-side search (case-insensitive), paginate all results
ENCODED_QUERY=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")

ALL_DATA="[]"
PAGE=1
TOTAL_PAGES=1

while [ "$PAGE" -le "$TOTAL_PAGES" ]; do
  RESPONSE=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
    -H "Content-Type: application/vnd.api+json" \
    "$BASE/organizations/$ORG/teams?q=${ENCODED_QUERY}&page%5Bsize%5D=100&page%5Bnumber%5D=$PAGE")

  # Check for API errors (e.g. 404 from insufficient permissions)
  if echo "$RESPONSE" | jq -e '.errors' >/dev/null 2>&1; then
    echo "❌ API error: $(echo "$RESPONSE" | jq -r '.errors[0].title // .errors[0].detail // "unknown"')" >&2
    exit 1
  fi

  TOTAL_PAGES=$(echo "$RESPONSE" | jq -r '.meta.pagination."total-pages" // 1')
  ALL_DATA=$(echo "$ALL_DATA" "$RESPONSE" | jq -s '.[0] + (.[1].data // [])')
  PAGE=$((PAGE + 1))
done

COUNT=$(echo "$ALL_DATA" | jq 'length')

if [ "$COUNT" = "0" ]; then
  echo "❌ No teams found matching: $QUERY"
  exit 1
fi

echo "🔍 Teams matching '$QUERY' (showing $COUNT of $COUNT):"
echo ""
echo "$ALL_DATA" | jq -r '.[] | "\(.id)  \(.attributes.name)  members=\(.attributes."users-count" // (.relationships.users.data | length))"' | \
  awk '{printf "%-35s  %-55s  %s\n", $1, $2, $3}'
