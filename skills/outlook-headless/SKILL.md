---
name: outlook-headless
description: Background Outlook email search and extraction using Playwright and Google Chrome. Use this skill when you need to search for emails, extract email bodies or conversation threads, filter by sender, subject, or date, and handle Outlook tasks headlessly.
---

# /outlook-headless -- Deterministic Outlook Web Automation

Background Outlook email search and extraction using Playwright and Google Chrome. Runs entirely in the background without UI interference.

---

## Protocol

### Step 0: Setup Auth (One-time)

Before the first headless run, you must log in to establish a persistent session.

```bash
cd ~/.gemini/skills/outlook-headless/scripts && uv run src/setup_auth.py
```

### Step 1: Search and Extract Headlessly

Perform a search entirely in the background. Results are returned as JSON.

#### Basic Search
```bash
cd ~/.gemini/skills/outlook-headless/scripts && uv run src/scanner.py "GMSGQ EHS"
```

#### Advanced Search (Recommended)
Use `src/cli.py` for fine-grained control:

```bash
# Search by sender and subject
cd ~/.gemini/skills/outlook-headless/scripts && uv run src/cli.py --from "boss@example.com" --subject "Urgent"

# Download images for visual analysis
cd ~/.gemini/skills/outlook-headless/scripts && uv run src/cli.py "Project" --download-images

# Search within date range
cd ~/.gemini/skills/outlook-headless/scripts && uv run src/cli.py --after "2024-01-01" --before "2024-01-31"

# Combine everything
cd ~/.gemini/skills/outlook-headless/scripts && uv run src/cli.py "Project" --from "alice@example.com" --unread --limit 10
```

### Step 2: Summarize

The output is a JSON array of email objects:
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
Summarize the content for the user or perform further analysis.

---

## Capabilities

- **Find by Subject:** `--subject "Your Subject"`
- **Find by Sender:** `--from "email@domain.com"`
- **Find by Recipient:** `--to "recipient@domain.com"`
- **Date Filtering:** `--after YYYY-MM-DD`, `--before YYYY-MM-DD`
- **Status Filtering:** `--unread`
- **Extraction:** Automatically extracts bodies from conversation threads.

---

## Notes

- **Safety:** Does not use `pyautogui` or move the mouse. Uses CSS selectors and DOM interaction.
- **Determinism:** High. Uses direct navigation and specific search commitment logic.
- **Prerequisites:** Requires the official Google Chrome installed in `/Applications/Google Chrome.app`.
- **Background:** Page remains invisible (`headless=True`) during standard scans. Use `--show-ui` with `cli.py` to debug.

---

## Backlog / Future Ideas

- **Extended Headers:** Implement optional extraction of raw RFC822 internet headers (Message-ID, X-Headers, etc.) via the "View message details" modal for deeper technical analysis.
- **Attachment Metadata:** List attachment names and sizes without downloading.
- **Move/Recover Action:** Implement an action to move emails from "Deleted Items" back to "Inbox" or a specific folder.
