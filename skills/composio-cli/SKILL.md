---
name: composio-cli
description: Use the Composio CLI (`composio`) to find and run tools on external apps (GitHub, Gmail, Slack, Google Sheets, Calendar, etc.) through the user's connected accounts. Use when the user asks to act on a third-party SaaS app, send an email/message, create an issue, or mentions Composio, toolkits, or connected accounts. Triggers on 'composio', 'connect my gmail', 'link slack', 'execute tool'.
---

# Composio CLI

Binary: `~/.composio/composio` (symlink `~/.local/bin/composio`). Ensure `~/.local/bin` is on PATH.
Logged-in account is shared across shells. Check with `composio whoami`.

## Workflow: search → link → inspect → execute

1. **Find a tool** (JSON by default; `--human` for readable):
   `composio search "send an email" --toolkits gmail --limit 5`
2. **Connect the account** if missing (OAuth; needs the user to open a URL):
   `composio link gmail --no-browser` (add `--alias work` for a second account;
   `--list` to show existing). Show the URL to the user, then wait for them.
3. **Inspect inputs** before calling:
   `composio execute GMAIL_SEND_EMAIL --get-schema`
4. **Preview, then run**:
   `composio execute SLACK_SEND_MESSAGE --dry-run -d '{ channel: "general", markdown_text: "Hi" }'`
   then drop `--dry-run`.

`execute` validates inputs and the connection itself; its error messages say what to fix.

## Useful flags / commands

- `-d` takes JSON, `@file`, or `-` (stdin). `--account <alias|id>` picks among multiple accounts.
- `--parallel` runs repeated slug/data groups concurrently. `--file PATH` uploads a file.
- `composio connections list` shows connected accounts; `composio whoami`, `composio orgs`.
- `composio run '<ts/js>'` runs inline code with Composio helpers.
- `composio proxy` gives curl-like raw API access through a connected account.

## Safety

- **Side-effecting tools (send, create, delete, post) act as the user.** Always `--dry-run`
  and confirm with the user before executing, unless they explicitly authorised it.
- Never print or store OAuth/login keys (`cliKey` URLs are one-time login links; relay only to the user).
- Do NOT use `composio login --agent` when a human is present; use `composio login` then `composio login --poll`.
- Do not run `composio setup` (installs unpinned Claude/Codex plugins) unless asked.
- Upgrade: `composio upgrade [version]`. Docs: https://docs.composio.dev
