---
name: terraform-dev
description: Continuous validation during Terraform module development. Use when actively developing Terraform code and needing fast feedback loops — runs format, validate, lint, and plan automatically. Covers inner loop (fast, local) and outer loop (TFC deployment) development patterns.
---

# Terraform Development Loop

Fast feedback during active Terraform development using Makefile targets.

## Prerequisites

- `make` — drives all targets below
- `terraform` — for format, validate, and plan
- `tflint` — for lint targets
- `entr` or `watchexec` — optional, for file-watch mode (see [Watching for Changes](#watching-for-changes))

## Inner Loop (Fast — < 30s)

Run after every meaningful code change:

```bash
make format          # terraform fmt -recursive (~1s)
make validate        # terraform validate (~2s)
make lint            # tflint (~5s)
```

Compose for a single fast-fail check:

```bash
make format && make validate && make lint
```

**What each catches**:
- `make format` — inconsistent indentation, alignment
- `make validate` — type errors, undefined references, malformed HCL
- `make lint` — security defaults too open, missing types, `lookup()` usage, line length

## Outer Loop (Full — 2–5 min)

Run before pushing or opening a PR:

```bash
make pre-pr          # format + validate-full + lint + docs + examples
```

## Example Testing Loop

When changing module interface (variables, outputs, resources):

```bash
# Convert to local source for testing
make relative-source

# Test all examples against local code
make test-examples

# Revert to registry source before committing
make registry-source
```

## TFC Deployment Loop

For real-world validation against a live AWS account:

```bash
# Deploy example to test workspace
make deploy EXAMPLE=basic WORKSPACE=<tec-dce-inn-dev-XXXXX-username>

# Monitor run
make tfc-run-status EXAMPLE=basic

# Inspect deployed resources (tags, names, outputs)
make tfc-workspace-state EXAMPLE=basic

# Tear down
make deploy-clean EXAMPLE=basic
```

## Safe Experimentation

Before risky refactors:

```bash
make checkpoint MSG="before restructuring locals"
# ... make changes ...
# If it goes wrong: git reset --soft HEAD~1
```

## Watching for Changes

For continuous validation while editing multiple files:

```bash
# Run inner loop on every save (requires entr or watchexec)
find . -name "*.tf" | entr -c make format validate lint

# Or use terraform-docs watcher if available
```

## Common Failures and Fixes

| Failure | Likely cause | Fix |
|---------|-------------|-----|
| `validate` fails on type | Variable uses `any` type | Specify explicit type |
| `lint` complains about `lookup()` | Using `lookup()` | Replace with `local.map[var.key]` |
| `test-examples` fails init | Registry source, no TFC auth | `make relative-source` first |
| `docs` fails | Missing variable description | Add description to all variables |
| `format` changes files | Ran code before `make format` | Run `make format` before all commits |

## References

- `tfc-api` skill — direct TFC API queries for deeper workspace inspection
