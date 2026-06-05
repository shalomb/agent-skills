# Farley Index — Reference Specification

A quantitative rubric for evaluating an automated test suite against
Dave Farley's six Properties of Good Tests. Scores 0–10 across six dimensions.

---

## Inputs

| Parameter        | Type   | Required | Description                                           |
| :--------------- | :----- | :------- | :---------------------------------------------------- |
| `source_path`    | string | Yes      | Path to production source code under test.            |
| `test_path`      | string | Yes      | Path to test files.                                   |
| `ci_logs`        | string | No       | Recent CI run output (for timing, flakiness signals). |
| `vcs_enabled`    | bool   | No       | If true, inspect git log for churn and test age.      |

---

## Six Properties

### 1. Fast (FA)

**Question:** Does the test suite give feedback in seconds, not minutes?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Full suite < 30 s; unit tests < 5 s; no real I/O in unit layer.       |
| 7–8   | Suite < 2 min; isolated slow tests are tagged `@slow`/`@integration`. |
| 4–6   | Suite 2–10 min; tests mix unit logic with database/HTTP calls.         |
| 0–3   | Suite > 10 min; no speed segmentation; developers skip locally.        |

**Detection heuristics (static analysis):**
- `time.sleep()`, `Thread.sleep()`, `asyncio.sleep()` in test bodies.
- Imports of `requests`, `httpx`, `boto3`, `psycopg2`, `pymongo` in unit tests.
- `docker-compose` or `testcontainers` in non-integration test files.
- CI timing data showing p95 > 5 min.

---

### 2. Maintainable (MA)

**Question:** Will this test survive a refactor of production code internals?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Tests call public API only; no `._private` access; no `getattr` hacks. |
| 7–8   | Occasional internal access, but only in helpers, not assertions.       |
| 4–6   | Tests import private modules or patch internal methods via `monkeypatch`.|
| 0–3   | Tests are implementation mirrors — break on every non-behavioural change.|

**Detection heuristics:**
- Attribute access on `._` or `.__` prefixed names in assertions.
- `unittest.mock.patch` targeting internal functions (not I/O boundaries).
- Test file imports matching `src.module._internal`.
- High test churn correlating with production refactors (VCS signal).

---

### 3. Repeatable (RE)

**Question:** Does the test produce the same result regardless of environment, order, or time?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | All non-determinism is controlled; tests pass in any order; no flakes. |
| 7–8   | Rare flakiness (< 1%); known root cause; tracked in issue tracker.     |
| 4–6   | Flakiness > 1%; time-dependent or order-dependent tests present.       |
| 0–3   | Tests routinely skipped or retried in CI; flakiness > 5%.             |

**Detection heuristics:**
- `datetime.now()`, `time.time()`, `Date.now()` without injection/mocking.
- `random` usage without seeding.
- Shared mutable globals or class-level state across tests.
- CI retry configuration (`--retries`, `retry_on_failure`) masking flakiness.
- `@pytest.mark.flaky` or `@Ignore` annotations.

---

### 4. Atomic (AT)

**Question:** Does each test verify exactly one behaviour in isolation?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | One assertion per test; tests are independent; no shared setup state.  |
| 7–8   | 1–2 related assertions per test; no cross-test state leakage.          |
| 4–6   | Tests have 3–5 assertions; setup/teardown creates hidden coupling.     |
| 0–3   | Test classes share mutable state; failure in test N breaks test N+1.  |

**Detection heuristics:**
- >3 `assert` / `expect` calls in a single test function.
- `setUp` / `tearDown` modifying shared class-level state.
- `global` keyword in test helpers.
- Tests using `setUpClass` with mutable data structures.
- Absence of `@pytest.fixture(scope="function")` (using broader scopes carelessly).

---

### 5. Necessary (NE)

**Question:** Is every line of production code demanded by a test?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Code coverage > 90%; no tests assert on mocks only; no redundant tests.|
| 7–8   | Coverage 75–90%; small untested branches (trivial getters, logging).   |
| 4–6   | Coverage 50–75%; large untested paths; tests duplicate each other.     |
| 0–3   | Tests are mock tautologies — assert that mock was called, not behaviour.|

**Mock tautology anti-pattern:**
```python
# Bad — tests the mock, not the behaviour
def test_sends_email():
    mock_sender = Mock()
    service = UserService(email_sender=mock_sender)
    service.register(user)
    mock_sender.send.assert_called_once()  # Only proves the mock was called.

# Good — tests the observable outcome
def test_new_user_receives_welcome_email(fake_mailer):
    service = UserService(email_sender=fake_mailer)
    service.register(user)
    assert fake_mailer.sent_to == [user.email]
    assert "Welcome" in fake_mailer.last_subject
```

**Detection heuristics:**
- `assert_called_once()` / `assert_called_with()` on mocks without verifying return values.
- Test names that describe implementation steps ("test_calls_repository_save").
- `@patch` decorating the system under test itself.
- Coverage report showing critical paths at 0%.

---

### 6. Understandable (UN)

