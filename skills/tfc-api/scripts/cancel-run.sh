#!/usr/bin/env bash
set -euo pipefail

# Cancel a Terraform Cloud run by run ID.
# Usage: ./cancel-run.sh <run-id> [comment]
#
# Use this when a manually-triggered run is superseded by a VCS-triggered run
# and needs to be cancelled to clear the workspace queue.
#
# Example:
#   ./cancel-run.sh run-EXAMPLE123456789 "Superseded by VCS-triggered run run-EXAMPLE987654321"

RUN_ID="${1:-}"
COMMENT="${2:-"Cancelled — superseded by another run"}"

if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 <run-id> [comment]"
  echo "Example: $0 run-EXAMPLE123456789 'Superseded by VCS-triggered run'"
  exit 1
fi

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

echo "🚫 Cancelling run ${RUN_ID}..."
RESPONSE=$(http --ignore-stdin --quiet POST "https://app.terraform.io/api/v2/runs/${RUN_ID}/actions/cancel" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json" \
  comment="${COMMENT}")

# Check response — TFC returns 202 Accepted on success, empty body
if echo "$RESPONSE" | grep -q '"errors"'; then
  echo "❌ Cancel failed:"
  echo "$RESPONSE" | jq '.errors'
  exit 1
fi

echo "✅ Run ${RUN_ID} cancellation requested."
echo "   Comment: ${COMMENT}"
echo "   Verify: https://app.terraform.io/app/{TFC_ORG}/runs/${RUN_ID}"
