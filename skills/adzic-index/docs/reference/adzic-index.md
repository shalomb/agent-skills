# Adzic Index — Reference Specification

A quantitative rubric for evaluating BDD `.feature` files against Gojko Adzic's
*Specification by Example* principles. Scores 0–10 across six dimensions.

---

## Inputs

| Parameter            | Type   | Required | Description                                      |
| :------------------- | :----- | :------- | :----------------------------------------------- |
| `feature_file_path`  | string | Yes      | Path to the `.feature` file(s) under evaluation. |
| `step_defs_path`     | string | No       | Path to step definition files (for Living check).|
| `vcs_enabled`        | bool   | No       | If true, check git log for last update timestamps.|

---

## Six Dimensions

### 1. Business-Readable (BR)

**Question:** Can a non-technical stakeholder read and confirm intent without help?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Plain English; no code, XPath, CSS selectors, or SQL in any step.     |
| 6–8   | Mostly plain language; occasional technical detail in background/Given.|
| 3–5   | Mix of business and technical language; requires dev to interpret.     |
| 0–2   | Steps are implementation scripts (click button id="submit").           |

**Red flags:**
- Steps containing CSS/XPath selectors, SQL, JSON blobs, or method names.
- `And I wait for 2 seconds` — timing is an implementation detail.
- Acronyms or system codes without a glossary.

---

### 2. Intention-Revealing (IR)

**Question:** Does the scenario describe *what* the system should do, not *how*?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Steps describe business rules and outcomes; zero UI verbs.             |
| 6–8   | Mostly outcome-oriented; 1–2 procedural steps that could be wrapped.  |
| 3–5   | Scenario is a user-journey script with occasional intent signals.      |
| 0–2   | Pure UI script: "click", "fill in", "navigate to", "wait for".        |

**Red flags:**
- UI verbs: `click`, `fill in`, `navigate to`, `press`, `scroll`, `drag`.
- Step names that mirror controller action names (e.g., `I POST to /api/v1/users`).
- Scenarios that only pass because of a specific UI layout.

---

### 3. Declarative (DC)

**Question:** Is each scenario focused on the *rule*, not the *procedure*?

The difference between Imperative and Declarative Gherkin:

```gherkin
# Imperative (bad)
Given I navigate to the login page
And I fill in "username" with "alice"
And I fill in "password" with "s3cr3t"
And I click the "Login" button
Then I should see the dashboard

# Declarative (good)
Given Alice is a registered user
When she logs in with valid credentials
Then she should see her dashboard
```

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | All scenarios use business-level steps; steps compose into sentences.  |
| 6–8   | Mostly declarative; procedural detail is isolated to Background.       |
| 3–5   | Mix; setup is declarative but action steps are imperative.             |
| 0–2   | Scenario is a full UI walkthrough; could be a manual test script.      |

---

### 4. Focused (FC)

**Question:** Does each scenario test exactly one rule?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Single `Then`; title states one clear rule; no compound assertions.    |
| 6–8   | One primary assertion with 1–2 supporting checks (e.g., redirect + message). |
| 3–5   | Multiple `Then` steps testing unrelated concerns.                      |
| 0–2   | Scenario is an end-to-end journey testing 5+ rules at once.            |

**Red flags:**
- Scenario title contains "and" joining two rules (e.g., "validates input and sends email").
- More than 3 `Then` steps.
- `Scenario Outline` with columns that test different rules (not different data).

---

### 5. Living (LV)

**Question:** Is every scenario backed by a working step definition?

**Scoring signals (requires `step_defs_path` or CI output):**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | 0 pending/undefined steps; all pass in CI.                             |
| 6–8   | ≤5% pending; all pending tagged `@wip` with an open ticket.           |
| 3–5   | 6–20% pending or commented-out step definitions.                       |
| 0–2   | >20% pending, or scenarios exist with no step definitions at all.      |

**Without step defs available — proxy signals:**
- `@pending`, `@wip`, `@ignore`, `@skip` tags on scenarios.
- Step text that references UI elements that no longer exist in codebase.
- `TODO` or `FIXME` in step definition comments (if partial path is available).

---

### 6. Cohesive (CH)

