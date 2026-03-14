---
name: pr-review
description: Comprehensive GitHub PR review automation that analyzes code changes, evaluates quality, identifies security issues, and posts inline comments. Use when given a GitHub PR URL and asked to review, analyze, or assess pull request quality.
compatibility: "Requires gh CLI with pr-review extension installed (gh extension install agynio/gh-pr-review), git, and appropriate repository access."
---

# PR Review

## Overview

This skill enables comprehensive, objective-driven PR reviews. Given a GitHub PR URL, it:

1. Clones/checks out the repository to the correct branch
2. Validates the PR has linked issues (GitHub or Jira) for context
3. Reads the linked issue to understand the PR's objective
4. Discovers any review standards or agents defined in the repository
5. Analyzes code changes against the objective and standards
6. Runs tests and analyzes GitHub Actions for failures
7. Posts inline comments on critical issues
8. Provides a structured summary

**Key principle**: Reviews are objective-driven. Every critical issue is framed against the stated goal from the linked issue, and suggestions are non-blocking (we bias toward shipping).

## Prerequisites

**Quick Check**: Run the prerequisite checker to verify your environment is ready:

```bash
python3 scripts/check_prerequisites.py
```

This validates:
- ✅ Python 3.6+
- ✅ Git 2.0+
- ✅ GitHub CLI (gh) with authentication
- ✅ gh pr-review extension
- ✅ Standard Python library modules
- ✅ Optional: uv (Python runner for faster execution)
- ✅ GitHub API access

**Manual Prerequisites**:
- `gh` CLI installed and authenticated: `gh auth status`
- `gh pr-review` extension: `gh extension install agynio/gh-pr-review`
- Git: `git --version`
- Python 3.6+: `python3 --version`
- Read/write access to target repositories

**Recommended (optional but faster)**:
- `uv` (Python runner): https://docs.astral.sh/uv/ — Enables 10x faster script startup

For detailed setup instructions, see `references/prerequisites.md`.

## PR Review Workflow

See `references/workflow.md` for the complete decision tree and multi-step process.

**Summary:**

1. **Parse PR URL** → Extract owner, repo, PR number
2. **Clone & checkout** → Repository ready at `~/{owner}/{repo}/`
3. **Validate issue link** → 🚨 Flag if missing
4. **Understand objective** → Read linked GitHub issue or Jira ticket
5. **Discover standards** → Find `.github/agents/*.md`, `.claude/agents/*.md`, etc.
6. **Analyze code** → Diff against objective
7. **Check for critical issues** → Security, breaking changes, architectural violations
8. **Run tests** → Capture failures and errors
9. **Analyze GitHub Actions** → Deep-dive into workflow failures
10. **Post comments** → Inline comments for critical issues + summary

## Key Scripts

All scripts output JSON for easy parsing. They handle error cases gracefully.

**Running scripts**: Use `./scripts/run_script.sh` wrapper (automatically uses `uv` if available, falls back to `python3`):

```bash
./scripts/run_script.sh <script_name> [args...]
```

Or run directly with `python3`:

```bash
python3 scripts/<script_name> [args...]
```

### check_prerequisites.py
Validates all prerequisites are installed and configured correctly.
```bash
./scripts/run_script.sh check_prerequisites.py
# Or: python3 scripts/check_prerequisites.py --verbose
# Output: JSON with status of all checks
# Exit code: 0 if ready, 1 if missing prerequisites
```

### parse_pr_url.py
Extracts owner, repo, and PR number from a GitHub PR URL.
```bash
./scripts/run_script.sh parse_pr_url.py "https://github.com/owner/repo/pull/123"
# Output: {"owner": "owner", "repo": "repo", "pr_number": 123, "url": "..."}
```

### clone_and_checkout.py
Clones (or updates) the repository and checks out the PR's actual branch.
```bash
./scripts/run_script.sh clone_and_checkout.py owner repo 123
# Output: {"checkout_dir": "~/owner/repo", "branch_name": "feature-xyz", "commit_sha": "abc123..."}
```

