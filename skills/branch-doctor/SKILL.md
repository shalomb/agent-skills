---
name: branch-doctor
description: >
  Comprehensive health check for the current git branch. Diagnoses working tree
  cleanliness, validates git history against Conventional Commits, executes local
  tests, checks GitHub Actions CI runs, and audits Pull Request well-formedness
  against PR templates and issue linking standards. Triggers on: 'doctor',
  'branch health', 'check branch', 'pre-flight check', 'PR health check'.
---

# Branch Doctor: Git, Test, CI & PR Health Check

Run a comprehensive diagnostic health check of the current branch before opening a PR, requesting review, or merging.

---

## The 5-Point Health Check

When invoked, execute the diagnostic script or perform the 5 checks:

```bash
uv run {SKILLS_DIR}/branch-doctor/scripts/doctor.py
```

### 1. Working Tree Health
- Inspect `git status --porcelain` and `git diff --stat`.
- Verify whether there are unstaged changes, untracked debris, or unresolved merge conflicts.
- Ensure only intentional files are modified.

### 2. Git History & Conventional Commits Sanity
- Check all commits on the branch since branching from base (`git log origin/main..HEAD --oneline`).
- Validate that every commit message strictly adheres to the Conventional Commits format:
  ```
  <type>(<optional scope>): <imperative subject>
  ```
- Reject WIP commits (`wip`, `temp`, `fixup!`, `squash!`, bare merge commits).
- Confirm commits adhere to the Atomic Commit Protocol (ACP): complete, self-contained units with corresponding tests.

### 3. Local Test Ladder Execution
- Detect the project's local test runner in this order of precedence:
  - `justfile` $\rightarrow$ `just test` (or `just fast-fail`)
  - `Makefile` $\rightarrow$ `make test`
  - `pyproject.toml` / `uv.lock` $\rightarrow$ `uv run pytest`
  - `Cargo.toml` $\rightarrow$ `cargo test`
  - `package.json` $\rightarrow$ `npm test`
  - `go.mod` $\rightarrow$ `go test ./...`
- Execute the test suite, confirm exit code is 0, and note the test count and duration.

### 4. GitHub Actions CI Status
- Check the status of remote GitHub Actions workflows for the current branch:
  ```bash
  gh run list --branch "$(git rev-parse --abbrev-ref HEAD)" --limit 3 --json databaseId,name,status,conclusion,url
  ```
- Check for any `failure`, `startup_failure` (permissions blocks), or ongoing runs.

### 5. Pull Request Well-Formedness
- Check whether an open PR exists for the branch:
  ```bash
  gh pr view --json number,title,body,state,mergeable,reviewDecision,url
  ```
- If PR exists, audit against quality gates:
  - **Title:** Must follow Conventional Commits (`feat(auth): add OAuth2 provider`).
  - **Body Content:** Must not be blank; must detail *what*, *why*, and verification proof.
  - **Issue References:** Must link related tickets or issues (`Fixes #123`, `Resolves #456`, or Jira ticket keys).
  - **Template Conformance:** Check against `.github/PULL_REQUEST_TEMPLATE.md` (or `.github/pull_request_template.md`). Verify sections are completed without unedited template placeholders.
  - **Mergeability:** Confirm no merge conflicts (`mergeable: MERGEABLE`).
- If PR does NOT exist:
  - Provide a ready-to-use PR title and summary generated from the branch commits.

---

## Output Format

```markdown
# 🏥 Branch Doctor Report

- **Branch:** `feat/auth-token-validation` (base: `origin/main`)
- **Overall Status:** ✅ HEALTHY / ⚠️ WARNINGS / ❌ UNHEALTHY

## Diagnostic Checks

| Check | Status | Details |
|---|---|---|
| **Working Tree** | ✅ Clean | 0 unstaged, 0 untracked |
| **Commit History** | ✅ Sane | 3 commits, all valid Conventional Commits |
| **Local Tests** | ✅ Passing | 42 passed in 1.4s via `make test` |
| **GitHub CI** | ✅ Passing | All 3 workflow runs successful |
| **Pull Request** | ⚠️ Attention | PR #104 missing linked issue reference |

## Findings & Action Items
1. **Pull Request:** Add `Fixes #<issue>` to PR description before requesting review.
```
