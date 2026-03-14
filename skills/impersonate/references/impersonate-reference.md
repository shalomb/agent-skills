---
name: impersonate
description: Find and assume roles from agent definitions in .github/agents/*.md files. Load agent context to guide specialized development workflows.
---

# AGENT IMPERSONATION SKILL

## NAME
**impersonate** - Discover and assume roles from agent definitions in .github/agents/*.md

## SYNOPSIS
Discover agent definitions in `.github/agents/*.md`, read and parse them, then assume their roles for specialized task guidance.

## OVERVIEW

This skill enables seamless integration with Takeda's **agent-driven development model**. Each project uses specialized agents (e.g., `@developer-agent`, `@review-agent`, `@release-agent`, `@triage-agent`) that provide context-aware workflows, quality standards, and specialized expertise.

The impersonate skill:
- ✅ **Discovers** all available agents in `.github/agents/`
- ✅ **Reads** agent definitions and extracts role context
- ✅ **Loads** agent persona, expertise, workflows, and quality standards
- ✅ **Assumes** the agent role for upcoming tasks
- ✅ **Applies** agent-specific workflows, checklists, and guidelines

## DESCRIPTION

### Key Principles

1. **Project-Aware**: Works with any project using `.github/agents/` directory
2. **Context Extraction**: Automatically extracts role, expertise, workflows, and standards
3. **Persona Adoption**: Assumes agent identity and applies their specialized guidance
4. **Workflow Integration**: Uses agent-defined processes, checklists, and quality gates
5. **Zero Configuration**: No setup required - discovers agents automatically

### Agent Definition Format

Each agent is documented in a markdown file at `.github/agents/<agent-name>.md` with sections like:

```markdown
# Agent Name

## Overview
[High-level description of agent's role and specialty]

## Expertise
[List of specialized areas this agent handles]

## Workflows
[Agent-specific workflows and processes]

## Quality Standards
[Agent's quality requirements and checklists]

## Tools & Integration
[Tools, scripts, and external integrations]

## References
[Links to related documentation]
```

## QUICK START

| Task | Command |
|------|---------|
| **List all agents** | `ls -1 .github/agents/*.md \| sed 's\|.*/\|\|;s/.md$//'` |
| **Load agent** | `cat .github/agents/<agent-name>.md` |
| **Get workflows** | `sed -n '/^## Workflows/,/^##/p' .github/agents/<agent-name>.md` |
| **Get quality** | `sed -n '/^## Quality Standards/,/^##/p' .github/agents/<agent-name>.md` |
| **Get expertise** | `sed -n '/^## Expertise/,/^##/p' .github/agents/<agent-name>.md` |

## COMMANDS

### 1. Discover Available Agents

**List all agents in current project**
```bash
# Show all agents with names and descriptions
ls -1 .github/agents/*.md 2>/dev/null | while read f; do
  name=$(basename "$f" .md)
  desc=$(head -20 "$f" | grep -A1 "^##" | head -1)
  echo "✓ @$name"
done

# Or with descriptions
for f in .github/agents/*.md 2>/dev/null; do
  basename "$f" .md
  head -5 "$f" | grep -E "^#|description|specialty" | head -2
done
```

**Count available agents**
```bash
ls -1 .github/agents/*.md 2>/dev/null | wc -l
```

**Check if agent exists**
```bash
# Check for specific agent
if [ -f ".github/agents/developer-agent.md" ]; then
  echo "✓ developer-agent found"
else
  echo "✗ developer-agent not found"
fi
```

### 2. Load Agent Definition

**Read full agent definition**
```bash
# Load complete agent definition
cat .github/agents/developer-agent.md

# Or just the overview section
sed -n '/^## Overview/,/^##/p' .github/agents/developer-agent.md | head -n -1
```

**Extract agent sections**
```bash
# Get agent expertise
sed -n '/^## Expertise/,/^##/p' .github/agents/developer-agent.md

# Get workflows
sed -n '/^## Workflows/,/^##/p' .github/agents/developer-agent.md

# Get quality standards
sed -n '/^## Quality Standards/,/^##/p' .github/agents/developer-agent.md

# Get tools
sed -n '/^## Tools/,/^##/p' .github/agents/developer-agent.md
```

**Extract specific information with jq (if JSON format)**
```bash
# If agent stores context as JSON block in markdown
grep -A 100 '```json' .github/agents/developer-agent.md | \
  grep -B 100 '```' | \
  sed '$ d' | sed '1 d' | jq '.'
```

### 3. Assume Agent Role

**Initialize developer-agent**
```bash
# Read developer-agent definition
DEV_AGENT=$(cat .github/agents/developer-agent.md)

# Display role context
echo "🤖 Assuming @developer-agent role..."
echo "$DEV_AGENT" | head -50
```

