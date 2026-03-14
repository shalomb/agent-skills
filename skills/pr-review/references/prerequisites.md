# Prerequisites & Environment Setup

## Quick Check

Run the prerequisite checker to verify your environment:

```bash
cd ~/shalomb/agent-skills/skills/pr-review
python3 scripts/check_prerequisites.py
```

This will validate all dependencies and provide installation commands for missing prerequisites.

---

## Critical Prerequisites

### 1. Python 3.6+

**Status**: Usually already installed  
**Why needed**: All scripts are written in Python  
**Check**:
```bash
python3 --version
```

**If missing**: Install from https://www.python.org/

### 2. Git

**Status**: Usually already installed  
**Why needed**: Repository cloning and branch operations  
**Check**:
```bash
git --version
```

**If missing**:
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Or: https://git-scm.com/download
```

### 3. GitHub CLI (gh)

**Status**: Needs to be installed  
**Why needed**: Interact with GitHub API, fetch PR details, post comments  
**Check**:
```bash
gh --version
```

**Install**:
```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt-get install gh

# Or: https://cli.github.com/
```

**Authenticate**:
```bash
gh auth login
# Follow prompts to authenticate with GitHub
# Required scopes: repo, workflow, gist, project, read:org
```

**Verify authentication**:
```bash
gh auth status
# Should show: "Logged in to github.com as <username>"
```

### 4. gh pr-review Extension

**Status**: Must be installed explicitly  
**Why needed**: Post inline comments on pull requests  
**Repository**: https://github.com/agynio/gh-pr-review  
**Blog**: https://agyn.io/blog/gh-pr-review-cli-agent-workflows  

**Install**:
```bash
gh extension install agynio/gh-pr-review
```

**Verify**:
```bash
gh extension list
# Should show: agynio/gh-pr-review

gh pr-review --help
# Should display help text
```

**What it does**:
- Allows posting inline comments on PR lines
- Supports batch commenting
- Part of the GitHub CLI extension ecosystem

---

## Optional (But Recommended)

### uv - Python Runner

**Status**: Optional, but recommended  
**Why useful**: Faster Python script execution, better package management  
**Check**:
```bash
uv --version
```

**Install**:
```bash
# Official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or: brew install uv
# Or: pipx install uv
# Or: https://github.com/astral-sh/uv
```

**Benefits**:
- Faster script startup (< 100ms vs ~500ms for python3)
- Better dependency management
- Works with the provided `scripts/run_script.sh` wrapper
- Enables future use of Python tool management

**How pr-review uses it**:
```bash
# Automatic fallback
./scripts/run_script.sh parse_pr_url.py "https://..."
# → Uses uv if available, falls back to python3
```

---

## System Requirements Summary

```
✅ Critical (must have):
   - Python 3.6+
   - Git 2.0+
   - GitHub CLI (gh) 2.0+
   - gh pr-review extension
   - Internet access (for GitHub API)

⚠️ Required for specific features:
   - Test framework binaries (pytest, go, cargo, npm, terraform)
     → Only needed if running tests in analyzed repos

📦 Optional (recommended):
   - uv (Python runner)
     → Faster execution, better tool management
```

---

## Authentication & Access

### GitHub CLI Authentication

```bash
# Login (interactive)
gh auth login

# Check status
gh auth status

# Refresh token
gh auth refresh

# Logout
gh auth logout
```

**Required scopes**:
- `repo` — Read/write repository access
- `workflow` — GitHub Actions access
- `gist` — Gist access
- `project` — Project access
- `read:org` — Organization read access

**Verify scopes**:
```bash
gh api user -q '.scopes'
```

### Repository Access

The skill needs read/write access to repositories to post comments.

**Check access to a specific repo**:
```bash
gh repo view owner/repo
# Should show repository details without error
```

**If access denied**:
1. Verify you have write access to the repository
2. Verify your GitHub token has appropriate scopes
3. Check repository permissions: Visit repo → Settings → Collaborators

---

## Testing Your Setup

### Test 1: Prerequisite Checker

```bash
cd ~/shalomb/agent-skills/skills/pr-review
python3 scripts/check_prerequisites.py --verbose
```

**Expected output**: All checks pass (except gh pr-review extension if not installed yet)

### Test 2: Parse a PR URL

```bash
cd ~/shalomb/agent-skills/skills/pr-review

# Using run_script.sh (automatically uses uv if available)
./scripts/run_script.sh parse_pr_url.py \
  "https://github.com/oneTakeda/terraform-aws-MSKServerless/pull/33"

# Or directly with python3
python3 scripts/parse_pr_url.py \
  "https://github.com/oneTakeda/terraform-aws-MSKServerless/pull/33"
