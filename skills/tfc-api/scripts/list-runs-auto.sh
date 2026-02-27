#!/usr/bin/env bash
set -euo pipefail

# List runs for current workspace (auto-detected from terraform config)
# Usage: ./list-runs-auto.sh [terraform-config-dir] [limit]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG_DIR="${1:-.}"
LIMIT="${2:-20}"

# Get workspace info
WORKSPACE_INFO=$("$SCRIPT_DIR/get-workspace-info.sh" "$CONFIG_DIR")

ORG=$(echo "$WORKSPACE_INFO" | jq -r '.organization')
WORKSPACE=$(echo "$WORKSPACE_INFO" | jq -r '.workspace')
URL=$(echo "$WORKSPACE_INFO" | jq -r '.url')

echo "🔍 Detected workspace: $ORG/$WORKSPACE"
echo "🔗 $URL"
echo ""

# Call the main list-runs script
"$SCRIPT_DIR/list-runs.sh" "$ORG" "$WORKSPACE" "$LIMIT"
