# Bart's Review Checklist

Reference for adversarial code review. Load this when acting as Bart.

## Review Checklist

**Correctness**
- [ ] Does code match the acceptance criteria?
- [ ] Does it handle error cases?
- [ ] Are edge cases covered?
- [ ] Are boundary conditions tested?

**Security**
- [ ] Are inputs validated/sanitized?
- [ ] Are secrets secure (no hardcoded tokens)?
- [ ] Is auth enforced?
- [ ] Can users do things they shouldn't?

**Performance**
- [ ] Are there obvious bottlenecks?
- [ ] Is data fetched unnecessarily?
- [ ] Are algorithms efficient for scale?
- [ ] Are there memory leaks?

**Robustness**
- [ ] What happens on network failure?
- [ ] What happens on timeout?
- [ ] What happens on bad data?
- [ ] Are retries handled correctly?

**Pattern Adherence**
- [ ] Does it follow established patterns?
- [ ] Does it violate any ADRs?
- [ ] Is it consistent with similar code?

## Feedback Format

Every comment must follow this pattern:

1. **What** — Identify the issue
2. **Why** — Explain the risk (security / perf / correctness / robustness)
3. **How** — Suggest a fix or point to the pattern to follow
4. **Priority** — `[BLOCKER]` (security/critical) or `[SUGGESTION]` (nice-to-have)

**Bad:**
> "This code is terrible. You hardcoded the timeout? What were you thinking?"

**Good:**
> "Line 47: Hardcoded 30-second timeout will fail on slow networks. Recommend making it configurable — see how `config.py` handles this. `[SUGGESTION]`"

## Refactor Judge Prompt

After Ralph's code is Green, evaluate for clean code:

**Input needed:**
1. Original Feature Brief / acceptance criteria
2. The source code Ralph produced
3. The tests that passed

**Evaluate:**
- **Hardcoding?** Did Ralph fake the logic to satisfy specific test data?
- **Duplication?** Is logic repeated where it could be generalized?
- **Clarity?** Does the code express intent, or is it a "random walk" of tokens?
- **Minimal?** Did Ralph add unnecessary complexity or boilerplate?

**Output:** Is the code sufficient as-is, or is a refactor necessary before merge?
