# Harness-IDP Skill ↔ Official OpenAPI Spec Cross-Reference

**Status**: 15/20 endpoints matched to official spec. 5 endpoints are internal/undocumented.

**Sources**:
- Official spec: `https://apidocs.harness.io/_bundle/index.json?download` (1685 endpoints, OpenAPI 3.0.3)
- HAR discovery: Real production traffic from Harness UI pipeline execution workflow

---

## ✅ Matched Endpoints (15/20) — In Official Spec

All parameters, request/response schemas, and detailed documentation available in the spec.

### Service Catalog & Entity Management

#### 1. `/v1/entities` — List/Create Entities
- **Our path**: `/gateway/v1/entities`
- **Spec path**: `/v1/entities`
- **Methods**: 
  - `GET`: Retrieve paginated list of entities with filtering
    - Query: `scopes`, `entity_refs`, `type`, `owner`, `lifecycle`, `tags`, `owned_by_me`, `favorites`
  - `POST`: Create new entity
    - Query: `convert` (Backstage→Harness), `dry_run` (validate only)
    - Response: 201 Created — Entity object
- **Use case**: Discover all components, services, APIs, users, groups in catalog

#### 2. `/v1/entities/kinds` — Get Entity Kinds
- **Our path**: `/gateway/v1/entities/kinds`
- **Spec path**: `/v1/entities/kinds`
- **Method**: `GET`
- **Response**: List of entity kinds (e.g., "Component", "API", "Service", "Group", "User") with display names, descriptions, and counts
- **Use case**: Populate filter dropdowns; understand available entity types

#### 3. `/v1/entities/groups` — Entity Groups
- **Our path**: `/gateway/v1/entities/groups`
- **Spec path**: `/v1/entities/groups` (likely under pagination/grouping endpoints)
- **Note**: Spec search suggests this is part of broader entity filtering

---

### Governance & Access Control

#### 4. `/ng/api/organizations/{identifier}` — Organization Details
- **Our path**: `/gateway/ng/api/organizations/{orgId}`
- **Spec path**: `/ng/api/organizations/{identifier}`
- **Methods**: 
  - `GET`: Retrieve org metadata
    - Required query: `accountIdentifier`
  - `PUT`: Update org settings
    - Required: `accountIdentifier`, body with org config
  - `DELETE`: Remove organization
- **Response**: OrganizationResponse (nested schema with settings, metadata)
- **Use case**: Audit org structure, settings, access policies

#### 5. `/ng/api/connectors` — Infrastructure Connectors
- **Our path**: `/gateway/ng/api/connectors`
- **Spec path**: `/ng/api/connectors`
- **Methods**:
  - `GET`: List connectors with filtering
    - Query: `pageIndex`, `pageSize`, `searchTerm`, `type` (AWS, Docker, Git, etc.), `category`, `source_category`
    - Required: `accountIdentifier`
  - `POST`: Create connector
  - `PUT`: Update connector
- **Response**: PageResponseConnectorResponse (paginated list)
- **Use case**: Discover all infrastructure integrations, provider accounts, credentials

#### 6. `/ng/api/apikey/aggregate` — API Key Audit
- **Our path**: `/gateway/ng/api/apikey/aggregate`
- **Spec path**: `/ng/api/apikey/aggregate`
- **Method**: `GET`
- **Query params**:
  - Required: `accountIdentifier`, `apiKeyType` (PAT or ServiceAccount), `parentIdentifier` (service account ID)
  - Optional: `identifiers` (list of specific API key IDs), `pageIndex`, `pageSize`, `searchTerm`
- **Response**: PageResponseApiKeyAggregate (lists all API keys with metadata)
- **Use case**: Audit API key usage, expiration status, access tokens across account

---

### User & Account Settings

