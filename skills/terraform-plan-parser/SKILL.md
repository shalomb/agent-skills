---
name: terraform-plan-parser
description: Parse and analyse terraform plan plain-text output to classify resource changes, detect unintended mutations, and produce structured reports. Use when reviewing terraform plan output for import safety, drift detection, or plan validation. Triggers on "parse plan", "plan analysis", "plan diff", "classify changes", "import validation", "zero-change check", or any post-hoc analysis of terraform plan stdout.
---

# Terraform Plan Parser

Parse `terraform plan -no-color` plain-text output into structured data for
programmatic analysis. Designed for TFC remote backends where `-json` and
`-out=` are unavailable.

## Parser location

The parser is a standalone Python module. Set `PLAN_PARSER_DIR` to its location:

```bash
# Example — adjust to your repo layout
export PLAN_PARSER_DIR="$HOME/your-repo/src/framework/parsers"
```

**Import path:**
```python
import sys
sys.path.insert(0, os.environ["PLAN_PARSER_DIR"])
from terraform_plain_text_plan_parser import TerraformPlainTextPlanParser
```

## Quick start

### 1. Capture plan output

```bash
PLAN_DIR=$(mktemp -d)
cd iac/{env}
terraform plan -no-color 2>&1 | tee "$PLAN_DIR/{env}-plan.txt"
```

Always use `-no-color`. The parser strips ANSI codes but clean input is faster.

### 2. Parse

```python
from terraform_plain_text_plan_parser import TerraformPlainTextPlanParser

with open(f"{plan_dir}/dev-plan.txt") as f:
    result = TerraformPlainTextPlanParser(f.read()).parse()
```

Returns a dict with `resource_changes` list. Each entry:
```python
{
    "address": "module.alb.aws_lb_listener.this[\"http\"]",
    "change": {
        "actions": ["update", "import"],  # or ["create"], ["delete"], ["import"]
        "before": { ... },   # null for create/import-only
        "after":  { ... },   # null for delete
    }
}
```

### 3. Classify changes

| `actions` | Meaning | Terraform counts as |
|-----------|---------|-------------------|
| `["import"]` | Pure import — state adoption, no API write | import |
| `["update", "import"]` | Import + update — state adopted AND attributes changed | import + change |
| `["create"]` | New resource | add |
| `["delete"]` | Destroy | **STOP — investigate** |
| `["update"]` | In-place update (post-import, steady state) | change |

### 4. Detect real mutations

On import, many "changes" are just state population (before=null). Filter to
real mutations where both before AND after have values:

```python
for rc in result["resource_changes"]:
    if "update" not in rc["change"]["actions"]:
        continue
    before = rc["change"].get("before") or {}
    after = rc["change"].get("after") or {}
    for k in set(list(before) + list(after)):
        if k in ("tags", "tags_all"):
            continue
        bv, av = before.get(k), after.get(k)
        if bv is not None and av is not None and bv != av:
            print(f'{rc["address"]}: {k}: {bv} → {av}')
```

## Import validation target

The goal for Terraform import workflows:

```
Plan: N to import, 0 to add, 0 to change, 0 to destroy.
```

- **Destroys must be 0** — any destroy is a blocker.
- **Adds**: internal resources like `terraform_data` may be expected. Verify.
- **Changes**: all should be tag normalization or import state population. No
  real attribute mutations on load balancers, databases, etc.

Use the mutation filter above to prove "no real changes" vs "cosmetic import diffs".

## Issue status template

When posting plan results to GitHub issues, use the template at
[`resources/issue-status-template.md`](resources/issue-status-template.md).

## Known parser limitations

- Plain-text parser cannot distinguish `(known after apply)` computed values
  from actual changes. Use `-json` output (via TFC API `plans/{id}/json-output`)
  when available for precise before/after comparison.
- Nested block diffs (e.g. `forward { stickiness { ... } }`) are flattened
  into the parent resource's attribute map. Cross-reference with the raw plan
  text for nested block analysis.

## Related skills

- **tfc-api** — `get-plan.sh` fetches plan logs; pipe output to this parser
- **terraform-dev** — inner-loop plan analysis during development
