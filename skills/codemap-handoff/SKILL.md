---
name: codemap-handoff
description: Build and consume cross-agent handoff artifacts with codemap. Use when switching between AI agents (Claude, Codex, Cursor, pi), resuming work after a break, or when context window is getting full and work needs to continue in a fresh session.
---

# Multi-Agent Handoff

## Building a handoff

```bash
codemap handoff .               # Build + save full artifact
codemap handoff --prefix .      # Stable context only (hubs, file count)
codemap handoff --delta .       # Recent work only (changed files, risk, events)
codemap handoff --json .        # Machine-readable for other tools
```

## Reading a handoff

```bash
codemap handoff --latest .      # Read most recent saved artifact
codemap handoff --detail <file> . # Full context for one changed file
```

## What's in a handoff

- **Prefix** (stable): file count, hub summaries — cache-friendly, changes rarely
- **Delta** (dynamic): changed files, risk files, recent events, next steps
- **Hashes**: deterministic — validates cache reuse across agent sessions

## Artifacts written

| File | Content |
|---|---|
| `.codemap/handoff.latest.json` | Full artifact |
| `.codemap/handoff.prefix.json` | Stable prefix snapshot |
| `.codemap/handoff.delta.json` | Dynamic delta snapshot |
| `.codemap/handoff.metrics.log` | Append-only metrics stream |

## When to handoff

- Switching from one agent CLI to another
- Starting a fresh session on the same branch
- Context window filling up — compact and resume
- Passing work to another developer's AI session
