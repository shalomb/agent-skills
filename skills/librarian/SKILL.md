---
name: librarian
description: >
  Find, cache, and refresh git repositories — both local projects and remote
  repos. Uses the gum CLI to discover existing checkouts under ~/*/  before
  cloning. Use when the user references a git repository (URL, org/repo, or
  local path) or when you need to locate a project on disk.
---

# Librarian — Repository Finder & Cache

Find local git repositories or cache remote ones for reference. Prefers
discovering existing checkouts over cloning — your machine likely already
has what you need.

## Quick Reference

| Task | Command |
|------|---------|
| Find a local repo | `gum projects --format json \| jq '.[] \| select(.path \| test("PATTERN"))'` |
| List all local repos | `gum projects --format simple` |
| Search by remote URL | `gum projects --format json \| jq '.[] \| select(.remote \| test("org/repo"))'` |
| Clone with smart placement | `gum clone org/repo` |
| Suggest clone location | `gum clone --suggest org/repo` |
| Cache a remote repo | `scripts/checkout.sh <repo> --path-only` |
| Force-refresh a cached repo | `scripts/checkout.sh <repo> --force-update --path-only` |

## Strategy: Local First

Before cloning anything, **always check if the repo already exists locally**:

```bash
# Step 1: Search local projects (fast — uses gum's indexed DB)
gum projects --format json | jq -r '.[] | select(.remote | test("SEARCH_TERM")) | .path'

# Step 2: If not found locally, check the cache
scripts/checkout.sh org/repo --path-only

# Step 3: Only clone if truly missing (gum picks the right directory)
gum clone org/repo
```

## Finding Local Repos

The `gum` CLI maintains an indexed database of all git repos under `~/`:

```bash
# All repos as JSON (path, remote, branch)
gum projects --format json

# Simple list of paths
gum projects --format simple

# Force re-scan
gum projects --refresh --format simple

# Search examples
gum projects --format json | jq -r '.[] | select(.path | test("terraform")) | .path'
gum projects --format json | jq -r '.[] | select(.remote | test("shalomb")) | "\(.path)\t\(.remote)"'
```

## Caching Remote Repos

For repos not already on disk, use `scripts/checkout.sh` to cache under
`~/.cache/checkouts/<host>/<org>/<repo>`:

```bash
# These all resolve to the same checkout:
scripts/checkout.sh mitsuhiko/minijinja --path-only
scripts/checkout.sh github.com/mitsuhiko/minijinja --path-only
scripts/checkout.sh https://github.com/mitsuhiko/minijinja --path-only
scripts/checkout.sh git@github.com:mitsuhiko/minijinja.git --path-only
```

Features:
- Partial clone (`--filter=blob:none`) for efficiency
- Throttled refresh (every 5 minutes by default)
- Fast-forward merge when checkout is clean
- Force refresh with `--force-update`

## Cloning New Repos

When a repo needs to be cloned (not just cached), use `gum clone` which
analyses your existing project structure and suggests the right directory:

```bash
# Clone with intelligent directory suggestion
gum clone hashicorp/terraform

# Just see where it would go
gum clone --suggest hashicorp/terraform

# Force a specific location
gum clone --target ~/projects/hashicorp/terraform hashicorp/terraform
```

## Rules

1. **Search locally first.** Don't clone what's already on disk.
2. **Cache for reading, clone for working.** Use `checkout.sh` when you
   just need to read/reference; use `gum clone` when you need a proper
   working copy.
3. **Don't edit cached repos.** Create a worktree or copy instead.
4. **Prefer gum projects over find.** It's indexed and fast. Only fall
   back to `find` if gum is unavailable.
