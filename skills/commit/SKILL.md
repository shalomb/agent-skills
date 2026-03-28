---
name: commit
description: "Read this skill before making git commits. Enforces Atomic Commit Protocol (ACP) with Conventional Commits format."
---

# Commit — Atomic Commit Protocol (ACP)

Read this skill before making any git commit. Every commit must be **atomic**
(one logical change), **verified** (tests pass), and **well-described**
(Conventional Commits format).

## Format

```
<type>(<scope>): <summary>

[optional body]
```

- **type** REQUIRED: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `perf`, `style`, `ci`
- **scope** OPTIONAL: short noun for the affected area (e.g., `api`, `tmux`, `auth`)
- **summary** REQUIRED: imperative, ≤72 chars, no trailing period

## ACP Rules

1. **One logical change per commit.** Don't mix a bugfix with a refactor.
   Split unrelated changes into separate commits.
2. **Verify before committing.** Run the test suite (or at minimum the
   relevant tests) and confirm they pass. Never commit broken code.
3. **Stage intentionally.** Only stage files that belong to this change.
   Use `git add -p` or explicit paths — not `git add .` blindly.
4. **Review the diff.** Run `git diff --cached` and read what you're
   committing. Catch accidental debug lines, leftover comments, unrelated
   changes.
5. **Body when needed.** If the "why" isn't obvious from the summary, add
   a body after a blank line. Keep it to short paragraphs or bullet points.

## What NOT to Do

- Do NOT add `Signed-off-by` or sign-off footers.
- Do NOT include breaking-change markers or BREAKING CHANGE footers.
- Do NOT push — only commit. The user decides when to push.
- Do NOT commit generated files, build artifacts, or secrets.
- Do NOT use `git add .` when only a subset of changes are related.

## Steps

1. **Understand the scope.** If the user provided file paths or globs,
   limit to those files. If freeform instructions, use them to guide
   scope and summary.
2. **Review changes.** Run `git status` and `git diff` to understand what
   changed. If staging specific files, `git diff -- <files>`.
3. **Match conventions.** Run `git log -n 30 --pretty=format:%s` to see
   the project's existing commit style and commonly used scopes.
4. **Ask if ambiguous.** If it's unclear which files belong together or
   what the logical boundary is, ask the user before committing.
5. **Stage.** `git add` only the intended files.
6. **Verify.** Run relevant tests if a test suite exists.
7. **Commit.** `git commit -m "<subject>"` (add `-m "<body>"` if needed).

## Multiple Commits

When changes span multiple logical units, make **separate commits** for each.
Order them so each commit leaves the codebase in a working state:

```bash
# Example: refactor + new feature
git add src/parser.rs
git commit -m "refactor(parser): extract token validation into helper"

git add src/parser.rs src/api.rs tests/test_api.rs
git commit -m "feat(api): add streaming response support"
```

## Commit Sizing Guide

| Good (atomic) | Bad (mixed) |
|---------------|-------------|
| One bugfix | Bugfix + unrelated formatting |
| One new function + its tests | Feature + refactor + docs update |
| Rename across codebase | Rename + behaviour change |
| Config change | Config + code + tests for different feature |
