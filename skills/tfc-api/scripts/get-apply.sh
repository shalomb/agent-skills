#!/usr/bin/env bash
set -euo pipefail

# Get apply output from a TFC run
# Usage: ./get-apply.sh <run-id>

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
  "https://app.terraform.io/api/v2/runs/$RUN_ID?include=apply")

# Extract metadata
echo "📊 Run Metadata:"
echo "$RUN_RESPONSE" | jq -r '.data.attributes | {
  status: .status,
  message: (.message // "No message"),
  "created-at": ."created-at",
  "has-changes": ."has-changes"
}'
echo ""

# Get apply ID
APPLY_ID=$(echo "$RUN_RESPONSE" | jq -r '.data.relationships.apply.data.id')

if [ "$APPLY_ID" = "null" ] || [ -z "$APPLY_ID" ]; then
  echo "⚠️  No apply found for this run (may be plan-only or not yet applied)"
  exit 0
fi

echo "✅ Apply ID: $APPLY_ID"
echo ""

# Get apply log URL
APPLY_DETAILS=$(curl -s --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/applies/$APPLY_ID")

LOG_URL=$(echo "$APPLY_DETAILS" | jq -r '.data.attributes["log-read-url"]')

if [ "$LOG_URL" = "null" ] || [ -z "$LOG_URL" ]; then
  echo "❌ Apply log not available"
  exit 1
fi

# Get apply status
APPLY_STATUS=$(echo "$APPLY_DETAILS" | jq -r '.data.attributes.status')
echo "📊 Apply Status: $APPLY_STATUS"
echo ""

# Download logs
TEMP_LOG="/tmp/tfc-apply-$APPLY_ID.jsonl"
curl -s "$LOG_URL" > "$TEMP_LOG"
echo "📝 Apply log saved to: $TEMP_LOG"
echo ""

# Parse and display key information
echo "✅ Resources Created:"
if grep -q '"type":"apply_complete"' "$TEMP_LOG" && grep -q '"action":"create"' "$TEMP_LOG"; then
  grep '"type":"apply_complete"' "$TEMP_LOG" | jq -r 'select(.hook.action == "create") | "  + " + .hook.resource.addr' | head -10
else
  echo "  None"
fi
echo ""

echo "🔄 Resources Modified:"
if grep -q '"type":"apply_complete"' "$TEMP_LOG" && grep -q '"action":"update"' "$TEMP_LOG"; then
  grep '"type":"apply_complete"' "$TEMP_LOG" | jq -r 'select(.hook.action == "update") | "  ~ " + .hook.resource.addr' | head -10
else
  echo "  None"
fi
echo ""

echo "❌ Resources Destroyed:"
if grep -q '"type":"apply_complete"' "$TEMP_LOG" && grep -q '"action":"delete"' "$TEMP_LOG"; then
  grep '"type":"apply_complete"' "$TEMP_LOG" | jq -r 'select(.hook.action == "delete") | "  - " + .hook.resource.addr' | head -10
else
  echo "  None"
fi
echo ""

echo "⚠️  Errors:"
if grep -q '"severity":"error"' "$TEMP_LOG"; then
  grep '"severity":"error"' "$TEMP_LOG" | jq -r '.diagnostic.summary + ": " + .diagnostic.detail' | head -5
else
  echo "  None"
fi
echo ""

echo "💡 Full log available at: $TEMP_LOG"
