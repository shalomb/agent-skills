---
name: codemap-refactor
description: Safe refactoring with dependency awareness. Use when restructuring, renaming, moving, extracting, or consolidating code — especially when hub files are in scope.
---

# Safe Refactoring with Code Intelligence

## Before refactoring

1. `codemap --deps .` — understand the full dependency graph
2. Identify hub files in scope — they need extra care
3. `codemap --diff` — see what's already changed on this branch

## Checklist

- [ ] All tests pass before starting
- [ ] Hub files identified, dependents listed
- [ ] Public API changes planned (additive preferred)
- [ ] Import paths updated if moving files
- [ ] No circular dependencies introduced

## Safe rename pattern

1. Add the new name alongside the old (alias or wrapper)
2. Update all callers to use the new name
3. Remove the old name
4. Full test suite

## Safe move pattern

1. Create new file with the same public API
2. Re-export from old location temporarily
3. Update all importers to use the new path
4. Remove old file and re-export

## After refactoring

- `codemap --deps .` — verify the graph is clean
- `codemap --importers <moved-file>` — confirm nothing is broken
- Full test suite must pass
