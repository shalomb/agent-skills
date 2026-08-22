# GitHub PR Review CLI Extension

## Overview

The `gh pr review` CLI extension is required to post inline comments on pull requests. This enables posting comments on specific lines of code with context.

**Repository**: https://github.com/agynio/gh-pr-review  
**Documentation**: https://agyn.io/blog/gh-pr-review-cli-agent-workflows

## Installation

```bash
gh extension install agynio/gh-pr-review
```

Verify installation:
```bash
gh pr-review --help
```

## Usage

### Basic Syntax

```bash
gh pr-review [flags] <owner/repo#PR_NUMBER>
```

### Posting a Comment on a Specific Line

```bash
gh pr-review <owner/repo>#<pr_number> \
  --comment "Your comment text" \
  --file <relative_file_path> \
  --line <line_number>
```

Example:
```bash
gh pr-review ORG/my-terraform-repo#33 \
  --comment "This hardcoded secret should be moved to a variable." \
  --file main.tf \
  --line 42
```

### Posting Multiple Comments

The extension supports batch comments. Construct a JSON or iterate:

```bash
# Single command, multiple lines in same file
gh pr-review <owner/repo>#<pr> \
  --comment "Issue 1" \
  --file module.tf \
  --line 10

gh pr-review <owner/repo>#<pr> \
  --comment "Issue 2" \
  --file module.tf \
  --line 25
```

### Reviewing the Entire PR (Summary)

For summary-level comments (not tied to a specific line):

```bash
gh pr-review <owner/repo>#<pr> \
  --comment "Overall PR summary and findings"
```

## Practical Patterns

### Check Prerequisites

Before posting comments, verify:
1. `gh` CLI is installed and authenticated
2. `gh pr-review` extension is installed
3. User has write/maintain access to the repository
4. The PR exists and is still open

```bash
gh extension list | grep pr-review
# Should output: agynio/gh-pr-review
```

### Post Critical Issues Only

Only post comments for issues identified in the review that are critical or require action:

```bash
# Example: Security issue
gh pr-review ORG/my-terraform-repo#33 \
  --comment "🚨 **Critical: Hardcoded secret detected.**\n\nMove to environment variable or AWS Secrets Manager.\n\nReference: CWE-798 (Hardcoded Credentials)" \
  --file variables.tf \
  --line 15
```

### Batch Comments via Script

If posting many comments, loop and batch:

```bash
#!/bin/bash
PR="$1"
REPO="ORG/my-terraform-repo"

# Array of line numbers and comments
declare -a ISSUES=(
  "10:Incorrect variable type"
  "25:Missing validation block"
  "42:Hardcoded secret"
)

for issue in "${ISSUES[@]}"; do
  LINE=${issue%%:*}
  COMMENT=${issue#*:}
  gh pr-review "${REPO}#${PR}" \
    --comment "$COMMENT" \
    --file main.tf \
    --line "$LINE"
done
```

### Summary Comment (Fallback)

If line-specific commenting fails or isn't needed, post a summary:

```bash
gh pr-review <owner/repo>#<pr> \
  --comment "
## Review Summary

### ✅ What Works Well
- Accomplishes the stated objective
- Tests are passing

### 🚨 Critical Issues
1. Line 42: Hardcoded secret
2. Line 25: Breaking change not documented

### Status
Blocked on secret removal. Once fixed, ready to merge.
"
```

## Error Handling

### Common Issues

**Extension not found**
```bash
gh extension install agynio/gh-pr-review
```

**Authentication failed**
```bash
gh auth login
# or
gh auth refresh
```

**PR not found or permission denied**
- Verify PR exists: `gh pr view <owner/repo>#<pr>`
- Verify repository access: `gh repo view <owner/repo>`

**Line number out of range**
- Ensure the line number exists in the current diff
- Check the file path is relative to repo root

## Integration with PR Review Workflow

In the `pr-review` skill, integrate this CLI as follows:

1. **Verify extension is installed** before attempting comments
2. **For each critical issue found**, post an inline comment:
   ```python
   # Pseudo-code
   for issue in critical_issues:
       gh pr-review {repo}#{pr} \
           --comment issue.description \
           --file issue.file \
           --line issue.line_number
   ```
3. **Post summary comment** with overall findings
4. **Report status** to the user (comments posted, count, etc.)

## Limitations

- Comments are posted as the authenticated user
- Cannot post on lines not in the diff (non-changed lines)
- Cannot modify or delete comments programmatically (use GitHub UI)
- Batch posting is manual (iterate via script)