**Initialize review-agent**
```bash
# Read review-agent definition
REVIEW_AGENT=$(cat .github/agents/review-agent.md)

# Show review workflows
echo "🔍 Assuming @review-agent role..."
sed -n '/^## Workflows/,/^##/p' <<< "$REVIEW_AGENT"
```

**Initialize release-agent**
```bash
# Read release-agent definition
RELEASE_AGENT=$(cat .github/agents/release-agent.md)

# Show release workflows
echo "🚀 Assuming @release-agent role..."
sed -n '/^## Workflows/,/^##/p' <<< "$RELEASE_AGENT"
```

### 4. Apply Agent Workflows

**Load workflow from agent definition**
```bash
# Extract workflow steps from agent definition
AGENT_FILE=".github/agents/developer-agent.md"
WORKFLOW="Development Workflow"

sed -n "/^## $WORKFLOW/,/^##/p" "$AGENT_FILE" | head -n -1
```

**Use agent quality checklist**
```bash
# Extract quality standards checklist
AGENT_FILE=".github/agents/developer-agent.md"

sed -n '/^## Quality Standards/,/^##/p' "$AGENT_FILE" | \
  grep -E "^\s*\-\s*\[" | \
  sed 's/^\s*//g'
```

**Apply agent's workspace-specific guidance**
```bash
# For projects with agent configuration
if [ -f ".github/agents/config.json" ]; then
  jq '.agents.developer_agent.guidance' .github/agents/config.json
fi
```

### 5. Agent-Specific Task Integration

**Run task with developer-agent guidance**
```bash
# Set agent context
CURRENT_AGENT="developer-agent"
AGENT_CONTEXT=$(cat .github/agents/developer-agent.md)

echo "Running task with @developer-agent guidance..."
echo "Expertise: $(sed -n '/^## Expertise/,/^##/p' <<< "$AGENT_CONTEXT")"
echo ""
echo "Proceed with development workflow..."
```

**Run task with review-agent guidance**
```bash
# Set agent context
CURRENT_AGENT="review-agent"
AGENT_CONTEXT=$(cat .github/agents/review-agent.md)

echo "Running task with @review-agent guidance..."
echo ""
sed -n '/^## Quality Standards/,/^##/p' <<< "$AGENT_CONTEXT"
```

**Multi-agent workflow**
```bash
# Chain multiple agents for complex tasks
AGENTS=("developer-agent" "review-agent" "release-agent")

for agent in "${AGENTS[@]}"; do
  echo "=== Loading @$agent ==="
  head -20 ".github/agents/$agent.md"
  echo ""
done
```

### 6. Display Agent Summary

**Show all agents and their specialties**
```bash
echo "Available Agents in this Repository:"
echo "===================================="
echo ""

for agent_file in .github/agents/*.md; do
  agent_name=$(basename "$agent_file" .md)
  echo "🤖 @$agent_name"
  
  # Extract first description line
  sed -n '1,20p' "$agent_file" | grep -E "specialty|handles|expertise|focuses" | head -1
  
  echo ""
done
```

**Create agent reference card**
```bash
# Quick reference for all agents
echo "Agent Reference Card"
echo "===================="
echo ""

for agent_file in .github/agents/*.md; do
  name=$(basename "$agent_file" .md)
  
  echo "### @$name"
  
  # Get first 3 lines of overview
  sed -n '/^## Overview/,/^##/p' "$agent_file" | head -3
  
  # Show key workflows
  echo "**Key workflows:**"
  sed -n '/^## Workflows/,/^##/p' "$agent_file" | head -2
  
  echo ""
done
```

## EXAMPLES

### Example 1: Load Developer Agent for Feature Development

```bash
# 1. Discover available agents
ls .github/agents/*.md

# 2. Load developer-agent
DEV_AGENT=$(cat .github/agents/developer-agent.md)

# 3. Display key sections
echo "=== Developer Agent Overview ==="
sed -n '/^## Overview/,/^## Expertise/p' <<< "$DEV_AGENT"

echo ""
echo "=== Key Workflows ==="
sed -n '/^## Workflows/,/^## Quality/p' <<< "$DEV_AGENT"

# 4. Proceed with feature development using workflow guidance
```

### Example 2: Chain Agents for Complete Task

```bash
# Task: Create feature from issue to release

# Step 1: @developer-agent creates feature
echo "📝 Step 1: Load @developer-agent for development"
cat .github/agents/developer-agent.md | head -50

# Step 2: @review-agent validates PR
echo "✅ Step 2: Load @review-agent for PR review"
sed -n '/^## Workflows/,/^##/p' .github/agents/review-agent.md

# Step 3: @release-agent manages release
echo "🚀 Step 3: Load @release-agent for release"
sed -n '/^## Workflows/,/^##/p' .github/agents/release-agent.md
```

