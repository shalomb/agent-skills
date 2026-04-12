---
name: commit
description: Use this skill to structure and format Git commits. Trigger this whenever you are about to make a commit. This enforces the Atomic Commit Protocol (ACP), ensuring commits are self-contained, tested, documented, and conform to Conventional Commits format.
---

# Commit — Atomic Commit Protocol (ACP)

You must adhere to the Atomic Commit Protocol (ACP) before making any git commit. The ACP guarantees that every commit is a complete, self-contained, and logically indivisible unit of work.

## Core ACP Composition Rules

An Atomic Commit MUST contain the following elements. Do not commit until all conditions are met:

1. **One Logical Change:** Do NOT mix functional changes with refactoring or formatting. Split unrelated changes into separate commits.
2. **Implementation & Verification:** 
   - You MUST include TDD tests that validate the implementation. At least one test MUST have failed prior to the implementation and pass afterward.
   - Run the test suite and confirm it passes. **Never commit broken code.**
3. **Documentation:** You MUST include updates to end-user documentation or inline code comments that reflect the change and explain non-obvious logic.
4. **Cleanliness:** You MUST remove all temporary files, build artifacts, debug statements (`console.log`, `print`), and leftover comments before committing.
5. **Intentional Staging:** Use `git add <files>` for specific paths. **Do NOT use `git add .`** blindly.

For the full formal specification, including rationale and TDD mapping, read: **[references/acp-spec.md](references/acp-spec.md)**

## Commit Message Format

```
<type>(<scope>): <Summary starting with Capital letter>

<Body explaining the "why", wrapped at 72 chars>

<Impact and Testing evidence>
```

### 1. The Header (Subject Line)
- **Type (Required):** `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `perf`, `style`, `ci`
- **Scope (Optional):** Short noun for the affected area (e.g., `auth`, `api`)
- **Summary (Required):** 
  - MUST be 50 characters or less.
  - MUST be in the **imperative mood** (e.g., "Add feature", not "Added feature").
  - SHOULD be **Capitalized**.
  - MUST NOT end with a period.

### 2. The Body
- MUST be separated from the header by a single blank line.
- MUST explain the reasoning and context behind the change (the "why"), rather than just repeating what the code does.
- SHOULD wrap lines at 72 characters.
- SHOULD include an `Impact:` section and a `Testing:` section detailing how the code was verified (see Appendix B in the spec for an example).

## What NOT to Do

- Do NOT add `Signed-off-by` or sign-off footers unless explicitly requested.
- Do NOT include breaking-change markers or BREAKING CHANGE footers unless explicitly requested.
- Do NOT push — only commit. The user decides when to push.

## Steps Before Committing

1. **Review Diff:** Run `git diff --cached` to catch accidental debug lines or unrelated changes.
2. **Verify Tests:** Run tests (e.g., `make test`, `pytest`, `npm test`) and ensure the GREEN state.
3. **Match Conventions:** Run `git log -n 5 --pretty=format:%s` to match existing project style.
4. **Draft Message:** Ensure it follows the ACP format and explains the "why".
5. **Commit:** Execute the commit. If the change spans multiple logical units, make separate, sequential atomic commits.