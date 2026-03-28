---
name: outlook-headless
description: >
  Search and extract emails from Outlook Web Access using headless browser
  automation. Use when the user wants to find, read, or summarise emails from
  Outlook without opening a browser — supports filtering by sender, recipient,
  subject, date range, and read status. Requires one-time auth setup via
  setup_auth.py and Google Chrome installed locally.
---

# Outlook Headless

Background Outlook Web Access email search and extraction using Playwright and
Google Chrome. Runs entirely headlessly without UI interference.

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

# Or set permanently in ~/.config/agent-skills/outlook-headless.env:
# CHROME_PATH=/usr/bin/google-chrome
```

User data and downloads are stored under XDG-compliant directories:
- Browser session: `$XDG_STATE_HOME/agent-skills/outlook-headless/user_data/`
  (default: `~/.local/state/`) — **not safe to delete** (breaks auth)
- Downloaded images: `$XDG_CACHE_HOME/agent-skills/outlook-headless/downloads/`
  (default: `~/.cache/`) — safe to delete

## Step 0: Setup Auth (one-time)

Log in to establish a persistent browser session:

```bash
cd skills/outlook-headless/scripts && uv run src/setup_auth.py
```

A Chrome window opens to `https://outlook.office.com/mail/`. Sign in manually.
The session is saved and reused for all future headless runs.

## Step 1: Search and Extract

### Basic search
```bash
cd skills/outlook-headless/scripts && uv run src/scanner.py "your search term"
```

### Advanced search (recommended)
```bash
# By sender and subject
uv run src/cli.py --from "boss@example.com" --subject "Urgent"

# With image download for visual analysis
uv run src/cli.py "Project" --download-images

# Date range
uv run src/cli.py --after "2024-01-01" --before "2024-01-31"

# Combined filters
uv run src/cli.py "Project" --from "alice@example.com" --unread --limit 10
```

## Step 2: Summarise

Output is a JSON array:
```json
[
  {
    "id": "0-0",
    "subject": "Example Subject",
    "sender": "sender@example.com",
    "body": "Email body text...",
    "timestamp": null
  }
]
```

Parse the JSON and summarise or analyse the content for the user.

## Capabilities

| Filter | Flag |
|--------|------|
| Subject keyword | `--subject "text"` |
| Sender | `--from "email@domain.com"` |
| Recipient | `--to "recipient@domain.com"` |
| After date | `--after YYYY-MM-DD` |
| Before date | `--before YYYY-MM-DD` |
| Unread only | `--unread` |
| Specific folder | `--folder "Deleted Items"` |
| Download images | `--download-images` |
| Show browser UI | `--show-ui` |

## Notes

- Does **not** use `pyautogui` or move the mouse — uses CSS selectors and DOM
  interaction only.
- Page stays invisible (`headless=True`) by default; use `--show-ui` to debug.
- Session is persistent — re-run `setup_auth.py` only if the session expires.
