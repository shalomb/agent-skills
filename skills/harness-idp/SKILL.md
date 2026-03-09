---
name: harness-idp
description: Execute Harness.io IDP Scaffolder templates and workflows programmatically. Use this skill to list/discover workflows, components, APIs, query the service catalog, and launch infrastructure/deployment configurations. It can manage and audit API keys, track execution status, integrate IDP tasks into pipelines, and discover project infrastructure dependencies or user access control. Trigger this when the user mentions Harness, IDP, Scaffolder, idp.harness.io, templates, entity groups, or Harness service registry/catalog.
---

# Harness IDP Skill

This skill provides programmatic interaction with the Harness.io IDP Scaffolder API.

## Prerequisites
- Valid credentials: `HARNESS_ACCOUNT_ID` and `HARNESS_API_KEY` environment variables.

## Usage Instructions

This skill has a massive API surface. **DO NOT GUESS ENDPOINTS OR PYTHON BOILERPLATE.**
Whenever you need to interact with the Harness API or perform any of the core capabilities (like executing a Scaffolder template, polling tasks, or auditing API keys), you must first read the detailed reference documentation:

1. Read `references/harness-api.md` to find the exact endpoints, schemas, and complete Python examples for:
   - Creating and monitoring Scaffolder tasks
   - Discovering entities, groups, and the service catalog
   - Managing and auditing API keys
   - Querying project governance, collaborators, and infrastructure connectors
   - Pipeline execution and variable tracking
   
2. Use the Python snippets provided in the reference document to build scripts in the `scripts/` directory or run them directly via your tools.

For any complex operations, write a self-contained Python script to execute the operation rather than doing it inline.