### check_linked_issue.py
Validates and fetches linked GitHub issues and Jira keys from the PR.
```bash
./scripts/run_script.sh check_linked_issue.py owner repo 123 --repo-dir ~/owner/repo
# Output: {"linked_issues": [...], "has_linked_issues": true, "jira_issues": ["PROJ-123"], ...}
```

### find_review_agents.py
Searches the repository for review agents or standards in `.github/agents/*.md`, `.claude/agents/*.md`, etc.
```bash
./scripts/run_script.sh find_review_agents.py ~/owner/repo
# Output: {"found_agents": [{path, name, content_preview, ...}], "count": 2, ...}
```

### run_tests.py
Auto-detects test framework (pytest, go test, npm test, cargo, terraform test) and runs tests.
```bash
./scripts/run_script.sh run_tests.py ~/owner/repo
# Output: {"framework": "pytest", "status": "passed|failed", "exit_code": 0, "stdout": "...", ...}
```

### analyze_github_actions.py
Fetches recent GitHub Actions workflow runs for the PR branch and identifies failures.
```bash
./scripts/run_script.sh analyze_github_actions.py owner repo 123 --repo-dir ~/owner/repo
# Output: {"branch": "feature-xyz", "workflow_runs": [{number, status, jobs, ...}], ...}
```

## Code Review Standards

See `references/review-criteria.md` for:
- What constitutes a **critical** issue (vs. non-blocking suggestions)
- Security review checklist
- Architecture and design checklist
- Language-specific considerations (Terraform, Python, Go, TypeScript, SQL)
- Review bias: We favor shipping over perfection

## Inline Comments & CI/CD Integration

See `references/gh-pr-review.md` for:
- How to post inline comments using `gh pr-review` CLI
- Batch comment patterns
- Error handling and troubleshooting
- Integration with the review workflow

## Execution Strategy

When executing a PR review, follow this structure:

### Step 0: Verify Prerequisites
```bash
# Check all prerequisites before starting
./scripts/run_script.sh check_prerequisites.py

# Should show all checks passing (except gh pr-review if not installed)
# If not, follow the installation instructions
```

### Step 1: Setup
```bash
cd ~/shalomb/agent-skills/skills/pr-review

# Parse URL (using uv if available, else python3)
metadata=$(./scripts/run_script.sh parse_pr_url.py "$PR_URL")
owner=$(echo $metadata | jq -r .owner)
repo=$(echo $metadata | jq -r .repo)
pr_number=$(echo $metadata | jq -r .pr_number)

# Clone/checkout
checkout=$(./scripts/run_script.sh clone_and_checkout.py $owner $repo $pr_number)
repo_dir=$(echo $checkout | jq -r .checkout_dir)
branch=$(echo $checkout | jq -r .branch_name)
```

### Step 2: Issue & Standards
```bash
# Validate linked issue
issue_check=$(./scripts/run_script.sh check_linked_issue.py $owner $repo $pr_number --repo-dir $repo_dir)

# Find repo-defined review standards
agents=$(./scripts/run_script.sh find_review_agents.py $repo_dir)
# Load and read any found agents to understand review standards
```

### Step 3: Code Analysis
- Get the full diff: `git diff origin/main..HEAD`
- Analyze against the linked issue objective
- Identify critical issues using `references/review-criteria.md`

### Step 4: Testing & CI/CD
```bash
# Run tests
tests=$(./scripts/run_script.sh run_tests.py $repo_dir)

# Analyze GitHub Actions
actions=$(./scripts/run_script.sh analyze_github_actions.py $owner $repo $pr_number --repo-dir $repo_dir)
```

### Step 5: Post Comments
For each critical issue identified:
```bash
gh pr-review ${owner}/${repo}#${pr_number} \
  --comment "Issue description" \
  --file relative/path/to/file.go \
  --line 42
```

Then post a summary comment with overall findings.

## Practical Example