### Example 3: Use Agent Quality Standards

```bash
# Load quality standards from developer-agent
QUALITY_CHECKS=$(sed -n '/^## Quality Standards/,/^##/p' \
  .github/agents/developer-agent.md)

echo "=== Quality Checklist ==="
echo "$QUALITY_CHECKS" | grep -E "^\s*-\s*" | sed 's/^\s*//g'

# Verify each check before committing
```

## AGENT STRUCTURE

### Typical Agent Sections

Each agent definition typically includes:

| Section | Purpose | Example |
|---------|---------|---------|
| **Overview** | Agent's role and specialty | "Handles code implementation with integrated tests" |
| **Expertise** | Areas of specialization | "Feature development, bug fixes, testing" |
| **Workflows** | Step-by-step processes | Development workflow with atomic commits |
| **Quality Standards** | Requirements and checklists | Testing, documentation, formatting requirements |
| **Tools** | Available tools and integrations | GitHub CLI, Make, Terraform, etc. |
| **References** | Related documentation | Links to guides, standards, templates |

### Common Agents

| Agent | Role | When to Use |
|-------|------|-----------|
| `@developer-agent` | Code + tests + docs | Implementing features, fixing bugs |
| `@review-agent` | PR validation | Code review, quality assurance |
| `@release-agent` | Release management | Versioning, publishing, deployment |
| `@triage-agent` | Issue management | Organizing, prioritizing, categorizing |

## INTEGRATION PATTERNS

### Pattern 1: Task-Driven Agent Selection

```bash
# Select agent based on task type
task_type="feature-development"

case "$task_type" in
  "feature-development")
    agent=".github/agents/developer-agent.md"
    ;;
  "code-review")
    agent=".github/agents/review-agent.md"
    ;;
  "release")
    agent=".github/agents/release-agent.md"
    ;;
  *)
    echo "Unknown task type"
    ;;
esac

echo "Loading agent: $agent"
cat "$agent"
```

### Pattern 2: Workflow-Driven Execution

```bash
# Execute workflow from agent definition
agent_file=".github/agents/developer-agent.md"
workflow_name="Feature Development"

# Extract workflow section
sed -n "/### $workflow_name/,/### /p" "$agent_file" | head -n -1
```

### Pattern 3: Quality Gate Enforcement

```bash
# Load quality standards and enforce
agent_file=".github/agents/developer-agent.md"

# Parse quality checklist
quality_items=$(sed -n '/^## Quality Standards/,/^##/p' "$agent_file" | \
  grep "^\s*-\s*\[" | \
  sed 's/.*\[\s*\]\s*//g')

echo "Quality Gates:"
echo "$quality_items"
```

## BEST PRACTICES

### 1. Always Discover First
```bash
# List available agents before starting
ls -1 .github/agents/ | sed 's/.md$//'
```

### 2. Load Full Context
```bash
# Read complete agent definition for full context
cat .github/agents/<agent-name>.md
```

### 3. Reference Workflows
```bash
# Use agent-defined workflows, don't invent new ones
sed -n '/^## Workflows/,/^##/p' .github/agents/<agent-name>.md
```

### 4. Apply Quality Standards
```bash
# Enforce agent's quality requirements
sed -n '/^## Quality Standards/,/^##/p' .github/agents/<agent-name>.md
```

### 5. Document Agent Usage
```bash
# When starting task, document which agent(s) you're using
echo "Using @<agent-name> for this task"
```

## TROUBLESHOOTING

### Agents Not Found

**Problem**: `.github/agents/` directory doesn't exist

**Solution**:
```bash
# Check if directory exists
if [ ! -d ".github/agents" ]; then
  echo "No agents directory found"
  echo "This repository may not use agent-driven development"
fi
```

### Cannot Read Agent File

**Problem**: Permission denied when reading agent file

**Solution**:
```bash
# Check file permissions
ls -la .github/agents/*.md

# If needed, make readable
chmod 644 .github/agents/*.md
```

### Malformed Agent Definition

**Problem**: Agent file doesn't have expected structure

**Solution**:
```bash
# Validate markdown structure
grep "^##" .github/agents/<agent-name>.md

# Should show: Overview, Expertise, Workflows, Quality Standards, etc.
```

## RELATED SKILLS

- **kedb**: Search Takeda's Known Error Database for solutions
- **takeda-building-blocks**: Discover and implement Terraform Building Blocks
- **tfc-api**: Query Terraform Cloud workspace and run data

## REFERENCES

- [Agent-Driven Development Model](#)
- [Takeda Repository Standards](#)
- [GitHub Actions Integration](#)
- [Custom Agent Development](#)

## VERSION

**impersonate** skill v1.0 - Supports all standard agent definitions in `.github/agents/`

Last updated: 2026-02-12
