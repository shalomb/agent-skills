# Authentication & Session Reuse

## The core assumption

The whole automation rests on one bet:

> **Authenticate interactively once. Reuse that credential headlessly, forever
> after, from cron, with no human present.**

This is **proven to work** (see *Evidence*, below). It was verified against a
Chrome profile whose last interactive SSO was **104 days** earlier, running
headless with zero interaction. If you are debugging a failure, do not start by
assuming the credential expired — that is almost never the cause, and chasing it
has historically sent people down the wrong path for weeks.

## How the protocol actually works

There are **two** sessions with very different lifetimes. Conflating them is the
root of most bugs in this area.

### Layer 1 — the durable Entra credential (~90 days)

`setup_auth.py` opens a headed Chrome against a **persistent
`user_data_dir`** and walks a human through Entra SSO. On success Microsoft
sets a persistent cookie into that profile:

```
ESTSAUTHPERSISTENT   domain=.login.microsoftonline.com   expires=+90 days
```

This is the "authenticate once" artifact. It survives reboots, and it is the
*only* thing that must be renewed by a human — roughly quarterly.

> **Gotcha — `auth.json` is a decoy.** A `storage_state()` file is written at
> `$XDG_STATE_HOME/agent-skills/agilquest-reservations/auth.json` by an older
> auth model (commit `51c4379`). Nothing in the current code path reads it. It
> is stale — from 26 May in the observed environment — and its age tells you
> **nothing** about whether auth is healthy. Ignore it. It should probably be
> deleted.

### Layer 2 — the ephemeral Agilquest session (~10 minutes)

Agilquest itself will not accept the Entra cookie directly. Every run must mint
a fresh session by walking the **MS app launcher**:

```
APP_LAUNCHER (launcher.myapps.microsoft.com/api/signin/<app-id>?tenantId=<tenant>)
  → 302 → login.microsoftonline.com/<tenant>/oauth2/authorize?...   [replays ESTSAUTHPERSISTENT]
  → SAML auto-submit form (POSTs itself, no user interaction)
  → login.agilquest.com/samlsuccess?authToken=<opaque-token>
  → SPA client-side exchange  ⟵ THE CRITICAL, EASILY-MISSED STEP
  → session cookies set: AUTH_DATA, JSESSIONID
```

This is why **every** entry point must go through `APP_LAUNCHER` first, and why
a direct `goto()` of a reservations URL can never work from a cold context.

### The step everyone misses

The URL stops moving at `/samlsuccess?authToken=…`. **The session does not
exist yet at that moment.** The SPA then spends a few seconds exchanging that
token for real cookies. Only when `AUTH_DATA` appears is the session live.

Navigate away during that window and the token is discarded — the app bounces
you to a `LOG IN` screen, and the *only* symptom is empty data.

## Signals — what to trust, what lies

| Signal | Trustworthy? | Notes |
|---|---|---|
| `AUTH_DATA` cookie on `login.agilquest.com` | **Yes** | Positive proof the exchange completed. Wait on this. |
| `page.evaluate("location.href")` | **Yes** | Always reflects the real document location. |
| `page.url` | **No** | Lags behind client-side/SAML redirects. See bug #1. |
| `nav` / `.navbar` selector present | Weak | Renders on some pre-auth pages too. Not proof of a session. |
| `get_reservations()` returning `[]` | **No** | Ambiguous: "no bookings" or "not authenticated". See bug #4. |
| Presence of `input[name='loginfmt']`, `#i0116` | **Yes** | Proof that Entra genuinely wants interactive login. |

## Known bugs & gotchas

These are the defects this spec exists to pin down. Each has a matching test.

### Bug #1 — `wait_until="commit"` makes `page.url` lie

Introduced in commit `e887e70` to dodge a hang. `commit` resolves as soon as the
*first response byte* arrives — long before the SAML chain finishes. Playwright's
`page.url` then reports the intermediate Microsoft URL while the document has
already moved on. Observed 8s after nav:

```
page.url                        →  https://login.microsoftonline.com/<tenant>/oauth2/authorize?...
page.evaluate("location.href")  →  https://login.agilquest.com/samlsuccess?authToken=...
document.domain                 →  login.agilquest.com
rendered body                   →  "Shalom Israel Bhooshi … Upcoming Reservations … Checked In"
```

The browser was **fully authenticated**. But `establish_session()` branches on
`page.url`:

```python
if "microsoftonline" in page.url:
    return False  # "MS SSO needs interactive login"   ← WRONG. It's mid-redirect.
```

Every caller then reports auth failure. This is the primary regression.

**Fix:** read the URL via `location.href`; decide "needs SSO" from the presence
of a login *form*, never from a URL substring.

**Also:** `domcontentloaded` does **not** hang — measured at 7.0–7.7s,
returning the correct `samlsuccess` URL. The hang that motivated `commit` was
almost certainly bug #2 misattributed.

### Bug #2 — a stale `SingletonLock` masquerades as a network timeout

