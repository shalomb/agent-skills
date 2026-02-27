# GitHub Copilot CLI Skill

Execute GitHub Copilot CLI commands programmatically for code generation, analysis, and automation tasks.

## Triggers

Use this skill when:
- User mentions "copilot", "gh copilot", or "copilot cli"
- User wants AI-powered code generation, analysis, or refactoring
- User needs to execute coding tasks autonomously
- User wants to generate shell scripts, fix bugs, or analyze code
- User mentions "copilot session" or wants to share copilot results

## Prerequisites

- GitHub Copilot CLI installed (`copilot --version`)
- Authenticated with GitHub (`copilot login`)
- Valid Copilot subscription

## Core Capabilities

### 1. Non-Interactive Prompt Mode (`-p`)

Execute single prompts and exit. Best for automation and scripting.

```bash
copilot -p "your prompt here" --yolo
```

**Key flags:**
- `-p, --prompt <text>`: Execute prompt in non-interactive mode
- `--silent, -s`: Output only the response (no stats), useful for scripting
- `--yolo` or `--allow-all`: Enable all permissions (required for non-interactive)
- `--share [path]`: Export session to markdown file
- `--share-gist`: Share session to secret GitHub gist
- `--model <model>`: Select specific AI model
- `--autopilot`: Enable autopilot continuation for multi-step tasks
- `--max-autopilot-continues <count>`: Limit autopilot iterations

### 2. Interactive Prompt Mode (`-i`)

Start interactive mode with an initial prompt:

```bash
copilot -i "Fix the bug in main.js" --yolo
```

### 3. Session Management

```bash
# Resume most recent session
copilot --continue

# Resume with session picker
copilot --resume

# Resume specific session
copilot --resume <session-id>
```

### 4. Permission Control

**Quick modes:**
- `--yolo` or `--allow-all`: Enable everything
- `--allow-all-tools`: Auto-approve all tool executions
- `--allow-all-paths`: Access any filesystem path
- `--allow-all-urls`: Access any URL

**Granular control:**
```bash
# Allow specific tools
copilot --allow-tool 'write' --allow-tool 'shell(git:*)'

# Deny specific tools
copilot --deny-tool 'shell(git push)'

# Allow specific directories
copilot --add-dir ~/workspace --add-dir /tmp

# Allow specific URLs
copilot --allow-url github.com --allow-url api.example.com

# Deny specific URLs
copilot --deny-url malicious-site.com
```

### 5. Model Selection

Available models (as of CLI 0.0.418):
- `claude-sonnet-4.6` (default)
- `claude-haiku-4.5` (faster, cheaper)
- `claude-opus-4.6` (more capable)
- `gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.1-codex`
- `gemini-3-pro-preview`

```bash
copilot --model claude-haiku-4.5 -p "quick task"
```

### 6. Output Modes

**Silent mode** (scripting-friendly):
```bash
copilot -p "calculate 2+2" --silent --yolo
# Output: 4
```

**Share to markdown**:
```bash
copilot -p "fix bug in app.js" --yolo --share ./session-report.md
```

**Share to gist**:
```bash
copilot -p "analyze codebase" --yolo --share-gist
```

### 7. Environment Variables

- `COPILOT_ALLOW_ALL=true`: Enable all permissions
- `COPILOT_MODEL=<model>`: Set default model
- `COPILOT_GITHUB_TOKEN=<token>`: Use specific auth token
- `COPILOT_AUTO_UPDATE=false`: Disable auto-updates
- `PLAIN_DIFF=true`: Disable rich diff rendering

## Usage Patterns

### Pattern 1: Quick Code Generation

```bash
copilot -p "Create a Python function to parse CSV files" \
  --silent \
  --yolo \
  --model claude-haiku-4.5
```

### Pattern 2: File Manipulation with Output Capture

```bash
copilot -p "Refactor main.js to use async/await" \
  --yolo \
  --share /tmp/refactor-session.md
```

### Pattern 3: Autopilot for Complex Tasks

```bash
copilot -p "Analyze this codebase and fix all TypeScript errors" \
  --yolo \
  --autopilot \
  --max-autopilot-continues 10 \
  --share /tmp/typescript-fixes.md
```

### Pattern 4: Scoped Permissions

```bash
copilot -p "Run tests and commit results" \
  --allow-tool 'shell(npm:*)' \
  --allow-tool 'shell(git add)' \
  --allow-tool 'shell(git commit)' \
  --deny-tool 'shell(git push)' \
  --allow-tool 'write'
```

### Pattern 5: Model Comparison

```bash
# Fast model for simple tasks
copilot -p "add docstrings" --yolo --model claude-haiku-4.5

# Powerful model for complex analysis
copilot -p "optimize algorithm" --yolo --model claude-opus-4.6
```

## Tool Permissions Reference

### Shell Commands
- `shell(command:*)`: Match command prefix (e.g., `shell(git:*)`)
- `shell(git push)`: Match exact command
- `shell`: Match all shell commands

### File Operations
- `write`: All file create/modify operations (except shell redirects)

