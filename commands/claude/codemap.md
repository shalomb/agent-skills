---
description: Map codebase architecture, dependency flow, hub files, and blast radius
---

You are tasked with: Map codebase architecture, dependency flow, hub files, and blast radius.

Follow the instructions in the `codemap` skill:
1. Analyze project structure using `codemap .` and dependency flow via `codemap --deps .`.
2. Identify architectural hub files and calculate blast radius using `codemap --importers <file>` before modifying shared code.
3. Generate or inspect cross-agent handoff context envelopes via `codemap handoff .`.

User request:
$ARGUMENTS
