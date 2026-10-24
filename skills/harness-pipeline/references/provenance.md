# Harness OpenAPI & Schema Provenance

## Upstream Sources

### 1. Official Harness Platform API Specifications
- **Provider Index**: [https://apis.io/providers/harness/](https://apis.io/providers/harness/)
- **Upstream Repository**: [https://github.com/api-evangelist/harness](https://github.com/api-evangelist/harness)
  - Monolithic Platform OpenAPI: `openapi/_original/harness-apis-openapi.yaml`
  - Pipelines API: `openapi/harness-pipelines-api-openapi.yml`
  - Pipeline Execution API: `openapi/harness-pipeline-execution-api-openapi.yml`

### 2. Official Harness NextGen Pipeline JSON Schema
- **Repository**: [https://github.com/harness/harness-schema](https://github.com/harness/harness-schema)
- **Pipeline Schema**: `v0/pipeline.json` (Used by Harness Pipeline Studio and IDEs)
- **Template Schema**: `v0/template.json`
- **Trigger Schema**: `v0/trigger.json`

Both the schemas and specs are downloaded and cached automatically on demand via `scripts/bootstrap_schemas.py`.
