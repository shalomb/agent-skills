# Issue Triage Standards

Reference for triage-agent. Load when triaging GitHub issues for a Terraform module repository.

## Issue Quality Requirements

A well-formed issue must have:
- Clear, human-readable title (not commit-message style)
- Problem description or feature request details  
- Acceptance criteria (features) or steps to reproduce (bugs)
- Expected vs actual behavior (bugs)

**Title patterns:**
```
# ❌ Bad — commit-message style
docs(Phase 4): KMS cross-organization replication guide
feat: validate customer-managed KMS keys

# ✅ Good — human readable
Documentation: KMS cross-organization replication policy guide
Feature: Validate that KMS keys are customer-managed (not AWS-managed)
```

## Definition of Ready (DoR) Checklist

Every issue must pass DoR before it can be handed to the developer-agent. Validate:

- [ ] **Objective** — one-line goal, clear and specific
- [ ] **Success Criteria** — testable checkboxes, not vague statements
- [ ] **Work Breakdown** — 3–5 major tasks with time estimates
- [ ] **Blockers & Dependencies** — nothing surprising, all known blockers documented
- [ ] **Ecosystem investigation** — related modules checked, patterns identified
- [ ] Developer-agent can start immediately with no clarifying questions

If DoR is met → label `status: ready-for-development`  
If DoR is not met → label `needs-clarification`, comment with what's missing

## Label Taxonomy

| Label | When to apply |
|---|---|
| `type: feature` | New capability |
| `type: bug` | Existing behaviour is wrong |
| `type: docs` | Documentation only |
| `type: chore` | Maintenance, dependency updates |
| `type: security` | Security-related change |
| `priority: critical` | Blocking users or security issue |
| `priority: high` | Important, should be next |
| `priority: medium` | Normal backlog |
| `priority: low` | Nice-to-have |
| `status: ready-for-development` | DoR passed |
| `needs-clarification` | Missing information |
| `duplicate` | Already tracked elsewhere |
| `semver: major` | Breaking change |
| `semver: minor` | Backward-compatible feature |
| `semver: patch` | Bug fix |

## Priority Matrix

| Urgency | Impact | Priority |
|---|---|---|
| High | High | Critical |
| High | Low | High |
| Low | High | High |
| Low | Low | Medium/Low |

Security issues → always Critical regardless of matrix.

## Duplicate Detection

Search before labelling new:
```bash
gh issue list --repo {GITHUB_ORG}/{REPO} --state all --search "keyword"
gh issue list --repo {GITHUB_ORG}/{REPO} --label "type: feature" | grep -i "keyword"
```

If duplicate found: close with comment linking the original.

## DoR Comment Template

```
✅ Definition of Ready validation complete.

**DoR Checklist**:
- [x] Objective: Clear and specific
- [x] Success Criteria: Testable
- [x] Work Breakdown: 3–5 tasks with estimates
- [x] Blockers: Documented
- [x] Ecosystem investigation: Complete

**Triage Findings**:
- Related modules: [list]
- Existing patterns: [list or none]
- Dependencies: [list or none]
- Risks: [list or none]

Ready for development.
```
