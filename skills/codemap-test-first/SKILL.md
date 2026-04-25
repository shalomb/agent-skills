---
name: codemap-test-first
description: TDD workflow with codemap impact analysis. Use when writing tests before implementation, especially when the file being tested is a hub or has many dependents.
---

# Test-First with Code Intelligence

## The cycle

1. **Write a failing test** for the behaviour you want
2. **Run it** — confirm it fails for the right reason
3. **Implement** the minimum to make it pass
4. **Run all tests** — not just the new one
5. **Check hub impact** — if you touched a hub, run importer tests too

## Using codemap for test planning

- `codemap --importers <file>` — which files depend on what you're testing?
- `codemap --deps .` — understand the dependency chain before writing mocks
- Working set (from `prompt-submit` hook) shows what you've already touched

## Testing hub files

Hub files affect many dependents. Test:
1. The hub's own tests
2. Direct importers' tests
3. Integration tests that cross the hub boundary

## Test file conventions

| Language | Convention |
|---|---|
| Go | `*_test.go` in same package |
| TypeScript | `*.test.ts` or `*.spec.ts` |
| Python | `test_*.py` or `*_test.py` |
| Rust | `#[cfg(test)]` module or `tests/` dir |
| Java | `*Test.java` in `src/test/` |
