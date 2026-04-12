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

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

echo "Applying run $RUN_ID..."
RESPONSE=$(http --ignore-stdin --quiet POST "https://app.terraform.io/api/v2/runs/$RUN_ID/actions/apply" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json" \
  comment="$COMMENT")

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
