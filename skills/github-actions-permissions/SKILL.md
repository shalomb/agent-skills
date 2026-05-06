---
name: github-actions-permissions
description: Diagnose and fix GitHub Actions workflow failures caused by Actions permissions policies — startup_failure with no jobs, third-party actions blocked, allowed_actions misconfiguration. Use when workflows fail immediately with no logs, or when actions from outside the repo owner are rejected.
---

# GitHub Actions Permissions

## The symptom

Workflow shows `startup_failure` with **zero jobs** — no runner ever starts,
no logs exist. The Actions UI shows an annotation like:

> The actions `actions/checkout@v4`, `astral-sh/setup-uv@v3` are not allowed
> in `owner/repo` because all actions must be from a repository owned by `owner`.

## Why it happens

GitHub repos can restrict which Actions are permitted via
`Settings → Actions → General → Actions permissions`. Common settings:

| Policy | Meaning |
|--------|---------|
| `all` | Any action allowed |
| `local_only` | Only actions from `owner/*` allowed |
| `selected` | Explicit allowlist (github-owned + patterns) |

`local_only` is the default for many org-owned repos and **silently blocks**
all third-party actions including `actions/checkout` (which is GitHub-owned
but not `owner`-owned).

## Diagnosis

```bash
gh api repos/OWNER/REPO/actions/permissions --jq '{enabled,allowed_actions}'
# {"allowed_actions":"local_only","enabled":true}  ← this is the problem
```

Check what's allowed:
```bash
gh api repos/OWNER/REPO/actions/permissions/selected-actions --jq '.'
```

## Fix

Switch to `selected` and grant the patterns you need:

```bash
gh api repos/OWNER/REPO/actions/permissions \
  --method PUT \
  --input - <<'EOF'
{"enabled": true, "allowed_actions": "selected"}
EOF

gh api repos/OWNER/REPO/actions/permissions/selected-actions \
  --method PUT \
  --input - <<'EOF'
{
  "github_owned_allowed": true,
  "verified_allowed": true,
  "patterns_allowed": ["astral-sh/*", "googleapis/*", "pypa/*", "codecov/*"]
}
EOF
```

**`github_owned_allowed: true`** covers `actions/checkout`, `actions/upload-artifact`,
`actions/download-artifact`, `actions/setup-python`, etc.

**`verified_allowed: true`** covers GitHub Marketplace verified creators.

**`patterns_allowed`** covers anything else — use `owner/*` globs.

## Common patterns to allow by stack

| Actions used | Pattern needed |
|-------------|----------------|
| astral-sh/setup-uv | `astral-sh/*` |
| googleapis/release-please-action | `googleapis/*` |
| pypa/gh-action-pypi-publish | `pypa/*` |
| codecov/codecov-action | `codecov/*` |
| docker/build-push-action | `docker/*` |
| hashicorp/setup-terraform | `hashicorp/*` |
| aws-actions/* | `aws-actions/*` |

## Verify the fix

```bash
gh api repos/OWNER/REPO/actions/permissions/selected-actions --jq '.'
# {
#   "github_owned_allowed": true,
#   "verified_allowed": true,
#   "patterns_allowed": ["astral-sh/*", "googleapis/*", ...]
# }
```

Then re-trigger the failed workflow:
```bash
gh run rerun <run-id> --repo OWNER/REPO
# or push an empty commit to re-trigger push-based workflows
git commit --allow-empty -m "ci: re-trigger after fixing Actions permissions"
git push
```

## Note on org-level policies

If the repo is inside a GitHub org, the org may have its own Actions policy
that overrides repo-level settings. Repo-level `selected` cannot be more
permissive than the org-level policy. If the fix above doesn't work, check:

```bash
gh api orgs/ORG/actions/permissions --jq '{allowed_actions}'
```

Org-level changes require org admin access.
