#!/usr/bin/env bash
set -euo pipefail

# Get plan output from a TFC run
# Usage: ./get-plan.sh <run-id>

RUN_ID="${1:-}"

if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 <run-id>"
  echo "Example: $0 run-2rzGeZbvRwLRCQgQ"
  exit 1
fi

# Get TFC token
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

if [ "$TFC_TOKEN" = "null" ] || [ -z "$TFC_TOKEN" ]; then
  echo "❌ TFC token not found at ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

echo "📋 Fetching run: $RUN_ID"
echo ""

# Get run details
RUN_RESPONSE=$(curl -s --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/runs/$RUN_ID?include=plan")

# Extract metadata
echo "📊 Run Metadata:"
echo "$RUN_RESPONSE" | jq -r '.data.attributes | {
  status: .status,
  message: (.message // "No message"),
  "created-at": ."created-at",
  "has-changes": ."has-changes",
  "resource-additions": ."resource-additions",
  "resource-changes": ."resource-changes",
  "resource-destructions": ."resource-destructions"
}'
echo ""

# Get plan ID
PLAN_ID=$(echo "$RUN_RESPONSE" | jq -r '.data.relationships.plan.data.id')

if [ "$PLAN_ID" = "null" ] || [ -z "$PLAN_ID" ]; then
  echo "❌ No plan found for this run"
  exit 1
fi

echo "✅ Plan ID: $PLAN_ID"
echo ""

# Get plan log URL
PLAN_DETAILS=$(curl -s --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/plans/$PLAN_ID")

LOG_URL=$(echo "$PLAN_DETAILS" | jq -r '.data.attributes["log-read-url"]')

if [ "$LOG_URL" = "null" ] || [ -z "$LOG_URL" ]; then
  echo "❌ Plan log not available"
  exit 1
fi

# Download logs
TEMP_LOG="/tmp/tfc-plan-$PLAN_ID.jsonl"
curl -s "$LOG_URL" > "$TEMP_LOG"
echo "📝 Plan log saved to: $TEMP_LOG"
echo ""

# Parse and display key information
echo "🔄 Planned Changes:"
echo "==================="
grep '"type":"planned_change"' "$TEMP_LOG" | jq -r '."@message"' | sort -u
echo ""

echo "📊 Change Summary:"
grep '"type":"change_summary"' "$TEMP_LOG" | jq -r '."@message"'
echo ""

echo "⚠️  Warnings:"
if grep -q '"severity":"warning"' "$TEMP_LOG"; then
  grep '"severity":"warning"' "$TEMP_LOG" | jq -r '.diagnostic.summary' | sort -u | head -5
else
  echo "  None"
fi
echo ""

echo "❌ Errors:"
if grep -q '"severity":"error"' "$TEMP_LOG"; then
  grep '"severity":"error"' "$TEMP_LOG" | jq -r '.diagnostic.summary + ": " + .diagnostic.detail' | head -5
else
  echo "  None"
fi
echo ""

echo "💡 Full log available at: $TEMP_LOG"