**Question:** Do all scenarios in the feature file describe one and only one feature?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Feature title matches all scenarios; single bounded concern.           |
| 6–8   | Minor scope creep; 1–2 scenarios testing adjacent concerns.            |
| 3–5   | Feature file covers 2 distinct features; should be split.              |
| 0–2   | Feature file is a catch-all "miscellaneous" dump.                      |

**Red flags:**
- Feature file title is vague: "User management", "Admin", "API".
- Scenarios reference entities from two unrelated domains.
- More than ~10 scenarios in a single feature file.

---

## Scoring Formula

```
adzic_index_score = round(
  (BR * 0.20) + (IR * 0.20) + (DC * 0.15) +
  (FC * 0.15) + (LV * 0.20) + (CH * 0.10),
  1
)
```

**Weight rationale:**
- BR, IR, LV each 20% — the three failure modes most commonly observed in legacy BDD suites.
- DC, FC each 15% — structural quality; harder to observe without domain knowledge.
- CH 10% — important but often an organisational/tooling problem outside the scenario author's control.

---

## Output Format

```json
{
  "adzic_index_score": 6.4,
  "grade": "C",
  "metrics": {
    "business_readable":    { "score": 8, "notes": "One step contains an XPath selector." },
    "intention_revealing":  { "score": 7, "notes": "Action steps are mostly outcome-focused." },
    "declarative":          { "score": 5, "notes": "Login scenario is imperative (7 UI steps)." },
    "focused":              { "score": 7, "notes": "Two scenarios have compound Then clauses." },
    "living":               { "score": 6, "notes": "3 @pending tags; no ticket references found." },
    "cohesive":             { "score": 4, "notes": "File mixes auth and profile management." }
  },
  "red_flags": [
    "Step 'And I click #submit-btn' contains CSS selector (line 14).",
    "Scenario 'User registers and receives email' tests two rules (line 32).",
    "Feature file covers both authentication and profile editing — split recommended."
  ],
  "recommendations": [
    "Extract profile scenarios to `user-profile.feature`.",
    "Replace imperative login steps with `Given Alice is logged in` step.",
    "Resolve 3 @pending scenarios or tag them with Jira/GitHub issue references."
  ]
}
```

**Grade scale:**

| Score | Grade | Meaning                                     |
| :---- | :---- | :------------------------------------------ |
| 9–10  | A     | Living specification. Ship it.              |
| 7–8   | B     | Good; minor cleanup before next sprint.     |
| 5–6   | C     | Functional but communicates poorly.         |
| 3–4   | D     | Specification theatre — tests pass, meaning is lost. |
| 0–2   | F     | UI script masquerading as specification.    |

---

## Worked Example

```gherkin
Feature: User authentication

  Scenario: Successful login
    Given I navigate to "/login"
    And I fill in "email" with "alice@example.com"
    And I fill in "password" with "hunter2"
    And I click "#login-btn"
    Then I should see "Welcome, Alice"

  Scenario: Failed login shows error
    Given a registered user with email "alice@example.com"
    When she logs in with the wrong password
    Then she should see "Invalid credentials"
    And her account should not be locked after one attempt
```

**Evaluation:**

| Dimension          | Score | Reason                                                        |
| :----------------- | :---- | :------------------------------------------------------------ |
| Business-Readable  | 4     | Scenario 1 has CSS selector and raw URL.                      |
| Intention-Revealing| 3     | Scenario 1 is a UI script with click/fill verbs.              |
| Declarative        | 4     | Scenario 1 is entirely imperative.                            |
| Focused            | 6     | Scenario 2 has two Then assertions (error + lock check).      |
| Living             | 9     | All steps defined; no pending tags.                           |
| Cohesive           | 9     | Feature file covers one concern.                              |

**adzic_index_score = (4×0.20) + (3×0.20) + (4×0.15) + (6×0.15) + (9×0.20) + (9×0.10)**
**= 0.80 + 0.60 + 0.60 + 0.90 + 1.80 + 0.90 = 5.6 → Grade C**

---

## Related Skills

- **Farley Index** — evaluates unit/integration test quality (trustworthiness layer).
- **Adzic Index** — evaluates BDD scenario quality (communication layer).

Target state for a healthy project: **both ≥ 7.0**.
