---
name: tfc-api
description: Query Terraform Cloud (TFC) workspaces, runs, plans, and logs via API. Use when inspecting TFC workspace state, checking run history, analyzing plan output, reviewing apply logs, or managing infrastructure changes.
---

# Terraform Cloud API Skill

This skill provides programmatic interaction with the Terraform Cloud (TFC) API for managing workspaces, runs, modules, and logs.

## Prerequisites
- TFC token at `~/.terraform.d/credentials.tfrc.json`
- `jq` and `curl` installed

## Usage Instructions

This skill has a collection of scripts to automate interactions with Terraform Cloud. **DO NOT GUESS ENDPOINTS OR WRITE RAW CURL REQUESTS MANUALLY** unless necessary.

1. When you need to interact with Terraform Cloud (e.g. trigger runs, check registry modules, apply runs, extract logs), you must first read the detailed reference documentation:
   - Use the `read` tool on `references/tfc-api-reference.md` for workspace, run, and module operations.
   - Use the `read` tool on `references/tfc-vcs-validation.md` for validating workspace VCS configurations and handling repository redirects.
   
2. Use the provided shell scripts in the `scripts/` directory as described in the reference documents.

3. **VCS Configuration Best Practices**:
   - Before bulk operations on workspaces, validate VCS configurations (see tfc-vcs-validation.md)
   - Check that repository names haven't changed (handle 301 redirects)
   - Verify user has sufficient permissions on target repositories

By following the reference guides, you will avoid incorrect API interactions and successfully automate TFC tasks.