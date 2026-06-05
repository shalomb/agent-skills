---
name: codemap-hub-safety
description: Strict safety protocol for modifying hub files. Trigger this skill immediately when you discover a file is imported by 3 or more other files, when the codemap hook surfaces 'hub-safety', or when making structural changes to core architecture files.
---

# Hub Safety Protocol

Hub files are imported by 3+ other files. Changes ripple across the codebase.

## Before editing

1. `codemap --importers <file>` — see all dependents and blast radius
2. Understand the public API surface: which functions/types are used externally
3. Confirm tests exist for dependents, not just the hub itself

## While editing

- Prefer additive changes over breaking changes
- If renaming or removing a public symbol, update all importers in the same commit
- If changing a function signature, check every call site

## After editing

- Run the full test suite, not just the hub's own tests
- `codemap --deps .` — verify the dependency graph is intact
- If 8+ importers, consider staged rollout: change hub → test → update callers separately

## Risk escalation

| Importers | Risk | Action |
|---|---|---|
| 3–5 | Medium | Package tests + direct importer tests |
| 6–10 | High | Full test suite, review all importers |
| 10+ | Critical | Consider splitting the hub or introducing an interface |
