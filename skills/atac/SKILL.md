---
name: atac
description: Use when developing, maintaining, or running API test plans with ATAC (Arguably a Terminal API Client). Covers creating collections, writing post-request assertion scripts, running tests headlessly, managing environments, and storing test plans in a git repo. Triggers on "atac", "API test plan", "test endpoints", "run collection", "assert status code", or any programmatic HTTP endpoint testing workflow.
---

# ATAC — API Test Plans

ATAC is a terminal API client (like Postman/Bruno) that stores collections as
**committed JSON/YAML files** and runs fully headlessly — ideal for CI and
agent-driven test plans.

Binary: `~/.cargo/bin/atac`  
Docs: https://atac.julien-cpsn.com/

## Key Concepts

| Concept | What it is |
|---------|-----------|
| **Directory** | A folder containing `*.json`/`*.yaml` collections, `.env.*` files, and `atac.toml` |
| **Collection** | A JSON or YAML file of named requests (one file = one collection) |
| **Request** | URL + method + headers + body + auth + pre/post scripts |
| **Environment** | `.env.<name>` file of `KEY=VALUE` pairs; variables used as `{{KEY}}` |
| **Script** | JavaScript (Boa engine) run pre- or post-request; reads/writes `request`, `response`, `env` objects |

## Directory Structure for a Test Plan Repo

```
api-tests/
├── atac.toml               # optional config
├── .env.staging            # KEY=VALUE env vars
├── .env.production
├── health.json             # collection: health checks
├── auth.json               # collection: auth flows
└── users.yaml              # collection: user CRUD
```

Always point atac at the directory: `atac -d ./api-tests <command>`

## Quick Reference

```bash
# Run a single request
atac -d ./api-tests request send auth/login --status-code --console

# Run an entire collection
atac -d ./api-tests collection send auth --status-code --console --env staging

# One-shot (no collection needed)
atac try -u https://api.example.com/health --status-code

# Create a new collection + request programmatically
atac -d ./api-tests collection new my-collection
atac -d ./api-tests request new my-collection/my-request \
  -u "{{BASE_URL}}/endpoint" -m POST \
  --body-json '{"key":"value"}' \
  --post-request-script 'if (response.status_code !== "200 OK") { throw "Expected 200, got " + response.status_code; }'

# Add/update a post-request assertion script
atac -d ./api-tests request scripts my-collection/my-request set post \
  'if (response.status_code !== "200 OK") { throw "FAIL: " + response.status_code; }'

# Use an environment
atac -d ./api-tests collection send health --env staging --status-code --console
```

## Post-Request Assertion Scripts (JavaScript)

Scripts run in a Boa JS engine. Two global objects are available:

**`response` object fields:**
```js
response.status_code  // e.g. "200 OK", "404 Not Found"
response.content      // body string (if Body variant)
response.headers      // array of [key, value] pairs
response.cookies      // cookie string
// Note: response.duration is available in TUI but NOT in post-request scripts
```

**`env` object:** key/value map of the active environment — read and write to
pass values between requests:
```js
env.TOKEN = JSON.parse(response.content).token;
```

**`console.log(msg)`** — output shown with `--console` flag

**`pretty_print(obj)`** — pretty-prints any object via `console.log`

### Assertion Pattern

```js
// Assert status
if (response.status_code !== "200 OK") {
  throw "FAIL: expected 200, got " + response.status_code;
}

// Assert body field
var body = JSON.parse(response.content);
if (!body.id) {
  throw "FAIL: missing 'id' in response body";
}

// Chain: store token for next request
env.AUTH_TOKEN = body.token;

console.log("PASS: login ok, token stored");
```

> **Exit behaviour:** ATAC does NOT fail with a non-zero exit code when a
> script throws. Use `--console` and parse output in CI, or check
> `--status-code` output. See [references/ci-testing.md](references/ci-testing.md)
> for shell-level assertion wrappers.

## Environment Files

`.env.<name>` files are plain `KEY=VALUE` (no quotes needed):

```
BASE_URL=https://api.staging.example.com
AUTH_TOKEN=
TIMEOUT=5000
```

Reference in requests as `{{BASE_URL}}`, `{{AUTH_TOKEN}}`.

Built-in variables (no env file needed): `{{NOW}}`, `{{TIMESTAMP}}`,
`{{UUIDv4}}`, `{{UUIDv7}}`, and any OS environment variable.

## Collection File Format

Collections are plain JSON or YAML — commit them to git.

```json
{
  "name": "health",
  "requests": [
    {
      "name": "GET /health",
      "url": "{{BASE_URL}}/health",
      "method": "GET",
      "auth": "no_auth",
      "scripts": {
        "pre_request_script": null,
        "post_request_script": "if (response.status_code !== \"200 OK\") throw \"FAIL\";"
      },
      "settings": {
        "use_config_proxy": true,
        "allow_redirects": true,
        "timeout": 30000,
        "store_received_cookies": true,
        "pretty_print_response_content": true,
        "accept_invalid_certs": false,
        "accept_invalid_hostnames": false
      },
      "protocol": { "type": "http", "method": "GET", "body": "no_body" }
    }
  ]
}
```

See [references/collection-format.md](references/collection-format.md) for
full JSON/YAML schema with all auth types and body variants.

## Importing Existing Collections

```bash
# From Postman v2.1 export
atac -d ./api-tests import postman ./my-collection.postman_collection.json

# From OpenAPI spec
atac -d ./api-tests import open-api ./openapi.yaml

# From a cURL command
atac -d ./api-tests import curl ./request.curl
```

## Workflow: Build a Test Plan in a Repo

1. **Create the directory** — one folder per project, committed to git
2. **Add environments** — `.env.staging`, `.env.production` with `BASE_URL`, secrets
3. **Create collections** — one per domain (auth, users, health)
4. **Add requests** — via CLI (`atac request new`) or edit JSON/YAML directly
5. **Write assertions** — post-request scripts that `throw` on failure
6. **Run headlessly** — `atac -d . collection send <name> --console --status-code --env staging`
7. **Commit** — collections and env files (exclude secrets via `.gitignore`)

## CI Integration

See [references/ci-testing.md](references/ci-testing.md) for:
- Shell wrapper to detect assertion failures from `--console` output
- GitHub Actions example
- `--no-ansi-log` flag for clean CI output
- Exit-code workaround (ATAC exits 0 even on script throws)
