# Auth & session tests

Specs and tests for the one assumption the whole skill rests on: **authenticate
interactively once, reuse that credential headlessly from cron forever after.**

## Running

```bash
cd scripts
uv sync --group dev
uv run pytest tests/ -q          # fast, hermetic — no Chrome, no network
```

Live checks against real Chrome / Entra / Agilquest are opt-in:

```bash
AQ_LIVE_TESTS=1 uv run pytest tests/ -v
```

Live tests are **read-only** — they authenticate and read reservations. Nothing
books, cancels, or checks in. Keep it that way.

## Expected state today

```
22 failed, 7 passed, 7 skipped
```

**The failures are the specification, not a broken suite.** They are written
test-first against an API that does not exist yet; each one pins a bug
catalogued in `../../features/auth_and_session.md`. Implement until they pass.
Do not weaken a test to match current behaviour.

The 7 passing tests are *characterisation* tests — they document how the
browser and the app actually behave today (e.g. that `page.url` really does go
stale after a `commit` navigation). If one of those ever starts failing, the
underlying platform changed and the docs need revisiting.

The 7 skipped are the live integration tests.

## What to implement

`agilquest_reservations.lib.browser` needs:

| Function | Purpose |
|---|---|
| `current_url(page)` | Authoritative location via `location.href`, falling back to `page.url`. |
| `needs_interactive_login(page)` | True only when a real login **form** is present — never a URL substring. |
| `wait_for_session(context, page, timeout)` | Block until the `AUTH_DATA` cookie appears; return False on timeout. |
| `establish_session(page, context=...)` | Full launcher flow; must not return True before the session exists. |
| `clear_singleton_lock(profile_dir)` | Remove stale `Singleton*` symlinks; called from every launch. |
| `diagnose(...)` | Report which layer failed: `profile_lock` / `interactive_login` / `session_exchange` / `network`. |

`agilquest_reservations.lib.agilquest.get_reservations` must raise on the
`LOG IN` screen rather than returning `[]`.

## Suggested order

1. `current_url` + `needs_interactive_login` — fixes the primary regression (bug #1).
2. `wait_for_session` + wire into `establish_session` — fixes the silent session loss (bug #3).
3. `get_reservations` raising on the login screen (bug #4).
4. `clear_singleton_lock` in `_persistent_context` (bug #2).
5. `diagnose` — stops the three failure modes all reporting as a network timeout.

Steps 1–2 are what actually restore booking. 3–5 stop the next misdiagnosis.

## The fakes

`conftest.py` models the *protocol*, not Playwright's API. The important part:
`FakePage.url` deliberately lags behind `evaluate("location.href")` during a
`commit` navigation, and the Agilquest session only exists after the token
exchange completes. That is what makes these bugs reproducible without a
browser.

## Before you touch anything network-shaped

Bugs #1, #2 and #3 all surfaced as the identical string:

```
Page.goto: Timeout 30000ms exceeded
```

None of them were network faults. Earlier rounds of fixes added DNS seeding,
`caffeinate`, and prewarm cron jobs chasing that message. Diagnose by layer —
profile lock → Entra cookie → launcher redirect → `AUTH_DATA` — before assuming
connectivity.
