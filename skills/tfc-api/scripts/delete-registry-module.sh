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

# Get TFC token
TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json)

if [[ -z "$TFC_TOKEN" || "$TFC_TOKEN" == "null" ]]; then
  echo "Error: TFC token not found in ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

# Delete the module
echo "Deleting registry module: ${ORG}/${NAMESPACE}/${NAME}/${PROVIDER}"

RESPONSE=$(curl -s -X DELETE \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/${ORG}/registry-modules/private/${NAMESPACE}/${NAME}/${PROVIDER}")

# Check for errors in response
if echo "$RESPONSE" | jq -e '.errors' > /dev/null 2>&1; then
  echo "Error deleting module:"
  echo "$RESPONSE" | jq '.errors'
  exit 1
fi

echo "✓ Module deleted successfully"
