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

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

BASE="https://app.terraform.io/api/v2"

# Get total pages
TOTAL_PAGES=$(http --ignore-stdin --quiet GET \
  "$BASE/organizations/$ORG/projects" \
  "Authorization: Bearer $TFC_TOKEN" \
  "page[size]==100" \
  "page[number]==1" \
  | jq -r '.meta.pagination."total-pages"')

echo "🔍 Searching $TOTAL_PAGES pages for projects matching: $PATTERN"

FOUND=0
for page in $(seq 1 "$TOTAL_PAGES"); do
  RESULTS=$(http --ignore-stdin --quiet GET \
    "$BASE/organizations/$ORG/projects" \
    "Authorization: Bearer $TFC_TOKEN" \
    "page[size]==100" \
    "page[number]==$page" \
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
