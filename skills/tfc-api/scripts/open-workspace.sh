#!/usr/bin/env bash
# open-workspace.sh: Auto-detect and open TFC workspace in browser

set -o errexit -o nounset -o noclobber -o pipefail

[[ ${DEBUG-} ]] && set -xv

if [[ -e .terraform/terraform.tfstate ]]; then
  # Pull organization and workspace name from .terraform/terraform.tfstate
  # This path requires that terraform init has been run
  organization=$(< .terraform/terraform.tfstate jq -Scr '.backend.config.organization')
  workspace=$(<    .terraform/terraform.tfstate jq -Scr '.backend.config.workspaces.name')
else
  # Fallback
  # Pull organization and workspace name from the remote backend definition in terraform.tf
  echo >&2 "Parsing workspace and organization from terraform.tf"
  workspace=$(grep -A 2 'workspaces' terraform.tf | awk -F'"' '/name.* =/{ print $2 }' | tr -d '\n')
  organization=$(awk -F'"' '/organization/{ print $2 }' terraform.tf)
fi

if [[ -z "$organization" ]] || [[ -z "$workspace" ]]; then
  echo >&2 "Error: Could not determine organization and workspace"
  exit 1
fi

echo >&2 "Opening workspace: $organization/$workspace"

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

"$open" "https://app.terraform.io/app/$organization/workspaces/$workspace"