```bash
cd ~/shalomb/agent-skills/skills/pr-review
PR_URL="https://github.com/oneTakeda/terraform-aws-MSKServerless/pull/33"

# 0. Check prerequisites (first time only)
./scripts/run_script.sh check_prerequisites.py

# 1. Parse
./scripts/run_script.sh parse_pr_url.py "$PR_URL"
# → owner: oneTakeda, repo: terraform-aws-MSKServerless, pr_number: 33

# 2. Clone & checkout
./scripts/run_script.sh clone_and_checkout.py oneTakeda terraform-aws-MSKServerless 33
# → repo at ~/oneTakeda/terraform-aws-MSKServerless/, branch: 8-vpc-authorization-patterns

# 3. Check for linked issue
./scripts/run_script.sh check_linked_issue.py oneTakeda terraform-aws-MSKServerless 33 \
  --repo-dir ~/oneTakeda/terraform-aws-MSKServerless
# → If no linked issue: 🚨 FLAG

# 4. Find review agents (if any)
./scripts/run_script.sh find_review_agents.py ~/oneTakeda/terraform-aws-MSKServerless
# → Check .github/agents/, .claude/agents/, etc.

# 5. Analyze code diff manually
cd ~/oneTakeda/terraform-aws-MSKServerless
git diff origin/main..HEAD --stat
git diff origin/main..HEAD | head -200  # first 200 lines of diff

# 6. Run tests (with automatic framework detection)
cd ~/shalomb/agent-skills/skills/pr-review
./scripts/run_script.sh run_tests.py ~/oneTakeda/terraform-aws-MSKServerless

# 7. Check GitHub Actions
./scripts/run_script.sh analyze_github_actions.py oneTakeda terraform-aws-MSKServerless 33

# 8. Post inline comments for critical issues
gh pr-review oneTakeda/terraform-aws-MSKServerless#33 \
  --comment "Hardcoded secret detected. Move to environment variable." \
  --file variables.tf \
  --line 15

# 9. Post summary
gh pr-review oneTakeda/terraform-aws-MSKServerless#33 \
  --comment "## Summary
...findings..."
```

**Note**: All `./scripts/run_script.sh` calls automatically use `uv` if available, otherwise fall back to `python3`.

## Review Quality

The quality of a review depends on:

1. **Clarity of the objective** — Is the linked issue well-defined?
2. **Context of changes** — Does the diff make sense in isolation?
3. **Reproducibility** — Can you verify test failures?
4. **Actionability** — Are comments specific and solvable?

## Limitations & Notes

- **No line-level commenting on unmodified lines** — The `gh pr review` CLI can only comment on lines in the diff
- **Test execution depends on environment** — If tests require special setup (databases, keys, etc.), results may be incomplete
- **GitHub Actions deep-dive is async** — Workflow logs are read-only; fixing requires PR author's actions
- **Review agents are optional** — Not all repos document standards; default to `references/review-criteria.md`
- **Bias toward action** — We call out blockers, not style issues; we want code to ship

## Troubleshooting

### Quick Diagnosis

Always start with the prerequisite checker:

```bash
./scripts/run_script.sh check_prerequisites.py
```

This will identify most issues and provide installation commands.

### Common Issues

| Issue | Solution |
|-------|----------|
| **Prerequisites failing** | Run `./scripts/run_script.sh check_prerequisites.py` for detailed diagnosis |
| `gh: command not found` | Install GitHub CLI: `brew install gh` or https://cli.github.com/ |
| `gh auth` shows "not authenticated" | Run `gh auth login` and follow prompts |
| `gh pr-review` not found | Install extension: `gh extension install agynio/gh-pr-review` |
| `uv` not available (slow startup) | Optional but recommended: https://docs.astral.sh/uv/ |
| Git clone fails | Verify GitHub access and network |
| No linked issue | Add GitHub issue link to PR, then retry |
| Tests not detected | Repo may not have tests; continue with code review |
| Workflow analysis incomplete | Check if workflows have been run yet on this branch |
| Comments won't post | Verify write access: `gh repo view owner/repo` |

### Getting Help

1. Check `references/prerequisites.md` for detailed setup instructions
2. Run prerequisite checker: `./scripts/run_script.sh check_prerequisites.py --verbose`
3. See `references/gh-pr-review.md` for inline comment issues
