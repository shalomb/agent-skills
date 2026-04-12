#!/bin/bash
# Publish a Terraform Cloud registry module via VCS integration
# Usage: publish-registry-module-vcs.sh <organization> <github-repo> <oauth-token-id> [display-identifier]
# Example: publish-registry-module-vcs.sh example-org example-org/terraform-aws-MSKProvisioned ot-EXAMPLE-OAUTH-TOKEN-ID

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <organization> <github-repo> <oauth-token-id> [display-identifier]"
  echo "Example: $0 example-org example-org/terraform-aws-MSKProvisioned ot-EXAMPLE-OAUTH-TOKEN-ID"
  echo ""
  echo "Note: github-repo should be in format 'owner/repo'"
  echo "      oauth-token-id can be found at: https://app.terraform.io/app/settings/tokens"
  exit 1
fi

ORG="$1"
GITHUB_REPO="$2"
OAUTH_TOKEN_ID="$3"
DISPLAY_ID="${4:-$GITHUB_REPO}"

# Get TFC token
# Prefer TFC_TOKEN env var; fall back to credentials file
if [ -z "${TFC_TOKEN:-}" ] || [ "${TFC_TOKEN:-}" = "null" ]; then
  TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "")
fi

if [[ -z "$TFC_TOKEN" || "$TFC_TOKEN" == "null" ]]; then
  echo "Error: TFC token not found in ~/.terraform.d/credentials.tfrc.json"
  exit 1
fi

# Validate oauth token ID format
if [[ ! "$OAUTH_TOKEN_ID" =~ ^ot- ]]; then
  echo "Error: OAuth token ID should start with 'ot-' (e.g., ot-EXAMPLE-OAUTH-TOKEN-ID)"
  exit 1
fi

# Create module via VCS endpoint
echo "Publishing registry module from GitHub: ${GITHUB_REPO}"
echo "Organization: ${ORG}"
echo "OAuth Token ID: ${OAUTH_TOKEN_ID}"
echo ""

RESPONSE=$(jq -n \
  --arg repo "${GITHUB_REPO}" \
  --arg otid "${OAUTH_TOKEN_ID}" \
  --arg display "${DISPLAY_ID}" \
  '{
    data: {
      type: "registry-modules",
      attributes: {
        "vcs-repo": {
          identifier: $repo,
          "oauth-token-id": $otid,
          "display-identifier": $display,
          tags: true,
          "ingress-submodules": true
        }
      },
      "no-code": false
    }
  }' | http --ignore-stdin --quiet POST "https://app.terraform.io/api/v2/organizations/${ORG}/registry-modules/vcs" \
  "Authorization: Bearer $TFC_TOKEN" \
  "Content-Type: application/vnd.api+json")

# Check for errors in response
if echo "$RESPONSE" | jq -e '.errors' > /dev/null 2>&1; then
  echo "Error publishing module:"
  echo "$RESPONSE" | jq '.errors'
  exit 1
fi

# Extract module details
MODULE_ID=$(echo "$RESPONSE" | jq -r '.data.id')
STATUS=$(echo "$RESPONSE" | jq -r '.data.attributes.status')
PUBLISHING_MECHANISM=$(echo "$RESPONSE" | jq -r '.data.attributes.publishing_mechanism')
VCS_REPO=$(echo "$RESPONSE" | jq -r '.data.attributes.vcs_repo.identifier')

echo "✓ Module published successfully"
echo ""
echo "Module Details:"
echo "  ID: ${MODULE_ID}"
echo "  Status: ${STATUS}"
echo "  Publishing Mechanism: ${PUBLISHING_MECHANISM}"
echo "  VCS Repository: ${VCS_REPO}"
echo ""
echo "Next: Monitor module status at https://app.terraform.io/app/${ORG}/registry/modules"
