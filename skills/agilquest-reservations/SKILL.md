---
name: agilquest-reservations
description: >
  Monitor and manage workspace reservations on Agilquest. Retrieve active reservations,
  check workspace availability, and automate recurring reservation checks via cron.
  Uses headless browser automation with cached Entra SSO authentication.
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

## Step 0: Setup Auth (one-time)

Establish persistent browser session with Entra SSO:

```bash
cd skills/agilquest-reservations/scripts && uv run src/setup_auth.py
```

A Chrome window opens to `https://login.agilquest.com/myreservations`. Sign in via Entra SSO manually.
The session is cached and reused for all future headless runs.

## Step 1: Check Active Reservations

### Basic check
```bash
cd skills/agilquest-reservations/scripts && uv run src/get_reservations.py
```

### Check specific workspace (asset 343)
```bash
uv run src/get_reservations.py --asset-id 343
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

## Step 2: Schedule Recurring Checks

Use the `schedule` skill to run on a cron schedule:

```bash
/schedule agilquest-check "0 9 * * *"
```

This checks reservations every day at 9 AM and returns the JSON output.

## Capabilities

| Operation | Command |
|-----------|---------|
| Check all reservations | `uv run src/get_reservations.py` |
| Check specific asset | `uv run src/get_reservations.py --asset-id 343` |
| Setup auth | `uv run src/setup_auth.py` |

## Environment variables

- `CHROME_PATH` — Path to Chrome/Chromium executable
- `AGILQUEST_ASSET_ID` — Default workspace asset ID (optional)
