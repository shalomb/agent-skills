#!/usr/bin/env bash
set -euo pipefail

# Trigger a Terraform Cloud run (optionally a destroy run).
# Usage: ./trigger-run.sh <org> <workspace> [is-destroy] [message]

ORG="${1:-}"
WORKSPACE_NAME="${2:-}"
IS_DESTROY="${3:-false}"
MESSAGE="${4:-"Run triggered via API"}"

if [ -z "$ORG" ] || [ -z "$WORKSPACE_NAME" ]; then
  echo "Usage: $0 <org> <workspace> [is-destroy] [message]"
  echo "Example: $0 example-org tec-man-sup-tst-90622-iacre true 'Decommission infrastructure'"
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

# 1. Get Workspace ID
echo "🔍 Fetching workspace ID for $ORG/$WORKSPACE_NAME..."
WORKSPACE_ID=$(curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/$ORG/workspaces/$WORKSPACE_NAME" \
  | jq -r '.data.id // empty')

if [ -z "$WORKSPACE_ID" ] || [ "$WORKSPACE_ID" == "null" ]; then
  echo "❌ Error: Could not find workspace ID for $ORG/$WORKSPACE_NAME" >&2
  exit 1
fi
echo "✅ Workspace ID: $WORKSPACE_ID"

# 2. Trigger Run
echo "🚀 Triggering run (is-destroy: $IS_DESTROY)..."
RUN_ID=$(jq -n \
  --arg is_destroy "$IS_DESTROY" \
  --arg msg "$MESSAGE" \
  --arg wid "$WORKSPACE_ID" \
  '{
    data: {
      attributes: {
        "is-destroy": ($is_destroy == "true"),
        message: $msg
      },
      type: "runs",
      relationships: {
        workspace: {
          data: {
            type: "workspaces",
            id: $wid
          }
        }
      }
    }
  }' | http POST "https://app.terraform.io/api/v2/runs" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json" \
  | jq -r '.data.id // empty')

if [ -z "$RUN_ID" ] || [ "$RUN_ID" == "null" ]; then
  echo "❌ Error triggering run." >&2
  exit 1
fi

echo "✅ Run triggered successfully: $RUN_ID"
echo "🔗 View run: https://app.terraform.io/app/$ORG/workspaces/$WORKSPACE_NAME/runs/$RUN_ID"
echo "$RUN_ID"
