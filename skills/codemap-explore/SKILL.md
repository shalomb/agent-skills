---
name: codemap-explore
description: Systematic codebase exploration. Trigger this skill when you need to understand how a specific subsystem works, trace the downstream impact of a feature, find where a function is defined, or onboard to an entirely new area of the codebase.
---

# Systematic Codebase Exploration

## Start with the big picture

1. `codemap .` — project tree, file counts, top extensions
2. `codemap --deps .` — how packages and files connect
3. Hub files (from HUBS: section) — understand these first, they define shared types/interfaces

## Trace a feature

1. Find the entry point (CLI command, API route, event handler)
2. `codemap --importers <entry-file>` — what calls this?
3. `codemap --deps .` — follow the import chain downstream
4. Read hub files in the chain first

## Find what you're looking for

| Question | Command |
|---|---|
| Where is X defined? | `codemap --deps .` → scan the output |
| Who uses X? | `codemap --importers <file>` |
| What's the architecture? | `codemap --deps .` → look at hubs |
| What changed recently? | `codemap --diff` |
| What was I working on? | Check working set in `prompt-submit` hook output |

## Subsystems (if `.codemap/config.json` has routing)

Check `codemap config show` — routing subsystems define logical boundaries with associated docs and keywords. Read subsystem docs before tracing code.
