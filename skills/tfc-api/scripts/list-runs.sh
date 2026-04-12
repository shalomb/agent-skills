#!/usr/bin/env bash
set -euo pipefail

# List runs for a TFC workspace
# Usage: ./list-runs.sh <org> <workspace> [limit]

ORG="${1:-}"
WORKSPACE="${2:-}"
LIMIT="${3:-20}"

if [ -z "$ORG" ] || [ -z "$WORKSPACE" ]; then
  echo "Usage: $0 <org> <workspace> [limit]"
  echo "Example: $0 example-org tec-man-bio-prd-93553-NTC 10"
  exit 1
fi

# Get TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

# Get workspace ID
echo "🔍 Fetching workspace: $ORG/$WORKSPACE"
WORKSPACE_RESPONSE=$(http --ignore-stdin --quiet GET \
  "https://app.terraform.io/api/v2/organizations/$ORG/workspaces/$WORKSPACE" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json")

WORKSPACE_ID=$(echo "$WORKSPACE_RESPONSE" | jq -r '.data.id')

if [ "$WORKSPACE_ID" = "null" ] || [ -z "$WORKSPACE_ID" ]; then
  echo "❌ Workspace not found"
  exit 1
fi

echo "✅ Workspace ID: $WORKSPACE_ID"
echo ""

# List runs
echo "📋 Recent Runs (limit: $LIMIT):"
echo ""

RUNS_RESPONSE=$(http --ignore-stdin --quiet GET \
  "https://app.terraform.io/api/v2/workspaces/$WORKSPACE_ID/runs" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json" \
  "page[size]==$LIMIT")

echo "$RUNS_RESPONSE" | jq -r '.data[] | [
  .id,
  .attributes.status,
  .attributes["created-at"],
  (.attributes.message // "No message" | .[0:50])
] | @tsv' | awk -F'\t' 'BEGIN {
  printf "%-22s %-20s %-26s %s\n", "RUN ID", "STATUS", "CREATED", "MESSAGE"
  printf "%-22s %-20s %-26s %s\n", "------", "------", "-------", "-------"
}
{
  printf "%-22s %-20s %-26s %s\n", $1, $2, $3, $4
}'

echo ""
RUN_COUNT=$(echo "$RUNS_RESPONSE" | jq -r '.data | length')
echo "📊 Total: $RUN_COUNT runs"
