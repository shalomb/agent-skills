---
name: farley-tdd
description: >
  Audit and score an existing test suite against Dave Farley's Properties of
  Good Tests using the Farley Index. Use when tests already exist and the
  question is whether they can be trusted — flaky runs, slow CI, brittle tests,
  or validating that TDD was actually practised. For writing new code test-first
  use `test-driven-development`; for reviewing specific tests or a diff use
  `test-design-review`. Triggers on: 'farley', 'farley index', 'test quality',
  'test suite audit', 'flaky tests', 'am I really doing TDD'.
metadata:
  version: 2.0.0
---

# Farley Test-Driven Development (TDD)

This skill provides comprehensive guidance on practicing Test-Driven Development (TDD) and evaluating test quality using Dave Farley's *Properties of Good Tests*.

## What Good TDD Looks Like

Reference criteria for judging whether TDD was actually practised. To *do* TDD
on new code, use `test-driven-development` — this section is the yardstick, not
the workflow.

The Red-Green-Refactor cycle:
1. **Red**: Write a failing test that defines the required behavior.
2. **Green**: Write the minimal production code necessary to pass the test.
3. **Refactor**: Improve the code structure without altering behavior.

A suite where **Refactor** was routinely skipped shows up as duplication across
test setup and production code that no test ever forced out. Score it under
*Maintainable* and *Understandable*.

**Canon TDD Pitfalls (via Kent Beck)** — evidence of these in the history or the
suite means the cycle was not followed:
- **Speculative Tests**: Do not write all tests upfront. Convert exactly one item from your test list into a concrete test, make it pass, then move to the next.
- **Mixing Interface & Implementation**: The "Red" phase is for designing the interface. The "Refactor" phase is for designing the implementation. Do not mix them.
- **Abstracting Too Soon**: In the "Refactor" phase, remember that duplication is a hint, not a command. Don't over-abstract prematurely.

All tests written must embody Farley's properties: **Fast, Maintainable, Repeatable, Atomic, Necessary, Understandable**.

> **Note**: For tactical guidance on writing good assertions and avoiding brittle setup patterns, use the **`test-design-review`** skill.

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

### Not this skill

| If the user wants to… | Use |
| :-------------------- | :-- |
| Write new code test-first | `test-driven-development` |
| Review specific tests or a diff | `test-design-review` |
| Burn down a TODO.md backlog | `ralph-build-agent` |
| Evaluate Gherkin/BDD specs | `adzic-bdd` |
