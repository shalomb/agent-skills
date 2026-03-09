# YAML Frontmatter Specification

**Quick ref**: Minimal template and complete field reference

## Minimal Required Frontmatter

```yaml
---
name: skill-name
description: What it does. Use when user [trigger phrases].
---
```

That's all you absolutely need. Everything else is optional.

## Complete Reference

### `name` (required)
The unique identifier for your skill.

**Rules**:
- kebab-case ONLY: `my-skill-name`
- No spaces, capitals, or underscores
- Must match folder name exactly
- 3-50 characters recommended

```yaml
---
name: sprint-planner
---
```

### `description` (required)
Tells Claude when to load your skill. This appears in system prompt.

**Rules**:
- Under 1024 characters
- MUST include BOTH:
  1. What the skill does (benefit statement)
  2. When to use it (trigger phrases)
- No XML tags (< or >)

**Good examples**:
```yaml
# Clear triggers, specific use case
description: Plans project sprints with task creation and prioritization. Use when user mentions "sprint planning", "plan this sprint", or asks to "create sprint tasks".

# File-type specific
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# Multi-service workflow
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".
```

**Bad examples**:
```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Missing benefit statement
description: Implements the Project entity model with hierarchical relationships.

# No user language
description: Calls the ProjectHub MCP server with proper parameters.
```

### `license` (optional)
Software license for open-source skills.

**Common values**:
- `MIT` — Most permissive, widely used
- `Apache-2.0` — Business-friendly with patent protection
- `GPL-3.0` — Requires derivative works to be open-source
- `CC0` — Public domain

```yaml
license: MIT
```

### `compatibility` (optional)
Environment or dependency requirements.

**Use for**:
- Required MCP servers
- System packages needed
- Version requirements
- Platform limitations

**Format**: 1-500 characters, plain text

```yaml
# Simple requirement
compatibility: Requires ProjectHub MCP server

# Multiple requirements  
compatibility: Requires Python 3.10+. MCP servers needed: Linear, Figma, GitHub.

# Platform limitation
compatibility: Works with Claude.ai and Claude Code. Requires Code Execution Tool beta for API usage.
```

### `metadata` (optional)
Custom key-value pairs for your skill.

**Common keys**:
- `author` — Creator name
- `version` — Semantic version (1.0.0)
- `mcp-server` — Primary MCP dependency
- `category` — Type (e.g., "workflow", "document", "analysis")
- `last-updated` — ISO date

```yaml
metadata:
  author: Your Name
  version: 1.0.0
  mcp-server: projecthub
  category: workflow
  last-updated: 2026-03-09
```

## Complete Example

```yaml
---
name: customer-onboarding
description: Manages complete customer onboarding including account creation, payment setup, and welcome emails. Use when user says "onboard new customer", "set up subscription", or "create PayFlow account".
license: MIT
compatibility: Requires PayFlow MCP server. Works with Stripe for payment processing.
metadata:
  author: Your Company
  version: 2.1.0
  mcp-server: payflow
  category: workflow
  last-updated: 2026-03-09
---

# Rest of your SKILL.md content goes here...
```

## Validation Rules

### Forbidden Content
- ❌ XML angle brackets: `< >` (security)
- ❌ Skills named "claude" or "anthropic" (reserved)
- ❌ Special characters outside kebab-case

### Format Requirements
- ❌ Must start with `---` (three dashes)
- ❌ Must end with `---` (three dashes)
- ❌ Valid YAML syntax
- ❌ UTF-8 encoding

### Case Sensitivity
- ❌ `SKILL.md` ❌ → must be exactly `SKILL.md`
- ❌ `skill.md` ❌
- ✅ `SKILL.md` ✅

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid frontmatter" | Check YAML syntax: proper `---` delimiters, colons after field names |
| "Invalid skill name" | Use kebab-case only (my-skill, not MySkill or my_skill) |
| "Skill won't upload" | Verify filename is exactly `SKILL.md` (case-sensitive) |
| "Skill doesn't trigger" | Rewrite description with clearer trigger phrases users would actually say |
| "Triggers too often" | Add negative example ("Do NOT use for...") or be more specific |

## See Also

- [Create your first skill](../how-to/create-first-skill.md) — Tutorial with examples
- [Skill anatomy](./skill-anatomy.md) — Full SKILL.md structure reference
- [Core principles](../explanation/core-principles.md) — Why progressive disclosure matters
