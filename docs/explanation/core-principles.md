# Core Design Principles

Three principles make skills powerful: **progressive disclosure**, **composability**, and **portability**.

## 1. Progressive Disclosure

Skills use a three-level system that minimizes token usage while maintaining specialized expertise:

### Level 1: YAML Frontmatter (Always Loaded)
The frontmatter in every skill tells Claude when to use it, without loading the full skill into context.

```yaml
---
name: sprint-planner
description: Plans project sprints with task prioritization. Use when user mentions "sprint planning" or "create sprint tasks".
---
```

**Why it matters**: Claude reads this and decides instantly whether the skill is relevant. Only if yes does it load the full instructions.

### Level 2: SKILL.md Body (Conditionally Loaded)
When Claude decides your skill is relevant, it loads the full instructions in Markdown.

```markdown
---
name: sprint-planner
description: Plans project sprints. Use when user mentions "sprint planning".
---

# Sprint Planner

## Overview
This skill helps teams plan projects by analyzing capacity and creating prioritized tasks.

## Workflow
### Step 1: Gather Sprint Details
...

### Step 2: Analyze Current Status
...
```

**Why it matters**: Users get full expertise without loading irrelevant skills. Saves tokens on unused skills.

### Level 3: Linked Files (On-Demand)
Additional documentation in `references/` that Claude loads only when needed.

```
sprint-planner/
├── SKILL.md
└── references/
    ├── linear-api-patterns.md    (Loaded if Claude needs API details)
    ├── sprint-templates.md        (Loaded if Claude needs templates)
    └── examples/                  (Loaded if Claude needs examples)
```

**Why it matters**: Keeps context focused. Reference material is there if needed, not cluttering the main skill.

### Real-World Example

**User asks**: "Help me plan the Q1 sprint"

1. Claude loads frontmatter from all skills (< 1KB)
2. Identifies: "sprint-planner skill is relevant"
3. Loads SKILL.md (2-5KB) with step-by-step instructions
4. Executes workflow
5. If Claude needs API details: loads `references/linear-api-patterns.md`
6. Unused skills never loaded → saves thousands of tokens

## 2. Composability

Skills work alongside each other without conflicts or interference.

### What This Means
Multiple skills can be active simultaneously. Your skill should:
- Not assume it's the only skill available
- Clearly indicate when to use itself vs. another tool
- Handle cases where multiple skills could help

### Pattern: Graceful Handoff

**Good**:
```markdown
## When to use other skills
- Use the **github-code-review** skill for automated security scanning
- Use the **documentation-writer** skill for architecture docs
- Use the **linter** skill for code formatting
```

**Bad**:
```markdown
# This skill is the only way to do code review
# Don't use other tools - use this skill for everything
```

### Real-World Example

**Scenario**: User has both:
- `design-to-code` skill (exports designs to code)
- `component-library` skill (manages reusable components)

**User asks**: "Convert this Figma design to React components"

**Good skill behavior**:
1. `design-to-code` loads and extracts components
2. During extraction, recognizes components already in library
3. Instead of regenerating: "Component `Button` exists in component-library. Should I import it or regenerate?"
4. User decides; both skills work together

## 3. Portability

The same skill works identically across Claude.ai, Claude Code, and the API.

### What This Means
Your skill:
- Uses only standard Markdown and YAML
- Doesn't depend on Claude.ai-specific features
- Works with any environment that has your dependencies

### Example: Python Script Dependency

```
my-skill/
├── SKILL.md
├── scripts/
│   └── validate_data.py
└── references/
    └── requirements.txt
```

**Compatibility field** tells users what they need:
```yaml
compatibility: Requires Python 3.10+. Install via: pip install -r scripts/requirements.txt
```

### Real-World Example

Same skill used three ways:

**1. Claude.ai** (User-facing)
```
User: "Validate my CSV data"
→ Skill loads
→ Executes Python script
→ Returns validation results
```

**2. Claude Code** (Developer-facing)
```
Developer: "Run full validation suite"
→ Skill loads
→ Calls scripts/validate_data.py
→ Gets detailed error report
```

**3. API** (Application integration)
```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    container={"skills": ["my-skill"]},
    messages=[{"role": "user", "content": "Validate data"}]
)
```

All three use the exact same skill folder. No modification needed.

### What Breaks Portability (Avoid)

❌ Platform-specific code:
```markdown
# (In SKILL.md)
This only works in Claude.ai because it uses the download feature
```

❌ Hard-coded environment dependencies:
```python
# (In scripts/process.py)
# Only works on macOS with Homebrew
import subprocess
result = subprocess.run(['brew', 'list'], ...)
```

❌ Assuming specific tool availability:
```markdown
Use this skill with the GitHub MCP server. If you don't have it, too bad.
```

✅ Declare requirements clearly:
```yaml
compatibility: Requires Python 3.10+. GitHub MCP server optional but recommended.
```

## Why These Principles Matter

### Token Efficiency
- Only load what's needed
- Multiple unused skills don't cost tokens
- Result: faster, cheaper API calls

### Better User Experience
- Skills don't interfere with each other
- Clearer when to use each skill
- Consistent results across platforms

### Maintainability
- Skills are self-contained modules
- Updates don't break other skills
- Reuse across projects

### Ecosystem Value
- Skills become portable assets
- Can be shared across projects
- Community can build on your work

## Putting It Together

A well-designed skill:

1. **Progressive Disclosure**: Clear frontmatter, focused SKILL.md, optional references
2. **Composability**: Knows when to recommend other skills
3. **Portability**: Works on Claude.ai, Code, and API without modification

---

**Next**: [Architecture patterns](./architecture-patterns.md) — Three categories of skills and their structure
