---
name: test-design-review
description: >
  Critically review tests or diffs against Dave Farley's Properties of Good Tests
  and Gojko Adzic's Specification by Example principles. Evaluates test speed,
  determinism, atomicity, maintainability, necessity, and behavior-versus-implementation
  fidelity, flagging violations with concrete fixes. Triggers on: 'test review',
  'review tests', 'review these tests', 'critique tests', 'test design review'.
---

# Test Design Review

Review tests (or a git diff containing tests) against an authoritative dual rubric: **Dave Farley's Properties of Good Tests** and **Gojko Adzic's Specification by Example (BDD)**.

---

## The Dual Rubric

### 1. Dave Farley's Properties of Good Tests

Every unit and integration test must satisfy Farley's 6 core properties:

| Property | Standard | Violation Tells |
|---|---|---|
| **Fast** | Unit tests execute in milliseconds; test suite runs in seconds. | Use of `sleep()`, artificial delays, network calls, slow disk I/O in unit tests. |
| **Maintainable** | Tests change only when requirements change, not when internal code refactors. | Fragile mocks coupling to private methods; copy-pasted 50-line test setups. |
| **Repeatable** | Deterministic: passes 1,000 times out of 1,000 runs in any order on any machine. | Flakiness, reliance on system timezone/clock, random seeds without fixed seeding, database pollution across runs. |
| **Atomic** | Each test is completely self-contained, tests one logical behavior, and fails for exactly one reason. | Cascading failures (Test B fails only if Test A runs first), `.first` or `.last` queries dependent on DB ordering. |
| **Necessary** | Every assertion validates a required domain capability or invariant. | Tautological assertions (`assert true`), testing standard library or framework features, redundant `is_successful` checks before body checks. |
| **Understandable** | Serves as living documentation. Clear Arrange-Act-Assert structure and intention-revealing names. | Vague test names (`test_case_1`, `it_works`), mixed levels of abstraction, obscure assertions. |

---

### 2. Gojko Adzic's Specification by Example (BDD)

Tests are executable specifications. They must reflect business behavior, not mechanical wiring:

| Principle | Standard | Violation Tells |
|---|---|---|
| **Behavior over Implementation** | Specify *what* happens in response to a business event, not *how* functions communicate internally. | Asserting method call counts (`verify(service, times(3))`), mocking internal collaborators excessively, inspecting private state. |
| **High Signal-to-Noise Ratio** | Every variable, input, and assertion in the test directly influences the outcome. | Incidental boilerplate, 20 unneeded mock returns, arbitrary dummy data obscuring the relevant parameter. |
| **Concrete Domain Examples** | Illustrate edge cases and rules with realistic domain examples rather than abstract placeholders. | Meaningless test values (`foo`, `bar`, `asdf`, `test1`), lack of domain edge-case verification. |
| **Living Documentation** | Specification names describe scenarios and business consequences. | Technical names (`test_process_data_flag_false`) instead of domain rules (`when_account_is_suspended_reject_withdrawal`). |

---

## Review Process

When reviewing tests:

1. **Locate Target Tests:**
   - If specific files/lines are provided, review those.
   - If a diff or branch is provided, extract all modified or added test files (`git diff origin/main...HEAD -- '*test*' '*spec*'`).
2. **Evaluate Farley Properties:**
   - Audit test speed, isolation, determinism, and atomicity.
   - Check for test pollution risks (global state, uncleaned fixtures, ordering dependencies).
3. **Evaluate Adzic Specification Fidelity:**
   - Check if tests read as executable specifications.
   - Identify tests coupled to implementation details rather than behavior.
   - Check signal-to-noise: flag incidental setup or redundant assertions.
4. **Produce Structured Review Report:**
   - Output the Farley Scorecard & Adzic Scorecard.
   - For every flagged violation: provide file path, line numbers, offending code, explanation, and a drop-in replacement fix.

---

## Review Report Output Template

```markdown
# Test Design Review

## Summary & Recommendation
- **Target:** `<file or diff>`
- **Verdict:** [PASS / NEEDS REVISION / BLOCKING]
- **Key Takeaway:** <1-2 sentences on overall test quality>

## Farley Properties Scorecard
- **Fast:** [Pass / Warning / Fail] — <notes>
- **Maintainable:** [Pass / Warning / Fail] — <notes>
- **Repeatable:** [Pass / Warning / Fail] — <notes>
- **Atomic:** [Pass / Warning / Fail] — <notes>
- **Necessary:** [Pass / Warning / Fail] — <notes>
- **Understandable:** [Pass / Warning / Fail] — <notes>

## Adzic Specification Scorecard
- **Behavior over Implementation:** [Pass / Warning / Fail] — <notes>
- **Signal-to-Noise Ratio:** [Pass / Warning / Fail] — <notes>
- **Concrete Examples:** [Pass / Warning / Fail] — <notes>

## Detailed Findings & Fixes

### 1. [Violation Name] (`path/to/test.ext:L12-L25`)
- **Rubric Rule:** Farley (Atomic) / Adzic (Behavior over Implementation)
- **Problem:** <explanation of the defect>
- **Offending Code:**
```code
<bad code>
```
- **Recommended Fix:**
```code
<improved code>
```
```
