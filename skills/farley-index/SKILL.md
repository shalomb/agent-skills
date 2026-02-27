---
name: farley-index
description: "Use this skill to evaluate the quality of an automated test suite using the Farley Index — Dave Farley's Properties of Good Tests (Fast, Maintainable, Repeatable, Atomic, Necessary, Understandable). Produces a scored diagnostic (0–10) and a prioritised list of red flags and recommendations. Triggers include: 'farley index', 'test quality', 'test health', 'brittle tests', 'mock tautology', 'flaky tests', 'test suite audit', 'TDD validation', 'test coupling', 'test theatre'."
license: Private
version: 1.0.0
---

# Farley Index Evaluator

A quantitative diagnostic skill that scores an automated test suite against
Dave Farley's six Properties of Good Tests. It shifts the question from
**"Do we have tests?"** to **"Can we trust our tests?"**

## When to Use This Skill

| Trigger Scenario            | Primary Property to Evaluate | Reason                                                  |
| :-------------------------- | :---------------------------- | :------------------------------------------------------ |
| Onboarding a new developer  | **Understandable**            | Tests should be clear, living specifications.            |
| Planning a refactor         | **Maintainable**              | Tests must survive internal changes without breaking.   |
| CI/CD pipeline is too slow  | **Fast**                      | Identify tests that hit real I/O and slow the pipeline. |
| Debugging flaky test runs   | **Atomic / Repeatable**       | Expose shared state and non-deterministic dependencies. |
| Pre-release quality audit   | **Repeatable / Atomic**       | Confirm tests are trustworthy under parallel execution. |
| Validating TDD practices    | **Necessary**                 | Every line of production code must be demanded by a test.|

## Instructions

1. Read the full reference spec at `docs/reference/farley-index.md`.
2. Collect inputs from the user (source path, test path; optionally logs and VCS flag).
3. Execute the evaluation protocol defined in the reference spec.
4. Output the `farley_index_score`, per-dimension `metrics`, `red_flags`, and `recommendations`.
5. Tailor the depth of analysis to the requesting agent's role:
   - **Bart** → focus on red flags and blockers (Refactor Judge mode).
   - **Ralph** → focus on Necessary + Fast to validate TDD hygiene.
   - **Lisa** → focus on Maintainable + Atomic to inform architecture decisions.
   - **Lovejoy** → focus on Repeatable as a release-gate signal.
   - **Marge** → translate score into plain-language user-impact summary.

## Triggers

- "farley index"
- "farley-index"
- "test quality"
- "test health"
- "brittle tests"
- "mock tautology"
- "test theatre"
- "flaky tests"
- "test suite audit"
- "TDD validation"
- "test coupling"
- "am I really doing TDD"
