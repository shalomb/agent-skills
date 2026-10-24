---
name: harness-pipeline
description: Use when authoring, modifying, reviewing, validating, reverse-engineering, or executing Harness NextGen CD/CI pipelines in YAML, configuring deployment/custom stages and step groups, inspecting live pipelines, or triggering runs via API.
---

# Harness Pipeline Skill

Author, reverse-engineer live pipelines, validate offline against official Harness JSON schemas, and trigger Harness NextGen CI/CD pipelines via REST API.

## Core Rules & Invariants

1. **Deterministic Verification First**:
   - Always run the offline validator before committing or deploying any pipeline YAML:
     ```bash
     python3 <skill-dir>/scripts/validate_pipeline_yaml.py <path/to/pipeline.yaml>
     ```
2. **Identifier Constraints**:
   - Every `identifier` (pipeline, stage, stepGroup, step) must strictly match `^[a-zA-Z_][0-9a-zA-Z_]{0,127}$` (underscores only, no hyphens).
   - Names allow spaces, hyphens, and periods: `^[a-zA-Z_0-9-.][-0-9a-zA-Z_\s.]{0,127}$`.
3. **Execution Hierarchy**:
   - `stages` is an array of stage wrappers: `- stage: { name, identifier, type, spec: { execution: { steps: [...] } } }`.
   - Each item in `steps` must be wrapped:
     - Standard step: `- step: { type, name, identifier, spec: { ... } }`
     - Step group: `- stepGroup: { name, identifier, steps: [...] }`
     - Parallel execution: `- parallel: [...]`
   - Never write `- steps:` inside a steps list (invalid syntax).
4. **JEXL Expressions Syntax**:
   - Harness expressions use `<+namespace.variable>`. See `references/jexl-reference.md`.
5. **12-Factor Configuration**:
   - API execution and extraction scripts resolve configuration in priority order: CLI flags > environment variables (`HARNESS_API_KEY`, `HARNESS_ACCOUNT_ID`, etc.) > `~/.config/harness/<profile>`.

## Workflows

### 1. Reverse-Engineering Live Pipelines from Harness
Extract the full YAML definition of any live pipeline from Pipeline Studio:
```bash
python3 <skill-dir>/scripts/get_pipeline.py --pipeline <pipeline-id> --project <project-id> [--org <org-id>] [--output pipeline.yaml]
```
See `references/pipeline-reverse-engineering.md`.

### 2. Authoring & Validating Pipelines Offline
1. Select stage and step types from `references/step-catalog.md` and `references/stage-and-step-patterns.md`.
2. Start from `assets/starter-pipeline.yaml` or an exported pipeline.
3. Validate offline:
   ```bash
   python3 <skill-dir>/scripts/validate_pipeline_yaml.py <pipeline-file>
   ```

### 3. Triggering & Running Pipelines via API
Trigger pipeline execution using 12-factor configuration:
```bash
python3 <skill-dir>/scripts/execute_pipeline.py --pipeline <pipeline-id> --project <project-id> [--org <org-id>] [--inputs <inputs.yaml>]
```