A crashed or orphaned Chrome leaves `SingletonLock` / `SingletonCookie` /
`SingletonSocket` symlinks in the profile. Any later launch dies with:

```
Failed to create a ProcessSingleton for your profile directory.
This usually means that the profile is already in use by another instance.
```

`clear_singleton_lock()` exists — but **only in `setup_auth.py`**. The four cron
entry points call `launch_headless()` directly and never clear it, so one
crashed run poisons the profile until a human runs setup-auth. This produced the
`launch_persistent_context: Timeout 180000ms exceeded` log entries.

**Fix:** clear the lock inside `_persistent_context()` so every entry point
self-heals.

### Bug #3 — navigating before `AUTH_DATA` silently discards the session

The `wait_for_selector("nav, .navbar, [class*='nav']")` that follows the
launcher nav is wrapped in `except: pass`. It is treated as cosmetic. **It is
not** — it is the only thing gating the token exchange, and swallowing its
failure lets the code navigate away mid-exchange.

Reproducible A/B, same profile, same run, 3/3 trials:

```
NO settle (current code path)   ->  0 reservation(s)     # bounced to LOG IN
WITH settle (wait AUTH_DATA)    ->  4 reservation(s)     # real data
```

**Fix:** wait for the `AUTH_DATA` cookie — a positive completion signal —
instead of guessing with a DOM selector whose failure is ignored.

### Bug #4 — auth failure is indistinguishable from "no bookings"

`get_reservations()` wraps its whole body in `except Exception: pass` and
returns `[]`. A lost session therefore reports as *zero reservations* rather
than an error, so `ensure_reservation.py` concludes nothing is booked and
attempts to rebook — masking the real fault.

**Fix:** detect the `LOG IN` screen explicitly and raise, rather than returning
an empty list.

### Not a bug — `.parent` depth in `trigger_reauth_and_wait()`

```python
scripts_dir = Path(__file__).parent.parent.parent.parent
```

Recorded here because it *looks* wrong and was flagged as a defect during
review. It is correct. From
`scripts/src/agilquest_reservations/lib/browser.py`, four `.parent`s resolve to
`scripts/` — the directory holding `pyproject.toml`, which is what the
osascript `cd` needs. The count differs from the three used by the old
`ensure_reservation.py` copy purely because `lib/` adds a directory level.

Verified:

```
file      : .../scripts/src/agilquest_reservations/lib/browser.py
4x parent : .../scripts          ← correct
3x parent : .../scripts/src      ← would be wrong
```

A test pins this so the next reader does not "fix" it back into a bug.

### Gotcha — the profile is single-owner

Chrome permits exactly one process per `user_data_dir`. `setup_auth.py` (headed)
and any headless run therefore **cannot** overlap. `trigger_reauth_and_wait()`
must close the caller's context before polling, and polls by opening and closing
its own short-lived context each time.

### Gotcha — error messages point at the wrong layer

Bugs #1, #2 and #3 all surfaced as the *same* string:

```
Page.goto: Timeout 30000ms exceeded
```

That text implicates the network. None of the three causes were network. This is
why earlier fixes added DNS seeding, `caffeinate`, and prewarm jobs — treating a
symptom whose cause lay elsewhere. **Diagnose by layer** (lock → Entra cookie →
launcher redirect → `AUTH_DATA`) before touching anything network-shaped.

## Evidence

Captured 2026-09-07 against a profile last interactively authenticated
2026-05-26 (104 days prior), headless, non-interactive:

```
STEP 1 — SAML exchange via app launcher (no interaction)
  nav completed in 7.7s
  landed: https://login.agilquest.com/samlsuccess?authToken=962cb031...
  interactive MS login form present: False

Durable credential in profile:
  ESTSAUTHPERSISTENT   domain=.login.microsoftonline.com   expires=2026-12-06

Agilquest session cookies after exchange:
  AUTH_DATA     domain=login.agilquest.com    expires=session
  JSESSIONID    domain=auth.agilquest.com     expires=session

Authenticated read (WITH settle):
  274269  SK-BRA-06.01.W1024  September 07, 2026 - 07:05 AM  Checked In
  274838  SK-BRA-06.01.W1024  September 08, 2026 - 09:00 AM  Awaiting Check In
  275350  SK-BRA-06.01.W1024  September 09, 2026 - 09:00 AM  Awaiting Check In
  275778  SK-BRA-06.01.W1024  September 10, 2026 - 09:00 AM  Awaiting Check In
```

**Conclusion:** the credential model is sound. No re-architecture, no token
refresh scheme, no move off the persistent profile is required. Every observed
failure lives in the ~40 lines that decide *when* the session is ready.

## Renewal

`ESTSAUTHPERSISTENT` expires roughly quarterly. When it does — and only then —
the launcher genuinely lands on an Entra login form and a human must run:

```
aq setup-auth
```

The distinguishing signal is a **login form element**, not a URL substring and
not an empty result set.
