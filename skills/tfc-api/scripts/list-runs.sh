#!/usr/bin/env bash
set -euo pipefail

# List runs for a TFC workspace
# Usage: ./list-runs.sh <org> <workspace> [limit]

ORG="${1:-}"
WORKSPACE="${2:-}"
LIMIT="${3:-20}"

if [ -z "$ORG" ] || [ -z "$WORKSPACE" ]; then
  echo "Usage: $0 <org> <workspace> [limit]"
  echo "Example: $0 my-org my-workspace 10"
  exit 1
fi

# Get TFC token
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

if [ "$TFC_TOKEN" = "null" ] || [ -z "$TFC_TOKEN" ]; then
  echo "❌ TFC token not found at ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

# Get workspace ID
echo "🔍 Fetching workspace: $ORG/$WORKSPACE"
WORKSPACE_RESPONSE=$(curl -s --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/$ORG/workspaces/$WORKSPACE")

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

RUNS_RESPONSE=$(curl -s --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/workspaces/$WORKSPACE_ID/runs?page%5Bsize%5D=$LIMIT")

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
