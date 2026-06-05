---
name: farley-tdd
description: Guide on applying Dave Farley's Properties of Good Tests (TDD). Use this skill to write robust unit tests, practice strict Red-Green-Refactor, or evaluate a test suite using the Farley Index. Triggers on 'farley', 'tdd', 'test driven development', 'unit tests', 'test quality'.
metadata:
  version: 2.0.0
---

# Farley Test-Driven Development (TDD)

This skill provides comprehensive guidance on practicing Test-Driven Development (TDD) and evaluating test quality using Dave Farley's *Properties of Good Tests*.

## Practicing Strict TDD

When writing new features or fixing bugs, follow the Red-Green-Refactor cycle:
1. **Red**: Write a failing test that defines the required behavior.
2. **Green**: Write the minimal production code necessary to pass the test.
3. **Refactor**: Improve the code structure without altering behavior.

All tests written must embody Farley's properties: **Fast, Maintainable, Repeatable, Atomic, Necessary, Understandable**.

## The Farley Index Evaluator

A quantitative diagnostic tool that scores an automated test suite against these six Properties of Good Tests. It shifts the question from **"Do we have tests?"** to **"Can we trust our tests?"**

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

- "farley"
- "tdd"
- "test driven development"
- "write unit tests"
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
