---
name: adzic-index
description: "Use this skill to evaluate the quality of BDD feature files and Gherkin scenarios using the Adzic Index — based on Gojko Adzic's Specification by Example principles. Produces a scored diagnostic (0–10) across six dimensions: Business-Readable, Intention-Revealing, Focused, Declarative, Minimal Context, and Living. Triggers include: 'adzic index', 'BDD quality', 'gherkin quality', 'scenario quality', 'feature file audit', 'specification theatre', 'living documentation', 'acceptance criteria quality', 'UI script theatre', 'imperative gherkin'."
license: Private
version: 1.0.0
---

# Adzic Index Evaluator

A quantitative diagnostic skill that scores BDD `.feature` files against
Gojko Adzic's Specification by Example principles. The companion to the
Farley Index — together they cover the complete quality picture.

It shifts the question from **"Do our scenarios pass?"** to
**"Do our scenarios communicate the right thing to the right people?"**

## When to Use This Skill

| Trigger Scenario                  | Primary Dimension      | Reason                                                        |
| :-------------------------------- | :--------------------- | :------------------------------------------------------------ |
| Writing a new Feature Brief       | **Business-Readable**  | Verify non-technical stakeholders can read and confirm intent.|
| Planning an Epic                  | **Living**             | Ensure all scenarios have executable step definitions.        |
| Reviewing before a refactor       | **Intention-Revealing**| Confirm scenarios won't break on internal implementation change.|
| Debugging brittle acceptance tests| **Declarative**        | Expose UI-scripted steps that couple specs to the interface.  |
| Pre-release quality audit         | **Living**             | No `@pending` scenarios at ship time.                        |
| Auditing inherited feature files  | **All six**            | Full health check of a legacy BDD suite.                      |

## Instructions

1. Read the full reference spec at `docs/reference/adzic-index.md`.
2. Collect inputs (feature file path; optionally step definition path and VCS flag).
3. Execute the evaluation protocol defined in the reference spec.
4. Output the `adzic_index_score`, per-dimension `metrics`, `red_flags`, and `recommendations`.
5. Tailor depth of analysis to the requesting agent's role:
   - **Marge** → focus on Business-Readable + Intention-Revealing (she writes the scenarios).
   - **Lisa** → focus on Living + Focused (Epic readiness gate).
   - **Ralph** → focus on Declarative + Living (step definition quality self-audit).
   - **Bart** → full audit; use as adversarial evidence base for merge decisions.
   - **Lovejoy** → focus on Living as a release go/no-go signal.

## Relationship to the Farley Index

| Layer              | Index             | Question                                                      |
| :----------------- | :---------------- | :------------------------------------------------------------ |
| BDD Specification  | **Adzic Index**   | Clear, executable, stakeholder-readable specification?        |
| TDD Unit Test      | **Farley Index**  | Fast, honest, implementation-independent test?                |

Target state: **Both ≥ 7.0.** This is "Clean Code that Works, clearly specified."

## Triggers

- "adzic index"
- "adzic-index"
- "BDD quality"
- "gherkin quality"
- "scenario quality"
- "feature file audit"
- "specification theatre"
- "living documentation"
- "acceptance criteria quality"
- "UI script theatre"
- "imperative gherkin"
- "are my scenarios any good"