**Question:** Can a new developer read the test and understand the rule it encodes?

**Scoring signals:**

| Score | Signal                                                                 |
| :---- | :--------------------------------------------------------------------- |
| 9–10  | Test name states rule; Arrange/Act/Assert sections visible; no magic.  |
| 7–8   | Test names are descriptive; minor use of unexplained helpers.          |
| 4–6   | Test names are method-oriented (`test_save_user`); helpers obscure flow.|
| 0–3   | Test names are `test1`, `test_2a`; no comments; deeply nested setup.  |

**Detection heuristics:**
- Test function names not following `test_<rule_under_test>_when_<condition>` or similar.
- Magic numbers/strings in assertions without constants or comments.
- Deeply nested helper calls hiding the actual assertion.
- Absence of `# Arrange / # Act / # Assert` or `given/when/then` comment structure.
- Test longer than 20 lines without explanatory comments.

---

## Scoring Formula

```
farley_index_score = round(
  (FA * 0.20) + (MA * 0.20) + (RE * 0.15) +
  (AT * 0.15) + (NE * 0.20) + (UN * 0.10),
  1
)
```

**Weight rationale:**
- FA, MA, NE each 20% — the three properties most directly tied to development velocity.
- RE, AT each 15% — critical for CI trustworthiness but detectable via tooling.
- UN 10% — important for onboarding; harder to score objectively.

---

## Output Format

```json
{
  "farley_index_score": 5.8,
  "grade": "C",
  "metrics": {
    "fast":          { "score": 4, "notes": "Unit tests import requests; suite takes 8 min." },
    "maintainable":  { "score": 7, "notes": "Minor: 2 tests access _internal_state." },
    "repeatable":    { "score": 6, "notes": "3 tests use datetime.now() without mocking." },
    "atomic":        { "score": 7, "notes": "Most tests have 1 assertion; 4 exceptions." },
    "necessary":     { "score": 5, "notes": "Mock tautology pattern in 6 tests." },
    "understandable":{ "score": 5, "notes": "38% of tests have generic names (test_1, test_save)." }
  },
  "red_flags": [
    "test_user_service.py imports `requests` — real HTTP in a unit test (line 4).",
    "test_order_processor.py: `mock_repo.save.assert_called_once()` — mock tautology (line 88).",
    "3 tests use `datetime.datetime.now()` without injection — time-dependent (lines 22, 67, 91)."
  ],
  "recommendations": [
    "Replace real HTTP calls with a `FakeHttpClient` adapter.",
    "Convert mock tautologies to behaviour assertions using a fake repository.",
    "Inject a `ClockService` and freeze time in tests with `FakeClock`."
  ]
}
```

**Grade scale:**

| Score | Grade | Meaning                                                       |
| :---- | :---- | :------------------------------------------------------------ |
| 9–10  | A     | Trustworthy suite. Supports fearless refactoring.             |
| 7–8   | B     | Good foundation; minor issues to clean up.                    |
| 5–6   | C     | Functional but brittle; refactoring is risky.                 |
| 3–4   | D     | Test theatre — tests exist but cannot be trusted.             |
| 0–2   | F     | No meaningful safety net.                                     |

---

## Worked Example

```python
# test_checkout.py

class TestCheckout(unittest.TestCase):
    repo = OrderRepository()   # real DB — class-level!

    def test1(self):
        order = Order(user_id=1, items=[Item("widget", 9.99)])
        result = self.repo.save(order)
        self.assertTrue(result)
        self.mock_emailer.send.assert_called_once()  # mock_emailer undefined!

    def test_discount(self):
        import datetime
        now = datetime.datetime.now()
        order = Order(placed_at=now - timedelta(days=400))
        self.assertFalse(order.is_eligible_for_loyalty_discount())
        self.assertTrue(order.total > 0)
        self.assertIsNotNone(order.id)
```

**Evaluation:**

| Property       | Score | Reason                                                        |
| :------------- | :---- | :------------------------------------------------------------ |
| Fast           | 2     | Real `OrderRepository` (DB) at class level.                   |
| Maintainable   | 3     | Tests depend on internal `Order.id` and `total` fields.       |
| Repeatable     | 3     | `datetime.now()` makes `test_discount` time-dependent.        |
| Atomic         | 3     | `test_discount` has 3 unrelated assertions.                   |
| Necessary      | 2     | `assert_called_once()` on undefined mock — tautology.         |
| Understandable | 1     | `test1` is meaningless name; no Arrange/Act/Assert structure.  |

**farley_index_score = (2×0.20) + (3×0.20) + (3×0.15) + (3×0.15) + (2×0.20) + (1×0.10)**
**= 0.40 + 0.60 + 0.45 + 0.45 + 0.40 + 0.10 = 2.4 → Grade F**

---

## Related Skills

- **Adzic Index** — evaluates BDD/Gherkin specification quality (communication layer).
- **Farley Index** — evaluates unit/integration test trustworthiness (safety net layer).

Target state for a healthy project: **both ≥ 7.0**.
