# Agent Self-Discovery System for Harness APIs

## Overview

The `harness-idp` skill now includes a **self-discovery system** that enables agents to automatically find documentation for ANY Harness API endpoint, even those not explicitly documented in the skill.

**Result**: Scale from 20 documented endpoints → **1685 endpoints** (entire official API surface) with zero additional effort.

---

## Architecture

### Two-Tier System

```
┌─────────────────────────────────────────────────────────┐
│                    Agent/User Query                      │
│          "How do I list webhook executions?"            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              openapi_fallback.py (Python API)            │
│  - resolve_endpoint(path, method)                        │
│  - search_endpoints_by_keyword(query)                    │
│  - suggest_related(keyword)                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│        OpenAPIResolver (In-Memory JSON Search)           │
│  - Fast regex/keyword matching (< 1s)                    │
│  - Handles path param normalization                      │
│  - Graceful caching & fallback                           │
└────────────────┬────────────────────────────────────────┘
                 │
     ┌───────────┴────────────┬─────────────────┐
     │                        │                 │
     ▼                        ▼                 ▼
 Cached                 Cache Miss         Offline Mode
 (7-day TTL)           (Auto-download)    (Stale Cache)
     │                        │                 │
     └────────────┬───────────┴────────────────┘
                  │
                  ▼
        ┌──────────────────────────────┐
        │   openapi-cache/            │
        │   harness-openapi.json      │
        │   (14MB, 1685 endpoints)    │
        │   manifest.json             │
        └──────────────────────────────┘
                  │
                  ▼
   Result: Full endpoint documentation
   (parameters, schemas, response types)
```

---

## Quick Start

### CLI Tool (for exploration)

```bash
cd skills/harness-idp

# Search for endpoints
python3 openapi-discovery.py --search "webhook"

# Get detailed docs
python3 openapi-discovery.py --endpoint "/code/api/v1/webhooks" --method GET

# List all modules
python3 openapi-discovery.py --list-modules

# Find related
python3 openapi-discovery.py --find-related "execution"
```

### Python API (for integration)

```python
from skills.harness_idp.scripts.openapi_fallback import OpenAPIResolver

resolver = OpenAPIResolver()

# Search
matches = resolver.search("pipeline trigger")
for path, method, summary in matches:
    print(f"[{method}] {path} → {summary}")

# Get docs
docs = resolver.resolve_endpoint("/pipeline/api/pipelines/execute", "POST")
print(docs)

# Get suggestions
suggestions = resolver.suggest("webhook")
print(suggestions)
```

---

## Features

### ✅ Automatic Spec Download
- Source: `https://apidocs.harness.io/_bundle/index.json?download`
- Size: 14MB JSON, 1685 endpoints
- No authentication required
- Cached locally in `openapi-cache/harness-openapi.json`

### ✅ Smart Caching
- 7-day TTL (balances freshness vs. network calls)
- Manifest file tracks version and endpoint count
- Auto-refresh on `--refresh` flag
- Graceful fallback to stale cache if offline

### ✅ Fast Search
- In-memory parsing (< 1 second)
- Regex path matching (handles `{param}` normalization)
- Keyword matching on summary + description
- Returns all matches ranked by relevance

### ✅ Robust Error Handling
- Download fails → use stale cache
- Cache corrupted → auto-retry download
- Offline → return whatever is cached
- No exceptions thrown

### ✅ Zero Setup
- First usage triggers auto-download
- No credentials needed
- Works offline after first download
- No config files to edit

---

## Coverage

### Spec Statistics
- **Total endpoints**: 1685 (OpenAPI 3.0.3)
- **API modules**: 20 (see below)
- **Methods**: GET, POST, PUT, DELETE, PATCH

### API Modules

| Module | Endpoints | Purpose |
|--------|----------:|---------|
| `v1` | 693 | IDP: catalog, scorecards, plugins, layouts, templates |
| `ng` | 343 | Platform: orgs, projects, connectors, RBAC |
| `ccm` | 207 | Cloud Cost Management |
| `iacm` | 168 | IaC Management |
| `gitops` | 145 | GitOps: applications, clusters, agents |
| `code` | 138 | Code Repository: repos, PRs, webhooks |
| `gateway` | 90 | Autostopping, load balancing |
| `har` | 86 | Artifact Registry |
| `pipeline` | 85 | **Pipeline execution, triggers, input sets** |
| `sto` | 78 | Security Testing Orchestration |
| `cv` | 77 | Continuous Verification |
| `cf` | 45 | Feature Flags |
| `authz` | 28 | ACL, permissions |
| `template` | 18 | Pipeline/stage templates |
| `dashboard` | 18 | Custom dashboards |
| `pm` | 24 | Policy Management |
| `audit` | 8 | Audit trail |
| ... | ... | ... |

---

## Use Cases

### 1. Agent Auto-Discovery

**Agent asks**: "How do I list webhook executions?"

