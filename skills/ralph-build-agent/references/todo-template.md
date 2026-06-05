# Terraform Module TODO.md Template

Standard task structure for Terraform Building Block feature work.
Copy and fill in for each new feature or fix.

```markdown
# TODO: [Issue Title]

## Objective
[One-line summary of what we're solving and why]

## Context
[Why this matters, business value, any constraints or dependencies]

## Pre-Work Baseline

**Baseline health**: `make test` passed ✅ / FAILED ⚠️ (pre-existing failures: <list>)
**Interface snapshot** (taken at `<git-sha>`):
- Variables: <N> total (<N> required, <N> optional)
- Outputs: <N>
- Resource addresses: <N>

**Semver pre-classification**:
- Expected bump: MAJOR / MINOR / PATCH
- Design constraint: [what is frozen, what is allowed to change]
- Draft migration guide: [if MAJOR — write migration steps now, before coding]

## Acceptance Criteria (Definition of Done)
- [ ] Baseline was green before work started (or pre-existing failures documented)
- [ ] Interface snapshot taken and semver pre-classified
- [ ] Code implementation complete
- [ ] All quality gates passing (`make format`, `make lint`, `make validate`, `make test`)
- [ ] Examples created and tested (all plan successfully)
- [ ] Documentation updated
- [ ] All variables and outputs documented
- [ ] Breaking change self-assessment complete; actual tier matches pre-classification
- [ ] ADRs created for architecturally significant decisions

## Work Breakdown

### Task 1: Code Implementation
**Objective**: [what to implement]

**Steps**:
1. [step]
2. [step]

**Success Criteria**:
- [ ] `terraform validate` passes
- [ ] Variables have explicit types and descriptions
- [ ] Outputs documented

### Task 2: Examples
**Objective**: [demonstrate the feature]

**Steps**:
1. Create `examples/<name>/` with `main.tf`, `variables.tf`, `outputs.tf`
2. Add `README.md` (copy-paste ready)
3. Test with `terraform plan`

**Success Criteria**:
- [ ] Plans successfully
- [ ] Uses registry source with pessimistic constraint `~> X.Y`

### Task 3: Documentation
**Steps**:
1. Update `Intro.md`
2. Regenerate `README.md` with `make docs`

**Success Criteria**:
- [ ] All variables/outputs documented
- [ ] No broken links

### Task 4: Validation
**Steps**:
1. `make format` — no changes
2. `make lint` — 0 errors
3. `make validate` — valid
4. `make test` — all pass
5. All examples plan successfully

### Task 5: ADR (if needed)
Create if this is a user-facing API change or architectural decision.
Use Y-Statement format — see `references/adr-template.md`.

## Progress
- [ ] Task 1 — Code
- [ ] Task 2 — Examples
- [ ] Task 3 — Docs
- [ ] Task 4 — Validation
- [ ] Task 5 — ADR

## Blockers
[Document any blockers discovered during work]
```
