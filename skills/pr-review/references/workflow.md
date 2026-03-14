# PR Review Workflow

## Overview

The PR review process follows a systematic approach to evaluate code quality, consistency with project objectives, and test coverage.

## Core Workflow

### 1. Parse and Setup
- **Input**: GitHub PR URL (e.g., `https://github.com/owner/repo/pull/123`)
- **Output**: Cloned repo at `~/{owner}/{repo}/`, checked out to the correct branch
- Use `scripts/parse_pr_url.py` to extract owner, repo, PR number
- Use `scripts/clone_and_checkout.py` to clone and checkout the PR branch (not `pr-xx`, but the actual feature branch)

### 2. Validate Issue Link
- **Requirement**: Every PR should have a linked GitHub issue or Jira ticket
- Use `scripts/check_linked_issue.py` to:
  - Fetch linked issues from the PR
  - Extract Jira references from PR body
  - Return both GitHub issue links and Jira keys
- **If no linked issue**: 🚨 Call this out as a critical gap in the review

### 3. Understand the Objective
- **Input**: Linked issue(s)
- **Output**: Clear understanding of what this PR is supposed to accomplish
- Fetch issue details (GitHub API or Jira API)
- Read and synthesize the objective
- Note any acceptance criteria or requirements
- This becomes the **lens** through which all code is evaluated

### 4. Discover Review Standards
- Use `scripts/find_review_agents.py` to search the repo for:
  - `.github/agents/*.md`
  - `.claude/agents/*.md`
  - `.agents/*.md`
  - `AGENTS.md` or `CLAUDE.md` in root
- **Load and read** any found agent/skill files
- These contain team-specific review criteria, coding standards, or architectural patterns
- **This is optional but valuable**: Teams that document standards should have those standards applied

### 5. Analyze the Code Changes
- **Get the diff**:
  ```bash
  git diff origin/main..HEAD --stat  # overview
  git diff origin/main..HEAD         # detailed diff
  ```
- **Understand what's changing**: 
  - Files modified, added, removed
  - Lines of code affected
  - Complexity and risk of changes
- **Review against the objective** from step 3
  - Does the code accomplish the stated goal?
  - Does it introduce unnecessary changes?
  - Are there missing pieces or loose ends?

### 6. Evaluate Code Quality
- **Apply review criteria** from `references/review-criteria.md`
- **Check for critical issues**:
  - Security vulnerabilities (hardcoded secrets, SQL injection, etc.)
  - Breaking changes without documentation
  - Missing error handling
  - Performance regressions
  - Architectural violations (if standards exist from step 4)
- **Note improvements** (not failures, but optional enhancements)
- **Bias toward action**: Not every code smell is a blocker

### 7. Run Tests
- Use `scripts/run_tests.py` to auto-detect and run tests
- Capture test output, failures, and error messages
- **Analyze failures** in context of the PR changes
  - Are failures in code the PR touched?
  - Are they new failures or pre-existing?
  - Can they be fixed easily or are they indicative of larger issues?

### 8. Analyze GitHub Actions
- Use `scripts/analyze_github_actions.py` to fetch recent workflow runs
- Identify failed runs on the PR branch
- **Deep dive into failures**:
  - Read error logs and stack traces
  - Correlate failures with code changes
  - Identify if failures are due to the PR or environmental issues

### 9. Post Comments and Summary
- **Inline comments**: Use `gh pr review` CLI to post specific comments on lines of code
  - Trigger: When there's a critical issue on a specific line
  - Format: Be concise, reference the objective, suggest solutions
  - Example: "This breaks the authorization pattern. See issue #123 for context."
- **Summary comment**: Post a summary review with:
  - ✅ What works well
  - ⚠️ Critical issues (blockers)
  - 💡 Suggestions (non-blocking improvements)
  - 📋 Checks performed (tests, Actions, standards)

## Decision Tree

```
Start: PR URL provided
│
├─ Parse URL → Extract owner/repo/PR#
│
├─ Clone/checkout → Repo ready
│
├─ Linked issue?
│  ├─ NO → 🚨 FLAG: No linked issue
│  └─ YES → Fetch objective
│
├─ Repo has review agents?
│  ├─ YES → Load and read standards
│  └─ NO → Skip to general criteria
│
├─ Analyze diff against objective
│  ├─ Accomplishes goal? 
│  ├─ Unnecessary changes?
│  └─ Missing pieces?
│
├─ Check for critical issues
│  ├─ Security issues? → FLAG
│  ├─ Breaking changes? → FLAG
│  ├─ Major architecture violation? → FLAG
│  └─ Continue
│
├─ Run tests
│  ├─ Tests fail? → Analyze why
│  └─ Tests pass? → Continue
│
├─ Analyze GitHub Actions
│  ├─ Recent failures? → Investigate
│  └─ No failures? → Continue
│
└─ Post comments and summary
   ├─ Inline comments for critical issues
   └─ Summary with findings
```

## Quality Criteria Reference

See `references/review-criteria.md` for:
- What constitutes a "critical" issue
- Code quality standards
- Security review checklist
- Architecture and pattern guidelines
