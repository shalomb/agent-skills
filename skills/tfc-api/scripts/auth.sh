#!/usr/bin/env bash
# TFC Authentication Helper
# Use this script to load a TFC token from the environment or ~/.terraform.d/credentials.tfrc.json

# If TFC_TOKEN is not already set, try to load it from the credentials file
if [ -z "${TFC_TOKEN:-}" ] || [ "${TFC_TOKEN:-}" = "null" ]; then
  TFC_TOKEN=$(jq -r '.credentials."app.terraform.io".token' ~/.terraform.d/credentials.tfrc.json 2>/dev/null || echo "")
fi

# Exit if no token is found
if [ -z "$TFC_TOKEN" ] || [ "$TFC_TOKEN" = "null" ]; then
  echo "❌ TFC token not found. Set TFC_TOKEN or configure ~/.terraform.d/credentials.tfrc.json" >&2
  return 1 2>/dev/null || exit 1
fi

export TFC_TOKEN
