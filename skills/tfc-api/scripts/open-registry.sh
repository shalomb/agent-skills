#!/usr/bin/env bash
# open-registry.sh: Open Terraform registry for current module

set -o errexit -o nounset -o noclobber -o pipefail

[[ ${DEBUG-} ]] && set -xv

url=$(git remote get-url origin 2>/dev/null || echo "")

if [[ -z "$url" ]]; then
  echo >&2 "Error: Not a git repository or no remote origin"
  exit 1
fi

url="${url%.git}"
module_name="${url##*/terraform-aws-}"

# If not a terraform-aws-* module, try to extract module name differently
if [[ "$module_name" == "$url" ]]; then
  module_name="${url##*/}"
fi

# Try to detect organization from terraform backend or git remote
organization=""

# First try terraform backend
if [[ -e .terraform/terraform.tfstate ]]; then
  organization=$(< .terraform/terraform.tfstate jq -Scr '.backend.config.organization // empty' 2>/dev/null || echo "")
elif [[ -e terraform.tf ]]; then
  organization=$(awk -F'"' '/organization/{ print $2 }' terraform.tf 2>/dev/null || echo "")
fi

# If still no organization, try to extract from git remote
if [[ -z "$organization" ]]; then
  # Try to extract org from github.com/ORG/repo URLs
  if [[ "$url" =~ github\.com[:/]([^/]+)/ ]]; then
    organization="${BASH_REMATCH[1]}"
  fi
fi

if [[ -z "$organization" ]]; then
  echo >&2 "Error: Could not determine organization"
  echo >&2 "Tried: terraform backend config, git remote URL"
  exit 1
fi

echo >&2 "Opening registry: $organization/$module_name"

# Determine browser command
if command -v x-www-browser &>/dev/null; then
  open=x-www-browser
elif command -v open &>/dev/null; then
  open=open
elif command -v xdg-open &>/dev/null; then
  open=xdg-open
else
  echo >&2 "Error: No browser command found (tried x-www-browser, open, xdg-open)"
  exit 1
fi

"$open" "https://app.terraform.io/app/$organization/registry/modules/private/$organization/$module_name/aws"
