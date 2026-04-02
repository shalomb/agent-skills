# ATAC CI Testing Guide

ATAC exits with code `0` even when a post-request script throws. This guide
shows how to reliably detect test failures in CI pipelines.

## The Problem

```bash
atac -d . collection send myapi --console
echo $?   # Always 0, even if scripts threw
```

ATAC writes response body and script console output to stdout. Failed
assertions show up in `--console` output but don't affect the exit code.

## Shell Wrapper Pattern

Capture console output and grep for failure markers:

```bash
#!/usr/bin/env bash
# run-tests.sh

set -euo pipefail

ATAC_DIR="${1:-.}"
COLLECTION="${2:-}"
ENV="${3:-}"
ATAC_BIN="${ATAC_BIN:-atac}"

ENV_FLAG=""
[[ -n "$ENV" ]] && ENV_FLAG="--env $ENV"

OUTPUT=$("$ATAC_BIN" -d "$ATAC_DIR" collection send "$COLLECTION" \
  --console \
  --status-code \
  --request-name \
  --no-ansi-log \
  $ENV_FLAG 2>&1)

echo "$OUTPUT"

# Detect throws from post-request scripts (starts with "FAIL" by convention)
if echo "$OUTPUT" | grep -qE '^FAIL:'; then
  echo ""
  echo "❌ Test failures detected"
  exit 1
fi

echo ""
echo "✅ All tests passed"
exit 0
```

Usage:
```bash
chmod +x run-tests.sh
./run-tests.sh ./api-tests auth staging
```

## Assertion Convention

In your post-request scripts, prefix failure messages with `FAIL:` so the
wrapper can detect them:

```js
// Good — detectable by grep
if (response.status_code !== "200 OK") {
  throw "FAIL: expected 200, got " + response.status_code;
}
console.log("PASS: health check ok");
```

## GitHub Actions Example

```yaml
# .github/workflows/api-tests.yml
name: API Tests

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 */6 * * *'   # every 6 hours

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install ATAC
        run: cargo install atac --locked

      - name: Run staging tests
        env:
          BASE_URL: ${{ secrets.STAGING_BASE_URL }}
          AUTH_TOKEN: ${{ secrets.STAGING_AUTH_TOKEN }}
        run: |
          # Write env file from secrets
          echo "BASE_URL=${BASE_URL}" > api-tests/.env.staging
          echo "AUTH_TOKEN=${AUTH_TOKEN}" >> api-tests/.env.staging
          ./run-tests.sh ./api-tests health staging
          ./run-tests.sh ./api-tests auth staging
          ./run-tests.sh ./api-tests users staging
```

## Running Multiple Collections

```bash
#!/usr/bin/env bash
# run-all-tests.sh

ATAC_DIR="${1:-.}"
ENV="${2:-staging}"
FAILED=0

for collection_file in "$ATAC_DIR"/*.json "$ATAC_DIR"/*.yaml; do
  [[ -f "$collection_file" ]] || continue
  name=$(basename "${collection_file%.*}")
  [[ "$name" == "atac" ]] && continue   # skip config

  echo "▶ Running collection: $name"
  if ! ./run-tests.sh "$ATAC_DIR" "$name" "$ENV"; then
    FAILED=$((FAILED + 1))
  fi
done

[[ $FAILED -eq 0 ]] && echo "✅ All collections passed" && exit 0
echo "❌ $FAILED collection(s) failed" && exit 1
```

## Per-Request Output Parsing

Use `--request-name` to get request names alongside results:

```bash
atac -d ./api-tests collection send users \
  --request-name \
  --status-code \
  --console \
  --no-ansi-log \
  --env staging
```

Output format:
```
GET /users
200 OK
PASS: got 3 users

POST /users
201 Created
PASS: user created, id=42
```

## Useful Flags Reference

| Flag | Effect |
|------|--------|
| `--status-code` | Print HTTP status code line per request |
| `--console` | Print pre/post script `console.log` output |
| `--request-name` | Print request name before its output |
| `--no-ansi-log` | Strip ANSI colour codes (essential for CI) |
| `--hide-content` | Suppress response body (cleaner CI output) |
| `--headers` | Print response headers |
| `--duration` | Print request duration |
| `--env <name>` | Use `.env.<name>` file |
| `--dry-run` | Don't write changes back to collection files |
