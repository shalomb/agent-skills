# PR-Review Skill: Setup & Usage

## What Was Created

The `pr-review` skill provides automated, objective-driven GitHub PR reviews.

### Structure

pr-review/
├── SKILL.md (9.4 KB)
│   ├─ Overview and core workflow
│   ├─ Prerequisites and setup
│   ├─ Execution strategy with examples
│   └─ Troubleshooting guide
│
├── scripts/ (6 Python scripts, 24.9 KB total)
│   ├─ parse_pr_url.py        - Extract PR metadata from URL
│   ├─ clone_and_checkout.py  - Clone repo & checkout branch
│   ├─ check_linked_issue.py  - Validate & fetch linked issues
│   ├─ find_review_agents.py  - Discover repo review standards
│   ├─ run_tests.py           - Auto-detect & run tests
│   └─ analyze_github_actions.py - Fetch workflow failures
│
└── references/ (3 guides, 14.4 KB total)
    ├─ workflow.md        - Complete PR review decision tree
    ├─ review-criteria.md - What's critical vs. non-blocking
    └─ gh-pr-review.md    - Integration with gh CLI extension

### Prerequisites

Before using this skill, install:

1. `gh` CLI (GitHub CLI)
   https://cli.github.com/
   
2. `gh pr-review` extension
   ```bash
   gh extension install agynio/gh-pr-review
   ```
   
3. Verify:
   ```bash
   gh auth status  # Should be authenticated
   gh pr-review --help  # Extension installed
   git --version  # Git available
   ```

## Quick Start

### Example: Review a PR

```bash
PR_URL="https://github.com/owner/repo/pull/123"

# The skill will:
# 1. Parse the URL
# 2. Clone/update the repo
# 3. Checkout the correct branch
# 4. Validate linked issue exists
# 5. Find & read any review standards in the repo
# 6. Analyze code diff
# 7. Run tests
# 8. Check GitHub Actions
# 9. Post inline comments for critical issues
# 10. Provide summary review
```

### Testing Individual Scripts

```bash
# Parse URL
python3 scripts/parse_pr_url.py "https://github.com/owner/repo/pull/123"

# Clone & checkout
python3 scripts/clone_and_checkout.py owner repo 123

# Check for linked issue
python3 scripts/check_linked_issue.py owner repo 123 --repo-dir ~/owner/repo

# Find review standards
python3 scripts/find_review_agents.py ~/owner/repo

# Run tests
python3 scripts/run_tests.py ~/owner/repo

# Analyze GitHub Actions
python3 scripts/analyze_github_actions.py owner repo 123
```

## Key Design Decisions

### 1. Objective-Driven Reviews
Every review is framed against the linked issue's objective. If the PR doesn't have a linked issue, that's flagged as a critical gap.

### 2. Repo-Defined Standards
The skill searches for and loads any review agents/standards defined in the repo (.github/agents/*.md, etc.). This lets teams encode their own review criteria.

### 3. Direct Comments, No Approval
Comments are posted directly via `gh pr-review`. This is suitable for async review workflows. The user always controls whether to merge.

### 4. Bias Toward Action
Non-critical improvements are flagged but don't block. We call out security issues, breaking changes, and objective misalignment—not style.

### 5. Deep-Dive Into Failures
When tests or workflows fail, the skill analyzes the error messages. This helps surface the root cause.

## What the Skill Does NOT Do

- Auto-merge PRs
- Auto-approve or explicitly approve PRs
- Modify code in the PR
- Create or update issues
- Require perfect test coverage
- Block on code style alone

## Customization

### Adding Language Support for Tests

Edit `scripts/run_tests.py`:
1. Add detection pattern to `detect_test_framework()`
2. Add command in `run_tests()` function
3. Test with a sample repo

### Adding Review Criteria

Edit `references/review-criteria.md` to add language-specific or domain-specific checklists.

### Custom Patterns for Finding Agents

Edit `scripts/find_review_agents.py` to search additional paths:
```python
patterns = [
    '.github/agents/*.md',
    'docs/review/*.md',  # Add custom path
]
```

## Integration Notes

This skill is designed to be called by Claude programmatically. The typical flow:

1. User provides PR URL
2. Claude triggers the `pr-review` skill
3. Skill executes scripts sequentially
4. Results inform Claude's review
5. Claude posts comments via `gh pr-review`
6. Claude summarizes findings

## Troubleshooting

**Error: gh pr-review not found**
→ `gh extension install agynio/gh-pr-review`

**Error: permission denied**
→ `gh auth login` and verify repo access

**Scripts won't run**
→ `chmod +x scripts/*.py` and check Python 3 is available

**Tests not detected**
→ The repo may not have automated tests. Continue with code review.

**Can't post comments**
→ Verify: `gh repo view owner/repo` shows you have write access

---

Version: 1.0
Created: 2026-03-14
