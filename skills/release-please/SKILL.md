---
name: release-please
description: Set up and operate Google release-please for automated changelog, version bumping, and GitHub Release creation driven by Conventional Commits. Use when adding release automation to a repo, diagnosing release-please failures, or understanding why a Release PR hasn't appeared. Triggers on "release-please", "automate releases", "release PR", "conventional commits versioning".
---

# release-please

Automates the release cycle: reads Conventional Commits → opens a Release PR
(bumps version + updates CHANGELOG) → merging the PR creates a GitHub Release
→ downstream publish workflow triggers.

## Required files

```
release-please-config.json          # package config
.release-please-manifest.json       # current version (release-please owns this)
.github/workflows/release-please.yml
```

### release-please-config.json

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "python",
  "packages": {
    ".": {
      "release-type": "python",
      "package-name": "mypackage",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "extra-files": [
        {
          "type": "toml",
          "path": "pyproject.toml",
          "jsonpath": "$.project.version"
        }
      ]
    }
  }
}
```

Supported `release-type` values: `python`, `node`, `rust`, `go`, `java`, `simple`.
For `node` the version lives in `package.json` automatically — no `extra-files` needed.

### .release-please-manifest.json

Seed with the current released version **before** the first run:

```json
{ ".": "1.2.3" }
```

release-please updates this file on every Release PR merge. Never edit manually.

### release-please.yml

```yaml
name: Release Please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
    steps:
      - uses: googleapis/release-please-action@v5
        id: release
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

**Use `@v5` not `@v4`.** v4 → v5 was a breaking rename of config options.

## How it works

```
Conventional Commit pushed to main
  → release-please opens/updates Release PR
    → human merges PR
      → GitHub Release + tag created  ← downstream publish triggers here
```

The Release PR contains:
- Updated `CHANGELOG.md` (grouped by feat/fix/chore)
- Bumped version in `pyproject.toml` (or `package.json` etc.)
- Updated `.release-please-manifest.json`

Semver bump rules from Conventional Commits:
| Commit type | Bump |
|-------------|------|
| `feat:` | minor |
| `fix:`, `perf:`, `refactor:` | patch |
| `feat!:` or `BREAKING CHANGE:` footer | major |
| `chore:`, `docs:`, `ci:` | no bump |

## Wiring a downstream publish workflow

The publish workflow must trigger on `release: [published]` — NOT on tag push.
release-please creates a GitHub Release, which fires `release: published`.

```yaml
on:
  release:
    types: [published]
```

**Critical:** GitHub Actions runs the workflow from the **tag ref**, not `HEAD`.
If you fix `publish.yml` after tagging, the fix won't apply until the next release.

## Common failures and fixes

### Release PR never appears

1. Check the workflow ran (push to `main` should trigger it)
2. Verify `permissions: contents: write, pull-requests: write` in workflow
3. Check commits use Conventional Commits format — `chore:`/`docs:`/`ci:` do NOT create a Release PR, only `feat:` and `fix:` do
4. Check `.release-please-manifest.json` has the correct current version — if it's ahead of any tag, release-please has nothing to release

### `startup_failure` on release-please workflow

Almost always an Actions permissions policy issue. See `github-actions-permissions` skill.

### `release-please failed: <!DOCTYPE html>`

GitHub API rate limit or transient timeout during commit backfill (release-please scans up to 500 commits looking for the last release tag). Transient — re-run or wait. The Release PR is usually already created before the timeout.

### Release PR bumps to wrong version (e.g. 0.6.1 instead of 0.6.0)

The manifest was seeded at `0.6.0` but no `v0.6.0` tag exists on the repo.
release-please sees `0.6.0` as "unreleased" and bumps past it.

Fix: create the tag manually before the first release-please run:
```bash
git tag v0.6.0 <sha>
git push origin v0.6.0
```
Or accept the bump — the version number is cosmetic.

### Publish workflow didn't fire after Release PR merged

The `release: published` event is only fired by GitHub when the Release is
published. release-please creates the Release automatically but occasionally
the event doesn't propagate to workflows (especially bot-created releases).

Workaround — toggle draft to re-fire the event:
```bash
RELEASE_ID=$(gh api repos/OWNER/REPO/releases/latest --jq '.id')
gh api repos/OWNER/REPO/releases/$RELEASE_ID --method PATCH --field draft=true
gh api repos/OWNER/REPO/releases/$RELEASE_ID --method PATCH --field draft=false
```

## Squash vs merge for Release PRs

Use `--merge` (not `--squash`) when merging the Release PR:
```bash
gh pr merge 22 --repo OWNER/REPO --merge
```

Squash changes the commit SHA that release-please uses to track the release
boundary, which can confuse the next Release PR.

## Version file locations by ecosystem

| Ecosystem | File | jsonpath / field |
|-----------|------|-----------------|
| Python | `pyproject.toml` | `$.project.version` |
| Node.js | `package.json` | automatic |
| Rust | `Cargo.toml` | `$.package.version` |
| Generic | any file | use `extra-files` with `type: generic` and regex |
