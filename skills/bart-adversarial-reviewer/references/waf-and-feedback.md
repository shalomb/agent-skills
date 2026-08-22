# PR Review Reference: WAF Checklist & FEEDBACK Template

Load when acting as review-agent or doing any infrastructure PR review.

## Well-Architected Framework Review

Apply these lenses to every PR, not just security:

**Operational Excellence** — Can operations teams work with this?
- [ ] Failure modes documented and recoverable
- [ ] Integrates with observability (monitoring, logging, alerting)
- [ ] Debuggable at 3 AM during an incident

**Security** — Least privilege, no exposure
- [ ] Follows principle of least privilege
- [ ] No credential/secret exposure risks
- [ ] Audit-ability maintained (who did what, when)
- [ ] Would survive a security audit

**Reliability** — Failure modes are graceful
- [ ] Single points of failure identified
- [ ] Retry mechanisms appropriate
- [ ] Handles API rate limits, transient failures, timeouts

**Performance Efficiency** — Right-sized, scalable
- [ ] Resource choices appropriate (not over/under-provisioned)
- [ ] Scales predictably
- [ ] No hidden inefficiencies

**Cost Optimization** — No surprise costs
- [ ] No unexpected AWS costs
- [ ] Cost drivers justified
- [ ] Could simpler achieve the same outcome?

## Breaking Change Analysis

Run independent of author's semver declaration:
1. Compare current and proposed interface (variables, outputs, resource addresses)
2. Classify each change: added / changed signature / removed / renamed
3. Determine actual semver tier: MAJOR / MINOR / PATCH
4. Check if actual tier matches author's declared tier
5. Discrepancy = finding that must appear in FEEDBACK.md

## FEEDBACK.md Template

```markdown
# FEEDBACK: PR #NNN — [Title]

## Summary
[1–2 sentences: overall verdict and key concerns]

## Review Decision
- [ ] ✅ APPROVED — ready to merge
- [ ] 🔄 CHANGES REQUIRED — blocking issues must be resolved
- [ ] 💬 COMMENTED — non-blocking observations

## Blocking Issues

### [Issue 1 Title]
**File**: `path/to/file.tf:NN`
**What**: [Describe the problem]
**Why**: [Risk: security / correctness / reliability / breaking change]
**How**: [Suggested fix or pattern to follow]

## Non-Blocking Suggestions

- `file.tf:NN` — [Observation: could improve X]

## Breaking Change Impact
**Declared tier**: MINOR
**Actual tier**: MAJOR (reason: `variable.name` type changed from `string` to `list(string)`)
**Required action**: [Migration steps if MAJOR bump needed]

## Resolution Status
After author pushes fixes:
- [ ] Blocking issue 1 resolved
- [ ] Re-ran `make test` — all passing
- [ ] Breaking change impact confirmed/resolved
```
