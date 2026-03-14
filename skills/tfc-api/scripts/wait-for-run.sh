#!/usr/bin/env bash
set -euo pipefail

# Poll for a Terraform Cloud run status until it reaches a terminal state.
# Usage: ./wait-for-run.sh <run-id> [timeout-seconds] [interval-seconds]

RUN_ID="${1:-}"
TIMEOUT="${2:-600}"
INTERVAL="${3:-10}"

if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 <run-id> [timeout-seconds] [interval-seconds]"
  exit 1
fi

# Load TFC token
if [ ! -f ~/.terraform.d/credentials.tfrc.json ]; then
  echo "❌ Error: ~/.terraform.d/credentials.tfrc.json not found" >&2
  exit 1
fi
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

echo "⏳ Waiting for run $RUN_ID status (timeout: ${TIMEOUT}s, interval: ${INTERVAL}s)..."

START_TIME=$(date +%s)
while true; do
  STATUS=$(curl -s \
    --header "Authorization: Bearer $TFC_TOKEN" \
    --header "Content-Type: application/vnd.api+json" \
    "https://app.terraform.io/api/v2/runs/$RUN_ID" \
    | jq -r '.data.attributes.status // "unknown"')

  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))
  
  echo "$(date +'%H:%M:%S') - Status: $STATUS (Elapsed: ${ELAPSED}s)"

  if [[ "$STATUS" =~ ^(applied|errored|canceled|discarded|planned_and_finished)$ ]]; then
    echo "🏁 Run $RUN_ID reached terminal state: $STATUS"
    break
  elif [ "$STATUS" == "planned" ] || [ "$STATUS" == "cost_estimated" ] || [ "$STATUS" == "policy_checked" ]; then
    # Some terminal-ish states depending on workflow
    # We continue if it's waiting for apply or if policy checks passed
    # But for a fully automated wait, we might want to stop here or wait for confirm
    # For now, we continue waiting until it's applied or failed.
    :
  fi
  
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "❌ Timeout reached waiting for run $RUN_ID"
    exit 1
  fi
  
  sleep "$INTERVAL"
done

echo "$STATUS"
