---
name: python-publish
description: Set up and validate a modern Python publish pipeline — hatchling build backend, uv, twine token validation, PyPI/TestPyPI publishing via GitHub Actions. Use when packaging a Python project for PyPI, wiring a CI publish workflow, or diagnosing publish failures. Triggers on "publish to PyPI", "python package release", "twine upload", "pypi token", "gh-action-pypi-publish".
---

# Python Publish

Modern Python publish pipeline: hatchling + uv + twine + PYPI_TOKEN.

## pyproject.toml setup

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mypackage"
version = "1.2.3"          # managed by release-please or manually
requires-python = ">=3.12"
dependencies = [...]

[project.scripts]
mypackage = "mypackage.cli:main"

[project.optional-dependencies]
build = ["twine", "build"]

[tool.hatch.build.targets.wheel]
packages = ["mypackage"]   # only needed if layout is non-standard
```

No `setup.py`, no `setup.cfg`, no `MANIFEST.in` needed.

## Build locally

```bash
uv sync --extra build
uv build                    # produces dist/*.whl + dist/*.tar.gz
uv run twine check dist/*   # validate metadata before upload
```

## Validate the PyPI token before CI

Always validate the token locally before storing it as a secret:

```bash
TOKEN=$(cat /tmp/pypi.token)

# 1. Build
uv build

# 2. Check distributions
uv run twine check dist/mypackage-*.whl dist/mypackage-*.tar.gz

# 3. Dry-run upload (validates token auth against PyPI)
uv run twine upload \
  --repository-url https://upload.pypi.org/legacy/ \
  --username __token__ \
  --password "$TOKEN" \
  --skip-existing \
  dist/mypackage-*

# If this succeeds, the token is valid and the package is live.
# If 403: token is wrong, expired, or scoped to wrong package.
```

## Store token as GitHub secret

```bash
gh secret set PYPI_TOKEN --repo OWNER/REPO < /tmp/pypi.token
gh secret list --repo OWNER/REPO   # verify timestamp updated
```

## publish.yml — GitHub Actions workflow

```yaml
name: Publish

on:
  release:
    types: [published]     # triggered by release-please creating a GitHub Release

jobs:
  build:
    name: Build distribution
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: astral-sh/setup-uv@v7
        with:
          version: "latest"

      - run: uv python install 3.12

      - run: uv sync --extra test

      - run: make test          # or: uv run pytest

      - run: uv build

      - run: |
          uv sync --extra build
          uv run twine check dist/*

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          if-no-files-found: error

  publish-pypi:
    name: Publish to PyPI
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/mypackage
    steps:
      - uses: actions/download-artifact@v8
        with:
          name: dist
          path: dist/

      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_TOKEN }}
          print-hash: true
```

**Do NOT add a Test PyPI stage unless you have a separate `TEST_PYPI_TOKEN`.**
The production PYPI_TOKEN is rejected by test.pypi.org with 403.

## PyPI token scopes

| Token type | Works with | Created at |
|------------|-----------|------------|
| Account-scoped | All packages for the account | pypi.org Account Settings |
| Project-scoped | One specific package only | pypi.org package management |
| Test PyPI token | test.pypi.org only | test.pypi.org (separate account) |

Use project-scoped tokens in CI — least privilege.

## GitHub environments

Create `pypi` (and optionally `test-pypi`) environments before first publish:

```bash
gh api repos/OWNER/REPO/environments/pypi --method PUT --input - <<'EOF'
{}
EOF
```

Without the environment, the job will fail or skip silently.
Add protection rules (required reviewers) for production gating if needed.

## Workflow runs from the tag ref, not HEAD

When a GitHub Release is created from tag `v1.2.3`, the publish workflow
runs the **`publish.yml` at that tag**, not the current `main`.

Consequence: if you fix `publish.yml` after tagging, the fix doesn't apply
until the next release tag. The workflow file at the tag is always used.

## Triggering publish after release-please

release-please creates the GitHub Release automatically after the Release PR
merges. The `release: published` event fires and triggers publish.yml.

If publish.yml doesn't trigger (known GitHub quirk with bot-created releases):

```bash
RELEASE_ID=$(gh api repos/OWNER/REPO/releases/latest --jq '.id')
gh api repos/OWNER/REPO/releases/$RELEASE_ID --method PATCH --field draft=true --jq '.draft'
gh api repos/OWNER/REPO/releases/$RELEASE_ID --method PATCH --field draft=false --jq '{tag_name,published_at}'
```

This re-publishes the release and re-fires the event.

## Verify publish succeeded

```bash
# PyPI index has a ~30s propagation delay
sleep 30
curl -s https://pypi.org/pypi/mypackage/json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['info']['version'])"

# Or install and check
uvx mypackage --version
pip install mypackage==1.2.3 --dry-run
```

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `403 Invalid or non-existent authentication information` | Wrong token or token scoped to different package | Validate token with twine locally first |
| `400 File already exists` | Version already on PyPI (immutable) | Bump version — PyPI doesn't allow re-upload |
| `startup_failure` in workflow | Actions permissions policy blocking `pypa/*` | See `github-actions-permissions` skill |
| Workflow didn't trigger | `release: published` event didn't fire | Toggle draft on the release to re-fire |
| Wrong `publish.yml` ran | Workflow runs from tag ref, not HEAD | Fix is in next release |
