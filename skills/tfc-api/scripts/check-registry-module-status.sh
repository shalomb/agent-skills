#!/bin/bash
# Check status of a Terraform Cloud registry module
# Usage: check-registry-module-status.sh <organization> <namespace> <name> <provider>
# Example: check-registry-module-status.sh example-org example-org MSKProvisioned aws

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
# Prefer TFC_TOKEN env var; fall back to credentials file
if [ -z "${TFC_TOKEN:-}" ] || [ "${TFC_TOKEN:-}" = "null" ]; then
  TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "")
fi

if [[ -z "$TFC_TOKEN" || "$TFC_TOKEN" == "null" ]]; then
  echo "Error: TFC token not found in ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

# Get module status
RESPONSE=$(curl -s -X GET \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  "https://app.terraform.io/api/v2/organizations/${ORG}/registry-modules/private/${NAMESPACE}/${NAME}/${PROVIDER}")

# Check for errors in response
if echo "$RESPONSE" | jq -e '.errors' > /dev/null 2>&1; then
  echo "Error retrieving module status:"
  echo "$RESPONSE" | jq '.errors'
  exit 1
fi

# Extract module details
STATUS=$(echo "$RESPONSE" | jq -r '.data.attributes.status')
PUBLISHING_MECHANISM=$(echo "$RESPONSE" | jq -r '.data.attributes.publishing_mechanism')
VCS_REPO=$(echo "$RESPONSE" | jq -r '.data.attributes.vcs_repo.identifier // "not configured"')
CREATED_AT=$(echo "$RESPONSE" | jq -r '.data.attributes.created_at')
UPDATED_AT=$(echo "$RESPONSE" | jq -r '.data.attributes.updated_at')
PUBLISHED_AT=$(echo "$RESPONSE" | jq -r '.data.attributes.published_at // "not published"')

echo "Registry Module Status"
echo "===================="
echo ""
echo "Module: ${NAMESPACE}/${NAME}/${PROVIDER}"
echo "Organization: ${ORG}"
echo ""
echo "Status Information:"
echo "  Status: ${STATUS}"
echo "  Publishing Mechanism: ${PUBLISHING_MECHANISM}"
echo "  VCS Repository: ${VCS_REPO}"
echo ""
echo "Timestamps:"
echo "  Created: ${CREATED_AT}"
echo "  Updated: ${UPDATED_AT}"
echo "  Published: ${PUBLISHED_AT}"
echo ""

# Display full response for reference
echo "Full Response:"
echo "$RESPONSE" | jq '.data.attributes | {name, status, publishing_mechanism, vcs_repo, created_at, updated_at, published_at}'
