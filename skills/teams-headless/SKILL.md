---
name: teams-headless
description: >
  Search and extract chat messages, meeting recaps, and transcripts from
  Microsoft Teams Web V2 using headless browser automation. Use when the user
  wants to read, find, or summarise Teams conversations or pull a meeting
  transcript without opening a browser. Requires one-time auth setup via
  setup_auth.py and Google Chrome installed locally.
---

# Teams Headless

Background Microsoft Teams Web V2 chat and transcript extraction using
Playwright and Google Chrome. Runs entirely headlessly without UI interference.

## Prerequisites

- Google Chrome installed (see path configuration below)
- `uv` package manager: `pip install uv` or `brew install uv`
- One-time auth setup completed (Step 0)

### Chrome path configuration

The scripts read `CHROME_PATH` from the environment, falling back to
platform defaults:

```bash
# Linux (common paths)
export CHROME_PATH="/usr/bin/google-chrome"
export CHROME_PATH="/usr/bin/chromium-browser"

# macOS
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

User data and downloads are stored under XDG-compliant directories:
- Browser session: `$XDG_STATE_HOME/agent-skills/teams-headless/user_data/`
  (default: `~/.local/state/`) — **not safe to delete** (breaks auth)
- Downloaded images: `$XDG_CACHE_HOME/agent-skills/teams-headless/downloads/`
  (default: `~/.cache/`) — safe to delete

## Step 0: Setup Auth (one-time)

Log in to establish a persistent browser session:

```bash
cd skills/teams-headless/scripts && uv run src/setup_auth.py
```

A Chrome window opens to `https://teams.microsoft.com/v2/`. Sign in manually,
then press Enter in the terminal. The session is saved and reused for all
future headless runs.

## Step 1: Extract

### Recent messages from a chat
```bash
cd skills/teams-headless/scripts

# Search for a chat by person or chat name, return recent messages
uv run src/teams_client.py "Suhasini"

# Control how many messages come back (default: 5)
uv run src/teams_client.py "Suhasini" --limit 20

# Omit the name to read the currently open chat
uv run src/teams_client.py
```

### Meeting recap and transcript
```bash
uv run src/teams_client.py "Call to Discuss AMI Creation" --recap
```

Opens the chat, clicks **View recap**, switches to the **Transcript** tab, and
returns the transcript segments. If no transcript is found, falls back to the
recap pane's text with author `"Recap Fallback"`.

## Step 2: Summarise

Output is a JSON array printed to stdout:

```json
[
  {
    "author": "Alice Smith",
    "body": "Message text...",
    "timestamp": null,
    "images": [
      { "alt": "diagram", "src": "https://...", "local_path": null }
    ]
  }
]
```

Parse the JSON and summarise or analyse the content for the user.

## Capabilities

| Action | Invocation |
|--------|-----------|
| Recent messages from named chat | `teams_client.py "Name"` |
| Recent messages from open chat | `teams_client.py` |
| Limit message count | `--limit N` (default 5) |
| Meeting recap / transcript | `--recap` (name required) |

## Notes

- Targets **Teams Web V2** (`teams.microsoft.com/v2/`) — selectors are tied to
  that UI and will need updating if Microsoft changes it.
- Uses CSS selectors and DOM interaction only — no mouse movement or
  screen automation.
- Session is persistent — re-run `setup_auth.py` only if the session expires.
- Chat selection and recap loading use fixed waits, so a run takes ~10-30s.
- Behaviour is specified in `features/chat_extraction.feature`.
