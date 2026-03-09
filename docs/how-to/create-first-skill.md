# How to Create Your First Skill

**Time estimate**: 15-30 minutes  
**Prerequisites**: Claude account (Claude.ai or Claude Code)  
**Output**: A working skill you can use immediately

## Overview

By the end of this guide, you'll have built a functional skill that Claude loads automatically. You'll learn the core structure, best practices, and testing approach.

## Step 1: Identify Your Use Case (5 minutes)

Start with a concrete goal, not a vague idea.

### Bad use case definitions:
- "Help with documentation"
- "Improve my workflow"
- "Make Claude smarter"

### Good use case definition:

**Title**: Project Sprint Planning

**Trigger**: User says "help me plan this sprint" or "create sprint tasks"

**Steps**:
1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates

**Result**: Fully planned sprint with tasks created

**Success looks like**: 
- Skill loads automatically when user mentions "sprint" or "planning"
- All tasks created without user needing to clarify labels/estimates
- Takes < 3 API calls (no retries)

### Find Your Use Case

Ask yourself:
- What repeatable workflow do I do regularly?
- What multi-step process could be automated?
- What domain knowledge should Claude remember?

**Examples that work well**:
- Creating documents from templates
- Multi-step approval workflows
- Consistent output formatting
- Data transformation pipelines
- API coordination across multiple systems

**Examples that DON'T work well**:
- One-off creative writing tasks
- Questions Claude can answer without context
- Tasks requiring human judgment Claude can't make
- Anything that's truly unique every time

## Step 2: Create the Folder Structure (5 minutes)

On your machine, create a folder for your skill:

```bash
mkdir my-skill-name
cd my-skill-name
```

**Critical rules**:
- Use kebab-case: `my-skill-name` (not `my_skill_name` or `MySkillName`)
- Match the folder name exactly in your skill
- Use lowercase only

Create empty files:

```bash
touch SKILL.md
mkdir scripts references assets
```

Your structure should look like:

```
my-skill-name/
├── SKILL.md                    # Required - your instructions go here
├── scripts/                     # Optional - Python, Bash, etc.
├── references/                  # Optional - documentation
└── assets/                      # Optional - templates, etc.
```

## Step 3: Write the YAML Frontmatter (5 minutes)

At the top of `SKILL.md`, add frontmatter. This tells Claude when to load your skill.

```yaml
---
name: my-skill-name
description: What it does. Use when user [specific phrases].
---
```

**Rules**:
- `name`: Must match folder name, kebab-case, no spaces/capitals
- `description`: Under 1024 characters, MUST include:
  - What the skill does
  - When to use it (trigger phrases)

### Good example:

```yaml
---
name: sprint-planner
description: Plans project sprints with task creation and prioritization. Use when user mentions "sprint planning", "plan this sprint", or asks to "create sprint tasks for this week".
---
```

### Bad examples:

```yaml
# ❌ Too vague
description: Helps with projects.

# ❌ Missing triggers  
description: Creates sophisticated multi-page documentation systems.

# ❌ No benefit statement
description: Implements project entity model with hierarchical relationships.
```

Optional fields (add if relevant):

```yaml
---
name: my-skill
description: [your description]
license: MIT
compatibility: Requires ProjectHub MCP server
metadata:
  author: Your Name
  version: 1.0.0
---
```

## Step 4: Write the Instructions (10-15 minutes)

Below the frontmatter, write clear, step-by-step instructions. Use this template:

```markdown
---
name: sprint-planner
description: Plans project sprints with task creation. Use when user mentions "sprint planning" or "create sprint tasks".
---

# Sprint Planner Skill

## Instructions

### Overview
This skill helps you plan project sprints by analyzing team capacity and creating prioritized tasks.

### Workflow

#### Step 1: Gather Sprint Details
Ask the user for:
- Sprint duration (e.g., 2 weeks)
- Team size and capacity
- Key priorities or themes

#### Step 2: Analyze Current Status
1. Fetch project status from Linear via MCP
2. Calculate team velocity from historical data
3. Identify blocked or in-progress items

#### Step 3: Create Sprint Plan
For each priority:
1. Break into subtasks (3-5 per story)
2. Estimate using team's historical velocity
3. Create tasks in Linear with:
   - Label: `sprint-2026-q1-w1`
   - Estimate: velocity-based (days)
   - Owner: based on team assignment

#### Step 4: Confirm and Summary
1. Create a sprint summary
2. Show task breakdown by team member
3. Highlight any capacity concerns

## Examples

### Example: Marketing Campaign Sprint
User says: "Help me plan the marketing sprint for product launch"

Actions:
1. Fetch project status and team assignments
2. Ask about timeline and priorities
3. Create tasks: content, design, approval workflows
4. Summary shows task distribution

Expected output: 8-12 tasks created, team notified

### Example: Engineering Sprint  
User says: "Create sprint tasks for the infrastructure refactor"

Actions:
1. Get current tech debt backlog
2. Propose task sequence (dependencies first)
3. Create implementation tasks with review gates

Expected output: 12-15 subtasks, architecture docs linked

## Error Handling

### Linear API Connection Failed
**Symptom**: See "Failed to authenticate with Linear"

**Fix**:
1. Check Linear API key in MCP settings
2. Verify key has project write permissions
3. Reconnect: Settings > Extensions > Linear > Reconnect

### Task Creation Failed
**Symptom**: Some tasks created, others skipped

**Fix**:
1. Check if task names exceed Linear's limits
2. Verify all required fields (owner, estimate) are set
3. Try creating fewer tasks per request (max 10)

### Capacity Analysis Inaccurate
**Symptom**: Claude suggests impossible capacity

**Fix**:
1. Provide explicit team member availability
2. List any ongoing commitments blocking the sprint
3. Specify any external dependencies

## Reference Documentation

For detailed Linear API patterns, see:
- `references/linear-api-patterns.md` - Rate limits, pagination, error codes
- `references/sprint-templates.md` - Pre-built sprint templates
```

