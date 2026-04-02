#!/usr/bin/env bash
set -euo pipefail

# Confirm/Apply a Terraform Cloud run that is in "planned" status.
# Usage: ./apply-run.sh <run-id> [comment]

RUN_ID="${1:-}"
COMMENT="${2:-"Confirming run via API"}"

if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 <run-id> [comment]"
  exit 1
fi

# Load TFC token
if [ ! -f ~/.terraform.d/credentials.tfrc.json ]; then
  echo "❌ Error: ~/.terraform.d/credentials.tfrc.json not found" >&2
  exit 1
fi
# Prefer TFC_TOKEN env var; fall back to credentials file
if [ -z "${TFC_TOKEN:-}" ] || [ "${TFC_TOKEN:-}" = "null" ]; then
  TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "")
fi

echo "Applying run $RUN_ID..."
RESPONSE=$(curl -s -X POST \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  -d "{\"comment\": \"$COMMENT\"}" \
  "https://app.terraform.io/api/v2/runs/$RUN_ID/actions/apply")

if [ "$RESPONSE" == "null" ] || [ -z "$RESPONSE" ]; then
  echo "✅ Apply triggered successfully (or run is already applying/applied)."
else
  # Check for errors in response
  ERROR=$(echo "$RESPONSE" | jq -r '.errors[0].detail // empty')
  if [ -n "$ERROR" ]; then
    echo "❌ Error applying run: $ERROR"
    exit 1
  else
    echo "✅ Apply action response received."
  fi
fi
