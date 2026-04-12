#!/usr/bin/env bash
set -euo pipefail

# Find a TFC workspace by name or wildcard pattern
# Usage: ./find-workspace.sh <org> <name_or_wildcard>
# Example: ./find-workspace.sh {ORGANIZATION} my-workspace-name
# Example: ./find-workspace.sh {ORGANIZATION} "*partial-name*"   # wildcard match via search[wildcard-name]

ORG="${1:-}"
QUERY="${2:-}"

if [ -z "$ORG" ] || [ -z "$QUERY" ]; then
  echo "Usage: $0 <org> <name_or_wildcard>"
  echo "Example: $0 {ORGANIZATION} my-workspace-name"
  echo "Example: $0 {ORGANIZATION} \"*partial-name*\""
  exit 1
fi

# Prefer TFC_TOKEN env var; fall back to credentials file
# Use the auth helper to load TFC_TOKEN
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

BASE="https://app.terraform.io/api/v2"

# If query has * use search[wildcard-name], otherwise use search[name] (fuzzy)
if [[ "$QUERY" == *"*"* ]]; then
  PARAM="search[wildcard-name]"
else
  PARAM="search[name]"
fi

ALL_DATA="[]"
PAGE=1
TOTAL_PAGES=1

while [ "$PAGE" -le "$TOTAL_PAGES" ]; do
  RESPONSE=$(http --ignore-stdin --quiet GET "$BASE/organizations/$ORG/workspaces" \
    "Authorization: Bearer $TFC_TOKEN" \
    "Content-Type: application/vnd.api+json" \
    "$PARAM==$QUERY" \
    "page[size]==100" \
    "page[number]==$PAGE")

  # Check for API errors
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
  echo "❌ No workspaces found matching: $QUERY"
  exit 0
fi

echo "🔍 Workspaces matching '$QUERY' (showing $COUNT of $COUNT):"
echo ""
echo "$ALL_DATA" | jq -r '.[] | "\(.id)  \(.attributes.name)  \(.attributes."terraform-version")  \(.attributes."updated-at")"' | \
  awk '{printf "%-35s  %-55s  %-10s  %s\n", $1, $2, $3, $4}'
