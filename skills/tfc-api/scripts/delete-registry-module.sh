#!/bin/bash
# Delete a Terraform Cloud registry module
# Usage: delete-registry-module.sh <organization> <namespace> <name> <provider>
# Example: delete-registry-module.sh example-org example-org MSKProvisioned aws

set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <organization> <namespace> <name> <provider>"
  echo "Example: $0 example-org example-org MSKProvisioned aws"
  exit 1
fi

ORG="$1"
NAMESPACE="$2"
NAME="$3"
PROVIDER="$4"

# Load TFC token using auth helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/auth.sh" || exit 1

# Delete the module
echo "Deleting registry module: ${ORG}/${NAMESPACE}/${NAME}/${PROVIDER}"

RESPONSE=$(http --ignore-stdin --quiet DELETE \
  "https://app.terraform.io/api/v2/organizations/${ORG}/registry-modules/private/${NAMESPACE}/${NAME}/${PROVIDER}" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json")

# Check for errors in response
if echo "$RESPONSE" | jq -e '.errors' > /dev/null 2>&1; then
  echo "Error deleting module:"
  echo "$RESPONSE" | jq '.errors'
  exit 1
fi

echo "✓ Module deleted successfully"
