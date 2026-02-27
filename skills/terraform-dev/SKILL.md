# Terraform Development Workflow Skill

Automated terraform development workflow with file watching and continuous validation.

## Triggers

Use this skill when:
- User mentions "terraform watch", "tf watch", or "terraform dev workflow"
- User wants to auto-run terraform commands on file changes
- User wants continuous validation during terraform development
- User mentions "terraform fmt on save" or "terraform validate automatically"

## Overview

This skill provides `tf-watcher`, a tool that watches terraform files for changes and automatically runs validation commands. Useful for maintaining clean, validated code during development.

## Prerequisites

- `inotify-tools` (Linux) or `fswatch` (macOS)
- Terraform installed
- Optional: `tflint`, `tfsec`, `terraform-docs` for additional checks

## Installation

Linux:
```bash
sudo apt install inotify-tools
```

macOS:
```bash
brew install fswatch
```

## Usage

### Basic Watch Mode

Run from your terraform workspace directory:

```bash
./scripts/tf-watcher
```

This will watch for `.tf` file changes and automatically run:
- `terraform fmt`
- `terraform validate`
- `terraform init` (if needed)
- `terraform plan` (if configured)

### Configuring Watched Commands

Create a `.tf-watcher.rc` file in your workspace to control which commands run:

```bash
# Add specific commands to watch
tf-watcher plan      # Enable plan on every change
tf-watcher tflint    # Enable tflint on every change
tf-watcher tfsec     # Enable tfsec on every change
```

View current configuration:
```bash
cat .tf-watcher.rc
```

### Custom Commands

You can configure tf-watcher to run custom validation:

```bash
# .tf-watcher.rc example
plan
tflint
tfsec
terraform-docs
```

When `.tf-watcher.rc` exists, only listed commands will run automatically.

## Workflow Examples

### Example 1: Minimal Validation

```bash
cd /path/to/terraform/workspace

# Start watcher (fmt + validate only)
tf-watcher
```

Edit your `.tf` files - they'll be formatted and validated automatically.

### Example 2: Full Validation Pipeline

```bash
# Enable comprehensive checks
echo "plan" > .tf-watcher.rc
echo "tflint" >> .tf-watcher.rc
echo "tfsec" >> .tf-watcher.rc

# Start watcher
tf-watcher
```

Now every save triggers:
1. `terraform fmt`
2. `terraform validate`
3. `terraform plan`
4. `tflint`
5. `tfsec`

### Example 3: Integration with TFC

```bash
# Watch and validate, then trigger TFC speculative plan
cat > .tf-watcher.rc <<EOF
validate
tflint
EOF

# Start watcher
tf-watcher &

# Work on your changes...
# When ready, push to trigger TFC plan
git add .
git commit -m "feature: add new resource"
git push
```

## Configuration

### .tf-watcher.rc Format

Simple list of commands to run, one per line:

```
init
validate
plan
tflint
tfsec
terraform-docs
```

Commands run in the order listed.

### Environment Variables

```bash
DEBUG=1 tf-watcher    # Enable debug output
```

## Integration Patterns

### Pattern 1: Pre-commit Validation

Use tf-watcher during development, ensures commits are pre-validated:

```bash
# Terminal 1: Watch mode
tf-watcher

# Terminal 2: Development
vim main.tf
git add main.tf
git commit -m "clean, validated change"
```

### Pattern 2: TDD for Infrastructure

```bash
# 1. Write test (expected state)
echo "plan" > .tf-watcher.rc
tf-watcher &

# 2. Edit infrastructure
vim resources.tf

# 3. Watch plan output update automatically
# 4. Iterate until plan matches expectations
```

### Pattern 3: Continuous Security Scanning

```bash
echo "tfsec" > .tf-watcher.rc
tf-watcher
```

Every change is immediately scanned for security issues.

## Common Commands

| Command | Purpose |
|---------|---------|
| `fmt` | Format files |
| `validate` | Validate syntax |
| `plan` | Generate execution plan |
| `init` | Initialize workspace |
| `tflint` | Lint terraform code |
| `tfsec` | Security scanning |
| `terraform-docs` | Generate documentation |

## Best Practices

1. **Start minimal** - Begin with just `fmt` and `validate`
2. **Add plan selectively** - Plan can be slow on large workspaces
3. **Use .tf-watcher.rc** - Document which checks your team requires
4. **Commit .tf-watcher.rc** - Share workflow configuration with team
5. **Combine with pre-commit** - tf-watcher for development, pre-commit hooks for enforcement

## Troubleshooting

### Watcher Not Starting

```bash
# Check if inotify-tools is installed (Linux)
which inotifywait

# Install if missing
sudo apt install inotify-tools
```

### Commands Running Too Frequently

```bash
# Reduce checked commands
cat > .tf-watcher.rc <<EOF
validate
EOF
```

### False Positive Triggers

Add exclusions to watcher script or use `.gitignore` patterns.

### Plan Taking Too Long

```bash
# Disable plan, run manually
echo "validate" > .tf-watcher.rc
echo "tflint" >> .tf-watcher.rc

# Run plan manually when ready
terraform plan
```

## Advanced Usage

### Multi-Workspace Development

```bash
# Terminal for each workspace
cd workspace-dev && tf-watcher &
cd workspace-staging && tf-watcher &
cd workspace-prod && tf-watcher &
```

### Integration with IDE

Many IDEs support external tools:

**VSCode:**
```json
{
  "tasks": [
    {
      "label": "tf-watcher",
      "type": "shell",
      "command": "./scripts/tf-watcher",
      "problemMatcher": [],
      "isBackground": true
    }
  ]
}
```

### Custom Validation Scripts

Create wrapper scripts for team-specific checks:

```bash
#!/bin/bash
# .tf-watcher.rc
custom-validation
```

```bash
#!/bin/bash
# custom-validation script
terraform fmt -check
terraform validate
./team-specific-checks.sh
```

## Files

- `scripts/tf-watcher` - Main watcher script
- `.tf-watcher.rc` - Workspace-specific configuration (optional)

## Related Skills

- **tfc-api** - Query TFC workspace and run status
- **github-cli** - Create PRs with validated terraform

## Credits

Original script from the CSE team tools collection.
