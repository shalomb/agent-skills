# OpenAPI Fallback Discovery System

**Purpose**: When you encounter a Harness API that isn't explicitly documented in the skill, use this self-discovery system to automatically find documentation from the official OpenAPI spec.

**No additional setup required** — the system auto-downloads the spec on first use and caches it locally (7-day TTL).

---

## Command-Line Usage

### 1. Search for endpoints by keyword

```bash
python3 openapi-discovery.py --search "pipeline execution"
python3 openapi-discovery.py --search "webhook"
python3 openapi-discovery.py --search "connector"
```

**Output**:
```
Found 47 endpoints matching 'pipeline execution':

  [POST  ] /pipeline/api/pipelines/execution/summary
           → List Executions
  [GET   ] /pipeline/api/pipelines/execution/v2/{planExecutionId}
           → Fetch Execution Details
  ...
```

### 2. Get detailed docs for a specific endpoint

```bash
python3 openapi-discovery.py --endpoint "/pipeline/api/pipeline/execute/{identifier}"
python3 openapi-discovery.py --endpoint "/pipeline/api/pipeline/execute/{identifier}" --method POST
```

**Output**:
```
================================================================================
  POST   /pipeline/api/pipeline/execute/{identifier}
================================================================================

Summary: Execute a Pipeline with Runtime Input YAML

▸ PARAMETERS:
  * accountIdentifier             (query  string  ) Account Identifier for the Entity.
  * orgIdentifier                 (query  string  ) Organization Identifier for the Entity.
  * projectIdentifier             (query  string  ) Project Identifier for the Entity.
    branch                        (query  string  ) Name of the branch.
    notifyOnlyUser                (query  boolean ) Whether to notify only the user who triggered

▸ REQUEST BODY [optional]:
  Content-Type: application/yaml
    Schema: PipelineYAML

▸ RESPONSES:
  200: Pipeline execution initiated successfully [PlanExecutionResponse]
  400: Bad Request [Failure]
  500: Internal Server Error [PipelineError]
```

### 3. List all available API modules

```bash
python3 openapi-discovery.py --list-modules
```

**Output**:
```
Harness API Modules:

  v1                693 endpoints
  ng                343 endpoints
  ccm               207 endpoints
  iacm              168 endpoints
  gitops            145 endpoints
  code              138 endpoints
  gateway            90 endpoints
  har                86 endpoints
  pipeline           85 endpoints
  ...
```

### 4. Find related endpoints

```bash
python3 openapi-discovery.py --find-related "webhook"
python3 openapi-discovery.py --find-related "trigger"
```

### 5. Force spec refresh

```bash
python3 openapi-discovery.py --refresh
```

