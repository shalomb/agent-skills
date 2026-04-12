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

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

BASE="https://app.terraform.io/api/v2"

ALL_DATA="[]"
PAGE=1
TOTAL_PAGES=1

while [ "$PAGE" -le "$TOTAL_PAGES" ]; do
  RESPONSE=$(http --ignore-stdin --quiet GET "$BASE/organizations/$ORG/teams" \
    "Authorization: Bearer $TFC_TOKEN" \
    "Content-Type: application/vnd.api+json" \
    "q==$QUERY" \
    "page[size]==100" \
    "page[number]==$PAGE")

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