```

**Expected output**:
```json
{
  "owner": "oneTakeda",
  "repo": "terraform-aws-MSKServerless",
  "pr_number": 33,
  "url": "https://github.com/oneTakeda/terraform-aws-MSKServerless/pull/33"
}
```

### Test 3: Check GitHub API Access

```bash
gh api user -q '.login'
# Should print your username
```

### Test 4: List gh Extensions

```bash
gh extension list
# Should include: agynio/gh-pr-review (after installing)
```

### Test 5: Test PR Review on Real PR

```bash
cd ~/shalomb/agent-skills/skills/pr-review

# Clone and checkout a real PR
./scripts/run_script.sh clone_and_checkout.py owner repo 123

# Check for linked issues
./scripts/run_script.sh check_linked_issue.py owner repo 123 \
  --repo-dir ~/owner/repo
```

---

## Troubleshooting

### "gh: command not found"

**Cause**: GitHub CLI not installed  
**Solution**:
```bash
brew install gh
# Or follow: https://cli.github.com/
```

### "gh auth status" shows "not authenticated"

**Cause**: Not logged in to GitHub  
**Solution**:
```bash
gh auth login
# Follow interactive prompts
```

### "gh pr-review: command not found"

**Cause**: Extension not installed  
**Solution**:
```bash
gh extension install agynio/gh-pr-review
```

**Verify**:
```bash
gh extension list  # Should list pr-review
gh pr-review --help  # Should show help
```

### "Permission denied" when posting comments

**Cause**: Insufficient repository access  
**Solutions**:
1. Check repo access: `gh repo view owner/repo`
2. Check token scopes: `gh api user -q '.scopes'`
3. Refresh token: `gh auth refresh`
4. Request write access to the repository

### "Python 3.6+" not found

**Cause**: Only Python 2 or old Python 3 available  
**Solution**:
```bash
# Check what's available
python3 --version
python --version

# Install if needed
brew install python@3.12
# Or: https://www.python.org/
```

### Scripts run slowly

**Cause**: Python startup overhead  
**Solution**: Install uv for faster execution
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Now scripts use: ./scripts/run_script.sh <script>
```

---

## Advanced Setup

### Using uv with Virtual Environments

If you want to manage dependencies with uv:

```bash
cd ~/shalomb/agent-skills/skills/pr-review

# Create virtual environment
uv venv

# Activate
source .venv/bin/activate

# Install dependencies (if needed in future)
uv pip install <package>
```

### Using Docker

If you prefer containerized execution:

```dockerfile
FROM python:3.12-slim

# Install gh, git
RUN apt-get update && apt-get install -y git curl && \
    curl -sL https://github-cli.s3.amazonaws.com/linux_amd64_deb/gh_2.50.0_linux_amd64.deb && \
    dpkg -i gh_*.deb

# Install uv (optional)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy skill
COPY pr-review /app/pr-review
WORKDIR /app/pr-review

# Install gh pr-review extension
RUN gh extension install agynio/gh-pr-review

ENTRYPOINT ["python3", "scripts/check_prerequisites.py"]
```

### CI/CD Integration

For CI/CD pipelines, ensure prerequisites are installed in your CI environment:

```yaml
# GitHub Actions Example
- name: Setup pr-review prerequisites
  run: |
    # Install gh (may already be available)
    if ! command -v gh &> /dev/null; then
      brew install gh
    fi
    
    # Install gh pr-review extension
    gh extension install agynio/gh-pr-review
    
    # Verify
    python3 scripts/check_prerequisites.py

- name: Run pr-review
  run: |
    cd ~/shalomb/agent-skills/skills/pr-review
    ./scripts/run_script.sh parse_pr_url.py "${{ github.event.pull_request.html_url }}"
```

---

## Security Considerations

### GitHub Token Scope

The skill uses your GitHub token (via `gh` CLI). Ensure:
- Token has minimum required scopes (see above)
- Token is stored securely (gh CLI handles this)
- Token is not logged or exposed in output

**Never**:
- Commit `~/.config/gh/hosts.yml` to version control
- Log the full token value
- Share your authentication token

### Repository Access

The skill needs:
- **Read**: Clone repo, read issues, analyze code
- **Write**: Post comments on PRs

**Check access**:
```bash
gh repo view owner/repo --json name  # Read access
gh pr view owner/repo#123 --json body  # PR access
```

---

## Environment Variables

The skill respects these GitHub environment variables:

```bash
# GitHub host (for GitHub Enterprise)
GH_HOST=github.enterprise.com

# GitHub token (if not using gh auth)
GH_TOKEN=gho_xxxxx

# GitHub API endpoint (advanced)
GH_API_HOST=api.github.com
```

Most users don't need to set these; `gh auth login` handles it.

---

## Next Steps

After confirming all prerequisites:

1. ✅ Run prerequisite checker: `python3 scripts/check_prerequisites.py`
2. ✅ Test a script: `./scripts/run_script.sh parse_pr_url.py "https://..."`
3. ✅ Use the skill: Tell Claude to review a PR

See `../SKILL.md` for the full skill documentation.