Clears the cache and re-downloads the spec (useful if it's older than 7 days or corrupted).

---

## Python Usage (In Code)

### Quick endpoint resolution

```python
from scripts.openapi_fallback import resolve_endpoint

# Get docs for an endpoint
docs = resolve_endpoint("/pipeline/api/pipelines/execute", method="POST")
if docs:
    print(docs)
```

### More control with OpenAPIResolver

```python
from scripts.openapi_fallback import OpenAPIResolver

resolver = OpenAPIResolver(refresh=False)

# Check if spec is available
if resolver.available:
    # Search endpoints
    matches = resolver.search("pipeline execution")
    for path, method, summary in matches:
        print(f"[{method}] {path} → {summary}")
    
    # Get endpoint docs
    docs = resolver.resolve_endpoint("/pipeline/api/pipeline/execute/{identifier}", "POST")
    print(docs)
    
    # Get suggestions
    suggestions = resolver.suggest("webhook")
    print(suggestions)
```

### Integrate with CLI tools

```python
import sys
from scripts.openapi_fallback import OpenAPIResolver

def help_user_find_endpoint(query: str):
    """Help user discover an endpoint they're looking for"""
    resolver = OpenAPIResolver()
    
    if not resolver.available:
        print("OpenAPI spec not available. Try: python3 openapi-discovery.py --refresh")
        return False
    
    # Search for endpoint
    matches = resolver.search(query)
    if not matches:
        print(f"No endpoints found for '{query}'")
        return False
    
    print(f"\nFound {len(matches)} matches:\n")
    for path, method, summary in matches:
        print(f"  [{method:<6}] {path}")
        if summary:
            print(f"           → {summary}\n")
    
    return True

# Usage
if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "pipeline"
    help_user_find_endpoint(query)
```

---

## How It Works

### 1. **Spec Download**
   - Source: `https://apidocs.harness.io/_bundle/index.json?download` (14MB, 1685 endpoints)
   - Cached locally in `openapi-cache/harness-openapi.json` (no auth required)
   - Auto-refreshes every 7 days or on manual `--refresh`

### 2. **Smart Caching**
   - Manifest file tracks download time and spec version
   - Avoids repeated downloads during development
   - 7-day TTL balances freshness vs. network calls

### 3. **Robust Fallback**
   - If download fails and cache exists, uses stale cache
   - If cache corrupted, attempts re-download
   - Gracefully degrades if spec unavailable

### 4. **Fast Search**
   - In-memory JSON parsing (< 1 second)
   - Regex path matching (handles path params)
   - Keyword matching on summary + description

---

## Example: Using Discovery in Skill Development

### Scenario: New API endpoint needed but not documented in skill

**Problem**: Need to trigger a pipeline with custom options, but the exact endpoint params unknown.

**Solution**:
```bash
# 1. Search
$ python3 openapi-discovery.py --search "execute pipeline"
Found 6 endpoints:
  [POST  ] /pipeline/api/pipeline/execute/{identifier}
           → Execute a Pipeline with Runtime Input YAML
  [POST  ] /v1/orgs/{org}/projects/{project}/pipelines/{pipeline}/execute
           → Execute Pipeline

# 2. Get details
$ python3 openapi-discovery.py --endpoint "/pipeline/api/pipeline/execute/{identifier}"
# (outputs full parameter list, request/response schema)

# 3. Use in code
from scripts.openapi_fallback import resolve_endpoint
docs = resolve_endpoint("/pipeline/api/pipeline/execute/{identifier}", "POST")
# (guides implementation with official schema)
```

---

## Cache Management

### Check cache status

```bash
ls -lh openapi-cache/
cat openapi-cache/manifest.json
```

**Example manifest**:
```json
{
  "downloaded_at": "2026-03-09T21:00:00",
  "spec_version": "1.0",
  "total_endpoints": 1685,
  "modules": ["v1", "ng", "ccm", "pipeline", ...]
}
```

### Clear cache

```bash
rm -rf openapi-cache/
# Next command will re-download
```

---

## Limitations & Known Issues

| Issue | Workaround |
|-------|-----------|
| Spec download requires internet | Use `--refresh` to cache spec for offline use |
| Internal/undocumented APIs not in spec | See OPENAPI-XREF.md for 5 discovered-but-undocumented endpoints |
| Param types may be generic (e.g., `string`) | Check operation summary for usage hints |
| Complex nested schemas hard to parse | Get endpoint docs, then inspect example in skill code |
| Spec may lag behind production | Use HAR file discovery for latest real-world examples |

---

## Integration with Agent Workflows

### Example: Agent auto-discovers API

```python
# In a skill handler or agent tool
def discover_harness_api(user_query: str) -> str:
    """Agent asks: 'How do I list webhook executions?'"""
    
    from scripts.openapi_fallback import OpenAPIResolver
    
    resolver = OpenAPIResolver()
    
    # Search for relevant endpoints
    matches = resolver.search(user_query)
    
    if matches:
        # Return first match with full docs
        path, method, summary = matches[0]
        docs = resolver.resolve_endpoint(path, method)
        return f"Found endpoint:\n{docs}"
    else:
        # Suggest related
        suggestions = resolver.suggest(user_query.split()[0])
        return f"No exact match. Related endpoints:\n{suggestions}"
```

---

## See Also

- **OPENAPI-XREF.md** — Cross-reference of skill endpoints with official spec
- **SKILL.md** — Main skill documentation
- **TESTING.md** — Integration test examples
- **https://apidocs.harness.io** — Live OpenAPI browser (read-only)

---

**Last Updated**: 2026-03-09  
**Spec Version**: OpenAPI 3.0.3 (1685 endpoints)  
**Caching**: 7-day TTL, auto-refresh on --refresh flag
