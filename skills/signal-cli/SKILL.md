---
name: signal-cli
description: Send and receive Signal messages from the shell with signal-cli — ping Note to Self, message a number or a named group, list groups, pull pending messages, or run the JSON-RPC/SSE daemon. Use when the user wants to notify themselves or others over Signal, check for Signal replies, find a group ID, or wire Signal into an agent loop. Triggers on "signal", "signal-cli", "note to self", "ping me on signal", "send a signal message".
---

# signal-cli

Use `scripts/sig` for routine work; it resolves the account, validates arguments, and refuses unsafe combinations.

```bash
scripts/sig self "build done"            # Note to Self (use for pings/notifications)
scripts/sig send +15551234567 "hello"    # DM; recipient must be E.164
scripts/sig groups                       # name<TAB>base64-id
scripts/sig group "Team Chat" "hello"    # group by exact name
scripts/sig receive 5                    # pull pending messages for 5s (JSON lines)
SIG_DRY_RUN=1 scripts/sig self "x"       # print the signal-cli command only
```

Account: `SIGNAL_ACCOUNT=+NUMBER`, else the only registered account (`signal-cli listAccounts`). Data lives in `~/.local/share/signal-cli`.

## Rules
- Sending messages is outward-facing and irreversible. Confirm the recipient and text with the user first, except for explicit Note-to-Self pings they requested.
- Never put secrets in message bodies.
- `receive` is a one-shot pull and conflicts with a running daemon on the same account. `scripts/sig receive` aborts if a daemon is detected; check `pgrep -af 'org.asamk.signal.Main'` and any systemd unit.
- signal-cli keeps no readable message history. Received messages arrive once; persist anything needed.
- Timestamps returned by `send` mean the server accepted the message, not that a device displayed it.

## Raw CLI (when the wrapper is not enough)
`signal-cli -a ACCOUNT send -m TEXT RECIPIENT`, with `--note-to-self`, `-g GROUP_ID`, `--attachment FILE`, `--quote-timestamp`/`--quote-author`, `--mention`, `--message-from-stdin`.
Also: `sendReaction`, `sendReceipt --type read -t TIMESTAMP`, `sendTyping`, `remoteDelete`, `listContacts`, `listDevices`, `link`/`register` for account setup. Add `-o json` for machine-readable output. Run `signal-cli <command> --help` for flags.

## Daemon / event-driven use
For SSE streaming, JSON-RPC calls, or an agent that reacts to incoming messages, read [references/daemon.md](references/daemon.md).