## Step 5: Test Your Skill (5 minutes)

### Test it in Claude.ai:

1. **Upload the skill**: Click ⊕ in Claude.ai > Upload files > Select your `SKILL.md`
2. **Test triggers**: Ask Claude something that should trigger your skill
   - ✅ "Help me plan this sprint"
   - ✅ "Create sprint tasks for Q1"
   - ❌ "What's the weather?" (should NOT trigger)

3. **Test functionality**: 
   - Does Claude follow the steps you outlined?
   - Does it ask for information when unclear?
   - Does it handle errors gracefully?

### Expected behavior:

✅ **Good result**:
- Claude loads your skill automatically
- Follows the steps in order
- Asks clarifying questions when needed
- Completes the workflow

❌ **Problem signs**:
- Claude doesn't recognize the trigger
- Skips steps from your instructions
- Gets stuck asking for the same info
- Tries to do things not in your instructions

### If it doesn't work:

**Check your frontmatter**:
```bash
# Make sure it's valid YAML
head -5 SKILL.md
```

**Rewrite the description** with clearer trigger phrases:
```yaml
# Before (too vague)
description: Helps with planning.

# After (specific triggers)
description: Plans project sprints with task prioritization. Use when user says "plan sprint", "sprint planning", or "create sprint tasks".
```

**Simplify the instructions**:
- Remove jargon
- Add numbered steps
- Include concrete examples
- Be explicit about when to do each thing

## Step 6: Iterate and Improve (5-10 minutes)

### Common improvements:

**Problem**: "Claude asks too many clarifying questions"  
**Fix**: Add a section "Reasonable Defaults" with standard assumptions

**Problem**: "Claude sometimes skips steps"  
**Fix**: Use clearer numbering and add "Before proceeding to step X, you must..."

**Problem**: "Skill triggers on unrelated tasks"  
**Fix**: Make trigger phrases MORE specific, add "❌ Should NOT trigger:" examples

**Example iteration**:

```markdown
### Reasonable Defaults
If user doesn't specify:
- Sprint duration: Assume 2 weeks
- Team size: Ask explicitly (no default)
- Priorities: Ask for top 3

### Common Issues
If task creation fails:
- Check Linear API key is set
- Reduce batch size to 5 tasks max
- Add 1-second delay between requests
```

## What's Next?

### Your skill now works! You can:

1. **Share it with your team**: Copy the folder to shared drive
2. **Add more documentation**: Create `references/` files for detailed info
3. **Add automation**: Put Python/Bash scripts in `scripts/` folder
4. **Set up MCP**: If you need data access, connect an MCP server
5. **Deploy it**: See [Distribute your skill](./distribute-skill.md)

### Ready for the next level?

- Learn [detailed structure](../reference/skill-anatomy.md)
- Set up [MCP integration](./setup-mcp-integration.md)
- Read about [design patterns](../explanation/architecture-patterns.md)
- See [real-world examples](#examples)

## Real-World Examples

### Example 1: Documentation Skill
```yaml
name: technical-writer
description: Creates consistent technical documentation with templates and style guides. Use when user asks to "write docs", "create README", or "document this API".
```

### Example 2: Workflow Automation
```yaml
name: customer-onboarding
description: Manages complete customer onboarding including account creation, payment setup, and welcome emails. Use when user says "onboard new customer" or "set up subscription".
```

### Example 3: MCP Enhancement
```yaml
name: github-code-review
description: Analyzes GitHub PRs with security scanning and coverage analysis. Use when user wants code review or compliance check on PRs.
```

---

**Congratulations!** You've built your first skill. Keep iterating to make it better. The best skills come from real, repeated use.

**Next**: See [How to Structure a Skill](./structure-skill.md) for more details on file organization and best practices.
