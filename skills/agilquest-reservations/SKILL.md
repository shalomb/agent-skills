---
name: agilquest-reservations
description: >
  Monitor and manage workspace reservations on Agilquest. Retrieve active reservations,
  check workspace availability, check in, book ahead, and automate recurring reservation
  checks via cron. Uses headless browser automation with cached Entra SSO authentication.
---

# Agilquest Reservations

Headless browser automation for Agilquest workspace reservation portal using Playwright.
Handles Entra SSO authentication (cached for days) and retrieves reservation data.

## Prerequisites

- Google Chrome or Chromium installed
- `uv` package manager: `pip install uv` or `brew install uv`
- One-time auth setup completed (Step 0)
- Entra SSO access to Agilquest

## Chrome path configuration

The scripts read `CHROME_PATH` from the environment, falling back to platform defaults:

```bash
# macOS
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Linux
export CHROME_PATH="/usr/bin/google-chrome"

# Or set permanently in ~/.config/agent-skills/agilquest-reservations.env:
# CHROME_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

Browser session stored at: `~/.local/state/agent-skills/agilquest-reservations/user_data/`
(persistent; do not delete)

Last scraped reservations table is cached at:
`~/.local/state/agent-skills/agilquest-reservations/reservations_cache.json`
(written automatically by every live fetch; read by `aq status`)

## `aq` CLI

The scripts are packaged as an installable `aq` command for day-to-day use.

### Install (one-time)
```bash
cd skills/agilquest-reservations/scripts
uv tool install --editable .
```
This puts `aq` on your PATH (`~/.local/bin/aq` via `uv tool`). Because it's
an editable install, pulling changes to this skill takes effect immediately —
no reinstall needed.

### Commands
```bash
aq checkin              # Check in to today's reservation, then book +7 days if missing
aq book                 # Book +7 days ahead (same booking step, standalone)
aq book 2026-09-16      # Book a specific date
aq book +3              # Book 3 days from today
aq status                # Today's status + 14-day calendar — offline, reads the cache only
aq status --days 30      # Wider calendar window
aq setup-auth            # Interactive SSO login (one-time, or when sessions expire)
```
Run `aq <command> --help` for full options (`--assets`, `--start`, `--end`, `--prestage`).

`aq status` never launches Chrome — it's instant (well under a second) and reads
whatever `aq checkin` / `aq book` / any other fetch last wrote to the cache. Run one
of those first to populate it; after that `aq status` is safe to call as often as
you like (e.g. in a shell prompt or status bar).

## Step 0: Setup Auth (one-time)

Establish persistent browser session with Entra SSO:

```bash
aq setup-auth
# or, without installing aq:
cd skills/agilquest-reservations/scripts && uv run src/agilquest_reservations/setup_auth.py
```

A Chrome window opens to `https://login.agilquest.com/myreservations`. Sign in via Entra SSO manually.
The session is cached and reused for all future headless runs.

## Step 1: Check Active Reservations

### Basic check
```bash
cd skills/agilquest-reservations/scripts && uv run src/agilquest_reservations/get_reservations.py
```

### Check specific workspace (asset 343)
```bash
uv run src/agilquest_reservations/get_reservations.py --asset-id 343
```

### Output format
JSON array of active reservations:
```json
[
  {
    "id": "RES-12345",
    "workspace": "Desk 4B",
    "asset_id": 343,
    "date": "2026-05-10",
    "time": "09:00 - 17:00",
    "status": "active"
  }
]
```

## Step 1b: Check In + Book Ahead

Checks in to today's reservation (if awaiting check-in) and ensures a
reservation exists 7 days ahead, booking it via the same asset-fallback
logic as `aq book` if missing:

```bash
aq checkin
# or:
cd skills/agilquest-reservations/scripts && uv run src/agilquest_reservations/checkin_and_book.py
```

Options: `--skip-checkin`, `--skip-book`, `--assets`, `--start`, `--end`
(see script docstring). Not currently scheduled via cron — run manually or
wire up with `/schedule` if daily automation is wanted.

## Step 2: Schedule Recurring Checks

Use the `schedule` skill to run on a cron schedule:

```bash
/schedule agilquest-check "0 9 * * *"
```

This checks reservations every day at 9 AM and returns the JSON output.

## Capabilities

| Operation | Command |
|-----------|---------|
| Check all reservations | `uv run src/agilquest_reservations/get_reservations.py` |
| Check specific asset | `uv run src/agilquest_reservations/get_reservations.py --asset-id 343` |
| Check in + book ahead | `aq checkin` |
| Book a date | `aq book [DATE]` |
| Status + calendar (offline) | `aq status` |
| Setup auth | `aq setup-auth` |

## Environment variables

- `CHROME_PATH` — Path to Chrome/Chromium executable
- `AGILQUEST_ASSET_ID` — Default workspace asset ID (optional)
