---
name: harness-gitops
description: Use when authoring, configuring, reviewing, or managing Harness GitOps and Argo CD applications, ApplicationSets, repositories, clusters, sync policies, or GitOps agent mappings.
---

# Harness GitOps Skill

Configure, author, and manage declarative Harness GitOps (Argo CD-based) applications, clusters, repositories, and sync workflows.

## Prerequisites
- For API operations: credentials configured via 12-factor hierarchy (CLI flags > ENV > `~/.config/harness/<profile>`).
- For offline YAML authoring: no credentials needed.

## Core Invariants

1. **Argo Application Alignment**:
   - Harness GitOps builds on Argo CD core primitives (`Application`, `ApplicationSet`, `AppProject`).
   - All managed applications bind to a specific `agentIdentifier` (Harness GitOps Agent installed in the target cluster).
2. **Identifier & Scope Formatting**:
   - Identifiers must be alphanumeric/underscore (`^[a-zA-Z_][0-9a-zA-Z_]{0,127}$`).
   - Sync policies must specify automated prune, self-heal, and sync options explicitly to avoid unexpected mutations.
3. **12-Factor Configuration**:
   - Uses `scripts/harness_config.py` for API interaction with `/gitops/api/v1/agents/...` and `/gitops/api/v1/applications/...`.

## Reference Materials
- `references/gitops-application-schema.md`: Application, destination, source (Helm/Kustomize), and syncPolicy structure.
- `references/gitops-agent-guide.md`: Mapping agents, clusters, and repository credentials in Harness.