### MCP Server Tools
- `<server-name>(tool-name)`: Specific tool from MCP server
- `<server-name>`: All tools from MCP server

### URL Access
- `url(https://github.com)`: Exact URL
- `url(github.com)`: Domain (defaults to HTTPS)
- `url(*.github.com)`: Wildcard subdomain
- `url`: All URLs

## Session Output Format

When using `--share`, sessions are exported as markdown with:
- Session metadata (ID, timestamp, duration)
- Full conversation history
- Tool invocations with results
- Usage statistics (API time, token usage, model breakdown)

Example structure:
```markdown
# 🤖 Copilot CLI Session

> **Session ID:** `uuid`
> **Started:** timestamp
> **Duration:** time
> **Exported:** timestamp

### 👤 User
prompt text

### ✅ `tool-name`
tool output

### 💬 Copilot
response text

---

Total usage est: X Premium requests
API time spent: Xs
Total code changes: +X -Y
```

## Best Practices

### For Automation

1. **Always use `--yolo` or explicit permissions** in non-interactive mode
2. **Use `--silent`** for scripting that parses output
3. **Use `--share`** to capture full session logs
4. **Set `COPILOT_AUTO_UPDATE=false`** in CI/CD environments
5. **Specify `--model`** for consistent behavior

### For Complex Tasks

1. **Use `--autopilot`** for multi-step workflows
2. **Limit autopilot with `--max-autopilot-continues`**
3. **Use `--share` or `--share-gist`** to review autonomous actions
4. **Scope permissions** to minimum required

### For Cost Optimization

1. **Use `claude-haiku-4.5`** for simple, fast tasks
2. **Use `--silent`** to reduce output processing
3. **Avoid interactive mode** for automation (no streaming overhead)

## Error Handling

Common error scenarios:

```bash
# Not authenticated
copilot login

# Insufficient permissions (non-interactive requires --yolo or explicit allows)
copilot -p "task" --yolo

# Session not found
copilot --resume  # Opens picker instead

# Model not available
copilot --model <valid-model> -p "task"
```

## Integration Examples

### With Pi Agent

```bash
# Execute copilot task and capture output
copilot -p "Generate unit tests for src/api.js" \
  --yolo \
  --share /tmp/copilot-output.md

# Parse copilot session output
cat /tmp/copilot-output.md
```

### Shell Script Integration

```bash
#!/bin/bash
set -e

# Run copilot task
output=$(copilot -p "Check for security vulnerabilities" \
  --silent \
  --yolo \
  --model claude-haiku-4.5)

# Process output
if echo "$output" | grep -q "vulnerability"; then
  echo "Security issues found"
  exit 1
fi
```

### CI/CD Pipeline

```yaml
- name: AI Code Review
  run: |
    export COPILOT_AUTO_UPDATE=false
    copilot -p "Review changes in this PR" \
      --yolo \
      --share-gist \
      --model claude-sonnet-4.6
```

## Advanced Features

### Custom Instructions

Copilot loads custom instructions from:
- `AGENTS.md` in repository root
- Custom instruction files in project
- Additional directories via `COPILOT_CUSTOM_INSTRUCTIONS_DIRS`

Disable with `--no-custom-instructions`

### MCP Server Integration

```bash
# Disable builtin MCP servers
copilot --disable-builtin-mcps

# Disable specific MCP server
copilot --disable-mcp-server github-mcp-server

# Add MCP config
copilot --additional-mcp-config @/path/to/config.json
```

### ACP Mode (Agent Client Protocol)

```bash
copilot --acp
```

Starts Copilot as an ACP server for agent integrations.

## Limitations

1. **Interactive features** (diff approval, tool confirmation) don't work in `-p` mode
2. **Requires permissions** - must use `--yolo` or explicit allows in non-interactive
3. **Token limits** - Large codebases may hit context limits
4. **Network required** - All operations require GitHub API access
5. **Session state** - Sessions persist in `~/.copilot/history-session-state/`

## Troubleshooting

```bash
# Check version
copilot --version

# Check logs
ls ~/.copilot/logs/

# Enable debug logging
copilot --log-level debug -p "task" --yolo

# Verify authentication
copilot login

# Update CLI
copilot update
```

## Implementation Checklist

When implementing copilot-cli automation:

- [ ] Verify copilot is installed and authenticated
- [ ] Choose appropriate model for task complexity
- [ ] Set permission flags (`--yolo` or specific allows/denies)
- [ ] Use `--silent` for programmatic output parsing
- [ ] Use `--share` for audit logs and session review
- [ ] Set `COPILOT_AUTO_UPDATE=false` in automation
- [ ] Handle errors (exit codes, stderr)
- [ ] Consider token/cost limits for large tasks
- [ ] Test with `--max-autopilot-continues` for safety
- [ ] Document which permissions are required

## Resources

- Documentation: https://docs.github.com/en/copilot/concepts/agents/copilot-cli
- CLI Help: `copilot --help`, `copilot help <topic>`
- Config location: `~/.copilot/`
- Session history: `~/.copilot/history-session-state/`
- Logs: `~/.copilot/logs/`
