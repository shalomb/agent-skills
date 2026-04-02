#!/usr/bin/env bash
set -euo pipefail

# Find a TFC project by name fragment (paginates all projects)
# Usage: ./find-project.sh <org> <name_fragment>
# Example: ./find-project.sh {ORGANIZATION} my-project
# Example: ./find-project.sh {ORGANIZATION} "proj-a\|proj-b"

ORG="${1:-}"
PATTERN="${2:-}"

if [ -z "$ORG" ] || [ -z "$PATTERN" ]; then
  echo "Usage: $0 <org> <name_fragment>"
  echo "Example: $0 {ORGANIZATION} my-project"
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

# Get total pages
TOTAL_PAGES=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
  "$BASE/organizations/$ORG/projects?page%5Bsize%5D=100&page%5Bnumber%5D=1" \
  | jq -r '.meta.pagination."total-pages"')

echo "🔍 Searching $TOTAL_PAGES pages for projects matching: $PATTERN"

FOUND=0
for page in $(seq 1 "$TOTAL_PAGES"); do
  RESULTS=$(curl -s -H "Authorization: Bearer $TFC_TOKEN" \
    "$BASE/organizations/$ORG/projects?page%5Bsize%5D=100&page%5Bnumber%5D=$page" \
    | jq -r --arg pat "$PATTERN" \
      '.data[] | select(.attributes.name | test($pat)) | "\(.id)  \(.attributes.name)  workspaces=\(.attributes."workspace-count") teams=\(.attributes."team-count")"')

  if [ -n "$RESULTS" ]; then
    echo "$RESULTS"
    FOUND=$((FOUND + $(echo "$RESULTS" | wc -l)))
  fi
done

echo ""
if [ "$FOUND" = "0" ]; then
  echo "❌ No projects found matching: $PATTERN"
  exit 1
else
  echo "📊 Found: $FOUND project(s)"
fi