#### 7. `/ng/api/user-settings/get-user-preferences` — User UI Preferences
- **Our path**: `/gateway/ng/api/user-settings/get-user-preferences`
- **Spec path**: `/ng/api/user-settings/get-user-preferences`
- **Method**: `GET`
- **Query**: `accountIdentifier` (required)
- **Response**: MapStringString (key-value pairs of user's UI preferences)
- **Use case**: Get current user's settings (theme, sidebar state, etc.)

#### 8. `/ng/api/user-settings` — User Settings CRUD
- **Our path**: `/gateway/ng/api/user-settings`
- **Spec path**: `/ng/api/user-settings`
- **Methods**:
  - `GET`: List settings by category
    - Query: `accountIdentifier` (req), `group` (optional category filter)
    - Response: ListUserSettingResponseDTO
  - `PUT`: Update settings
    - Body: `identifier`, `value`, `updateType` (replace/append), `enableAcrossAccounts`
    - Response: ListUserSettingUpdateResponseDTO
- **Use case**: Audit/modify user account configuration

---

### Pipeline Discovery & Metadata

#### 9. `/pipeline/api/pipelines/summary/{pipelineIdentifier}` — Pipeline Metadata
- **Our path**: `/gateway/pipeline/api/pipelines/summary/{pipelineId}`
- **Spec path**: `/pipeline/api/pipelines/summary/{pipelineIdentifier}`
- **Method**: `GET`
- **Query params**:
  - Required: `accountIdentifier`, `orgIdentifier`, `projectIdentifier`
  - Optional: `branch`, `repoIdentifier`, `getDefaultFromOtherRepo`, `Load-From-Cache` (header)
- **Response**: PMSPipelineSummaryResponse (metadata + execution summary)
- **Use case**: Get lightweight pipeline info (name, description, last execution)

#### 10. `/pipeline/api/pipelines/{pipelineIdentifier}` — Full Pipeline YAML
- **Our path**: `/gateway/pipeline/api/pipelines/{pipelineId}`
- **Spec path**: `/pipeline/api/pipelines/{pipelineIdentifier}`
- **Methods**:
  - `GET`: Retrieve full pipeline definition
    - Query: Same as summary, plus `getTemplatesResolvedPipeline` (resolve template references)
    - Response: PMSPipelineResponse (complete YAML)
  - `PUT`: Update pipeline
  - `DELETE`: Remove pipeline
- **Use case**: Audit/modify pipeline definitions, stage structure, step configuration

---

### Execution Management

#### 11. `/pipeline/api/pipelines/execution/summary` — List Executions
- **Our path**: `/gateway/pipeline/api/pipelines/execution/summary`
- **Spec path**: `/pipeline/api/pipelines/execution/summary`
- **Method**: `POST` (not GET!)
- **Query params**:
  - Required: `accountIdentifier`, `orgIdentifier`, `projectIdentifier`
  - Optional: `pipelineIdentifier`, `searchTerm`, `page` (0-based), `size` (20 default), `sort` (array), `status` (array)
  - Optional: `myDeployments` (bool), `module` (filter by module type)
- **Body** (optional): `{ "filterType": "PipelineExecution", "tags": {...} }`
- **Response**: PagePipelineExecutionSummary (paginated list with metadata)
- **Use case**: Get execution history, success rates, execution audit trail

#### 12. `/pipeline/api/pipelines/execution/v2/{planExecutionId}` — Execution Details
- **Our path**: `/gateway/pipeline/api/pipelines/execution/v2/{executionId}`
- **Spec path**: `/pipeline/api/pipelines/execution/v2/{planExecutionId}`
- **Method**: `GET`
- **Query params**:
  - Required: `accountIdentifier`, `orgIdentifier`, `projectIdentifier`, `planExecutionId` (path)
  - Optional: `stageNodeId`, `stageNodeExecutionId`, `renderFullBottomGraph` (full step tree)
- **Response**: PipelineExecutionDetail (nodeExecutionMap, edges, logs, outputs)
- **Use case**: Get detailed execution tree, step-level results, task logs

---

### Input Sets & Pipeline Execution

#### 13. `/pipeline/api/inputSets/template` — Input Set Template
- **Our path**: `/gateway/pipeline/api/inputSets/template`
- **Spec path**: `/pipeline/api/inputSets/template`
- **Method**: `POST`
- **Query params**:
  - Required: `accountIdentifier`, `orgIdentifier`, `projectIdentifier`, `pipelineIdentifier`
  - Optional: `branch`, `repoIdentifier`, `Load-From-Cache` (header)
- **Body** (optional): `{ "stageIdentifiers": [...] }` (to filter specific stages)
- **Response**: InputSetTemplateWithReplacedExpressionsResponse
  - Contains: `inputSetTemplateYaml`, `modules`, `hasInputSets`
  - Template shows all variables with regex patterns, descriptions, default values
- **Use case**: Discover available pipeline variables and their constraints

#### 14. `/pipeline/api/inputSets/merge` — Merge Input Sets
- **Our path**: `/gateway/pipeline/api/inputSets/merge`
- **Spec path**: `/pipeline/api/inputSets/merge`
- **Method**: `POST`
- **Query params**:
  - Required: `accountIdentifier`, `orgIdentifier`, `projectIdentifier`, `pipelineIdentifier`
  - Optional: `pipelineRepoID`, `pipelineBranch`, `branch`, `repoIdentifier`, `getDefaultFromOtherRepo`
- **Body** (required):
  ```json
  {
    "inputSetReferences": ["inputset-1", "inputset-2"],
    "withMergedPipelineYaml": true,
    "stageIdentifiers": [],
    "lastYamlToMerge": "pipeline:\n  variables:\n    - name: foo\n      value: bar"
  }
  ```
- **Response**: MergeInputSetResponse (`pipelineYaml`, `completePipelineYaml`)
- **Use case**: Preview merged configuration before execution; compose multiple input sets

#### 15. `/pipeline/api/pipeline/execute/{identifier}` — Execute Pipeline
- **Our path**: `/gateway/pipeline/api/pipeline/execute/{pipelineId}`
- **Spec path**: `/pipeline/api/pipeline/execute/{identifier}`
- **Method**: `POST`
- **Query params**:
  - Required: `accountIdentifier`, `orgIdentifier`, `projectIdentifier`, `identifier` (path = pipelineId)
  - Optional: `branch`, `repoIdentifier`, `notifyOnlyUser`, `inputSetIdentifiers` (array, multi-value), `asyncPlanCreation`
- **Body** (optional, but typically needed): YAML format pipeline with variables set
  ```yaml
  pipeline:
    identifier: my-pipeline
    variables:
      - name: apms_id
        value: "92203"
      - name: workspace_name
        value: "prod-us-east"
  ```
- **Response**: PlanExecutionResponse (`planExecution` with `uuid`, `status`, `startTs`, `metadata`)
- **Use case**: Programmatically trigger pipeline execution with variable values

---

## ⚠️ Unmatched Endpoints (5/20) — NOT in Official Spec

These endpoints work in production (verified via HAR) but are **internal/undocumented**. 
Consider these "discovered" APIs; they may change without notice.

### 1. `/gateway/ng/api/aggregate/projects/{projectId}` 
- **Purpose**: Aggregate project details with collaborators, access list
- **Status**: ⚠️ **NOT in spec** — Use documented v1 endpoint instead
- **Recommended replacement**: `/ng/api/projects/{identifier}` (spec)
- **Note**: The gateway route may be an internal optimization; prefer public API

### 2. `/gateway/ng/api/entitySetupUsage/getOrgEntitiesReferredByProject`
- **Purpose**: Get which connectors/entities are used within a project
- **Status**: ⚠️ **NOT in spec** — Likely internal dependency graph endpoint
- **Recommended replacement**: Query `/ng/api/connectors` + inspect pipeline YAML for references
- **Note**: No public API for this; may need to reverse-engineer from pipeline definitions

### 3. `/gateway/ng-dashboard/api/overview/resources-overview-count`
- **Purpose**: Account-level resource metrics (projects, services, pipelines, users count)
- **Status**: ⚠️ **NOT in spec** — Dashboard-specific, internal API
- **Recommended replacement**: Query individual endpoints (`/ng/api/connectors`, `/ng/api/organizations`, etc.) and aggregate
- **Note**: No official API for this aggregate view

### 4. `/gateway/pipeline/api/pipelines/list-repos`
- **Purpose**: List git repositories available to a project
- **Status**: ⚠️ **NOT in spec** — Connector-specific discovery
- **Recommended replacement**: Use `/ng/api/connectors` with `type=GitConnector`, then query the connector's repos
- **Note**: Repo listing is provider-specific; use connector test endpoint

### 5. `/gateway/pipeline/api/pipelines/v2/variables`
- **Purpose**: Get pipeline variable metadata (POST, pass raw YAML)
- **Status**: ⚠️ **NOT in spec** — But `/pipeline/api/inputSets/template` is the official way
- **Recommended replacement**: 
  - Use `/pipeline/api/inputSets/template` (GET, official)
  - Or use `/v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/inputs-schema` (v1 clean API)
- **Note**: v2/variables may be internal; template endpoint is documented and preferred

---

## 🎯 Recommended API Versions

### For Pipeline Execution (Cleaner v1 API)

The spec also documents **v1 equivalents** that are cleaner and more consistent:

| Use Case | v1 Endpoint | gateway Endpoint | Notes |
|----------|-------------|------------------|-------|
| Execute pipeline | `POST /v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/execute` | `/gateway/pipeline/api/pipeline/execute/{id}` | v1 is cleaner, uses path params |
| Get inputs schema | `GET /v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/inputs-schema` | `/gateway/pipeline/api/pipelines/v2/variables` | v1 is official, recommended |
| Merge input sets | `POST /v1/orgs/{org}/projects/{project}/input-sets/merge` | `/gateway/pipeline/api/inputSets/merge` | Both work; v1 follows REST naming |
| Rerun execution | `POST /v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/execute/rerun/{id}` | (not available) | v1 only |
| Retry execution | `POST /v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/execute/retry/{id}` | (not available) | v1 only |

---

## 📖 How to Use the OpenAPI Spec

Download the spec and query it programmatically:

```bash
# Download
curl -sL "https://apidocs.harness.io/_bundle/index.json?download" -o harness-openapi.json

# List all pipeline endpoints
jq '.paths | to_entries[] | select(.key | contains("pipeline")) | .key' harness-openapi.json

# Get full docs for an endpoint
jq '.paths["/pipeline/api/pipeline/execute/{identifier}"].post' harness-openapi.json | jq '.parameters, .requestBody, .responses' -r

# Extract all query parameters for execution
jq '.paths["/pipeline/api/pipelines/execution/summary"].post.parameters[] | {name, required, in, description}' harness-openapi.json
```

---

## 📝 Implementation Notes

### Query Parameter Quirk
The **gateway/pipeline** endpoints use different param names than **v1**:
- `pipelineIdentifier` (gateway) vs `pipeline` (v1)
- `planExecutionId` (gateway) vs `execution-id` (v1)

### Body Format Quirk
Execution endpoints accept YAML in the body (not JSON):
```yaml
# Correct (gateway)
pipeline:
  identifier: my-pipeline
  variables:
    - name: var1
      value: val1
```

### POST vs GET
Counterintuitively, the execution listing endpoint is **POST**, not GET:
```bash
POST /pipeline/api/pipelines/execution/summary
Body: { "filterType": "PipelineExecution" }
```

---

## 🔗 Related Endpoints (Also Documented in Spec)

For completeness, the spec includes:

| Endpoint | Purpose |
|----------|---------|
| `/v1/entities/{scope}/{kind}/{identifier}` | Get/update/delete specific entity |
| `/v1/backstage-env-variables` | Manage Backstage environment variables |
| `/v1/catalog/custom-properties` | Ingest catalog custom properties |
| `/v1/scorecards`, `/v1/checks` | IDP quality gates |
| `/v1/plugins-info` | Plugin discovery and management |
| `/v1/layout` | Homepage layout configuration |
| `/ng/api/variables` | Account/org/project variables (not pipeline vars) |
| `/authz/api/permissions` | List available permissions |
| `/authz/api/acl` | Check access control (500 on many accounts — permissions issue) |

---

**Generated**: 2026-03-09  
**Spec Version**: OpenAPI 3.0.3 from apidocs.harness.io