```python
def help_agent(question: str):
    resolver = OpenAPIResolver()
    matches = resolver.search(question)
    
    if matches:
        path, method, summary = matches[0]
        docs = resolver.resolve_endpoint(path, method)
        return f"Found endpoint:\n{docs}"
    else:
        suggestions = resolver.suggest(question.split()[0])
        return f"Try these:\n{suggestions}"
```

**Result**: Agent gets full parameter list, schemas, response types.

### 2. Skill Development

**Problem**: Need to implement new feature but endpoint not documented.

**Solution**:
```bash
$ python3 openapi-discovery.py --search "custom property"
Found 6 endpoints:
  [POST  ] /v1/catalog/custom-properties
           → Ingest catalog custom properties

$ python3 openapi-discovery.py --endpoint "/v1/catalog/custom-properties" --method POST
# (outputs full docs with parameters and schema)
```

### 3. Interactive API Explorer

**Use case**: "Show me all available trigger endpoints"

```bash
$ python3 openapi-discovery.py --find-related "trigger"
```

### 4. Documentation Generation

```python
resolver = OpenAPIResolver()
for module in resolver.spec.get("modules", []):
    endpoints = resolver.search(module)
    # Generate markdown docs for module
```

---

## Integration Points

### In Skills
```python
# Any skill can use the discovery system
from skills.harness_idp.scripts.openapi_fallback import OpenAPIResolver

resolver = OpenAPIResolver()
docs = resolver.resolve_endpoint(user_request_endpoint, method)
```

### In Agents
```python
# Agent tools can call discovery
def tool_api_lookup(endpoint: str):
    docs = resolve_endpoint(endpoint)
    return docs or "Endpoint not found. Try searching."
```

### In Documentation
```bash
# Generate updated docs automatically
python3 openapi-discovery.py --list-modules > API-MODULES.txt
python3 openapi-discovery.py --search "pipeline" > PIPELINE-APIS.txt
```

---

## Cache Details

### Manifest File
```json
{
  "downloaded_at": "2026-03-09T21:00:00",
  "spec_version": "1.0",
  "total_endpoints": 1685,
  "modules": ["v1", "ng", "ccm", "pipeline", ...]
}
```

### Cache Location
```
skills/harness-idp/openapi-cache/
├── harness-openapi.json    (14MB, 1685 endpoints)
└── manifest.json            (metadata)
```

### Cache Management
```bash
# Check status
cat skills/harness-idp/openapi-cache/manifest.json

# Clear cache (forces re-download on next use)
rm -rf skills/harness-idp/openapi-cache/

# Force refresh
python3 openapi-discovery.py --refresh
```

---

## Comparison: Before vs. After

### Before (Hardcoded Documentation)
- 20 documented endpoints
- New endpoint needed = update skill docs manually
- Max coverage: what we knew about
- Scaling: O(n) manual effort per endpoint

### After (Self-Discovery)
- **1685 discoverable endpoints** (entire API surface)
- New endpoint needed = user asks agent, agent searches spec
- Full coverage: all official Harness APIs
- Scaling: O(1) effort (tool already built)

---

## Limitations & Workarounds

| Limitation | Workaround |
|-----------|-----------|
| Spec download requires internet | Use `--refresh` to cache spec, then work offline |
| 5 undocumented but working APIs | See `OPENAPI-XREF.md` for list + recommended replacements |
| Param types may be generic | Check operation summary; look at skill examples |
| Complex nested schemas | Get endpoint docs, inspect example in skill code |
| Spec may lag 1-2 weeks behind production | Use HAR file discovery for bleeding-edge features |

---

## File Structure

```
skills/harness-idp/
├── openapi-discovery.py         (CLI tool)
├── OPENAPI-FALLBACK.md          (User guide)
├── OPENAPI-XREF.md              (Cross-ref: 15 matched + 5 unmatched)
├── scripts/
│   └── openapi_fallback.py      (Python API)
├── openapi-cache/               (auto-generated)
│   ├── harness-openapi.json    (14MB spec)
│   └── manifest.json            (metadata)
└── ...
```

---

## See Also

- **OPENAPI-FALLBACK.md** — Complete usage guide (CLI + Python API)
- **OPENAPI-XREF.md** — Cross-reference of all 20 skill endpoints with official spec
- **SKILL.md** — Main skill documentation (references discovery system)
- **https://apidocs.harness.io** — Live OpenAPI browser (read-only)

---

## Summary

The self-discovery system turns the `harness-idp` skill into a **universal Harness API client** that can:
1. **Search** 1685 endpoints by keyword
2. **Resolve** full documentation for any endpoint
3. **Suggest** related endpoints
4. **Cache** locally for offline use
5. **Fail gracefully** with stale fallbacks

**Result**: Agents can help users with ANY Harness API without manual documentation updates.

---

**Created**: 2026-03-09  
**Spec Version**: OpenAPI 3.0.3 (1685 endpoints)  
**Cache TTL**: 7 days  
**Auto-download**: Yes (first use or on --refresh)
