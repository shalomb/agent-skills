# Reverse-Engineering Live Harness Pipelines

## Overview

Harness exposes two REST endpoints to extract the full YAML specification of any pipeline deployed in Pipeline Studio:

1. **V1 Pipeline API**:
   ```http
   GET /v1/orgs/{org}/projects/{project}/pipelines/{pipeline}
   Harness-Account: <account_id>
   x-api-key: <api_key>
   ```
   **Returns**: JSON document containing the complete raw `pipeline_yaml` string along with metadata (`modules`, `tags`, `git_details`, `valid`).

2. **NextGen Gateway API**:
   ```http
   GET /gateway/pipeline/api/pipelines/{pipeline}?accountIdentifier={account}&orgIdentifier={org}&projectIdentifier={project}
   x-api-key: <api_key>
   ```

## Extracting Pipeline YAML via CLI

Use the bundled script in `scripts/get_pipeline.py`:

```bash
python3 scripts/get_pipeline.py \
  --pipeline <pipeline_id> \
  --org <org_id> \
  --project <project_id> \
  --output ./exported-pipeline.yaml
```

The script adheres to 12-factor configuration, resolving credentials and account details automatically from environment variables or `~/.config/harness/<profile>`.

## Validating the Extracted Pipeline

Immediately validate the exported YAML against the official JSON Schema and JEXL rules:

```bash
python3 scripts/validate_pipeline_yaml.py ./exported-pipeline.yaml
```
