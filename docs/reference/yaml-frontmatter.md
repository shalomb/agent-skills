# Reference: YAML Frontmatter Specification

This document provides the complete specification for `SKILL.md` frontmatter fields, aligned with the official [Agent Skills specification](https://agentskills.io/specification).

## Minimal Required Frontmatter

Every skill requires only two fields:

```yaml
---
name: skill-name
description: What it does. Use when [trigger conditions].
---
```

Everything else is optional.

## Complete Frontmatter Reference

### Required Fields

#### `name`
**Type:** String  
**Min:** 1 character  
**Max:** 64 characters  
**Pattern:** Lowercase alphanumeric + hyphens only

**Rules:**
- Must contain only `a-z`, `0-9`, and hyphens (`-`)
- Cannot start or end with a hyphen
- Cannot contain consecutive hyphens (`--`)
- Must match parent directory name exactly
- Must not conflict with reserved names

**Examples:**
```yaml
name: pdf-processing        ✓ Valid
name: data-analysis         ✓ Valid
name: github-cli-wrapper    ✓ Valid
name: PDF-Processing        ✗ Uppercase forbidden
name: -pdf                  ✗ Cannot start with hyphen
name: pdf--processing       ✗ No consecutive hyphens
name: pdf_processing        ✗ Underscores not allowed
name: claude                ✗ Reserved name
```

#### `description`
**Type:** String  
**Min:** 1 character  
**Max:** 1024 characters  
**Required content:** Both capability and trigger conditions

The description is critical — agents use it to decide whether a skill is relevant to the current task.

**Must include:**
1. **What the skill does** — The capability or outcome
2. **When to use it** — Trigger phrases or conditions

**Effective descriptions:**
```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.

description: Generates comprehensive unit tests for Python functions using pytest. Use when implementing new functions, improving test coverage, or when the user asks to "write tests" or "add test cases".

description: Analyzes GitHub pull requests for code quality issues, performance problems, and style violations. Use when reviewing PRs, checking for bugs, or when the user mentions "code review" or "review this PR".
```

**Poor descriptions:**
```yaml
description: Helps with PDFs.                           # Too vague
description: Extracts PDF text.                          # No trigger conditions
description: For testing Python.                         # Vague triggers
description: Uses pdfplumber library.                    # Technical detail, not benefit
```

**Best practices:**
- Be specific about what the skill does
- Include user language and phrases they would actually say
- Clarify the trigger with "Use when..."
- Avoid implementation details (library names, API details)

### Optional Fields

#### `license`
**Type:** String  
**Recommended length:** 1–50 characters  
**Format:** License name or reference to license file

Specifies the open-source or proprietary license under which the skill is distributed.

**Common values:**
```yaml
license: MIT
license: Apache-2.0
license: CC-BY-4.0
license: Proprietary. See LICENSE.txt for terms.
```

**When to include:**
- Public or open-source skills
- Skills shared with your organization
- Skills distributed through skill repositories

#### `compatibility`
**Type:** String  
**Max:** 500 characters  
**Format:** Plain text describing requirements

Indicates environment requirements or constraints. Include this only if your skill has specific dependencies.

**Use for:**
- Required system packages (git, docker, jq)
- Python/Node/Go/Rust version requirements
- Network access needs
- API or library dependencies
- Product-specific requirements

**Examples:**
```yaml
compatibility: Designed for Claude Code (or similar products)

compatibility: Requires git, docker, and jq. Needs access to the internet.

compatibility: Requires Python 3.11+ and the pdfplumber library.

compatibility: Works with Terraform Cloud API (requires TFC_TOKEN environment variable).

compatibility: Requires access to GitHub API. GitHub CLI recommended for local use.
```

**When to omit:** If your skill has no special requirements, omit this field.

#### `metadata`
**Type:** Map (string keys → string values)  
**No required keys** — Define your own conventions

Custom key-value pairs for client-specific, organizational, or application-specific metadata. The specification does not mandate any particular keys.

**Common conventions:**
- `author` — Creator or team name
- `version` — Semantic version (e.g., "1.0.0")
- `category` — Skill type (e.g., "workflow", "document", "analysis")
- `mcp-server` — Primary MCP server dependency
- `last-updated` — ISO 8601 date
- `team` — Responsible team or group

**Example:**
```yaml
metadata:
  author: Your Organization
  version: "1.0.0"
  category: data-processing
  mcp-server: github
  last-updated: 2026-03-14
  team: platform-engineering
```

#### `allowed-tools`
**Type:** String (space-delimited list)  
**Status:** Experimental  
**Format:** `ToolName(pattern:pattern)` separated by spaces

Pre-approves tools the skill is allowed to execute. This is a forward-looking field for implementing capability-based access control.

**Example:**
```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

**Note:** Support varies between agent implementations. Do not rely on this for security in production systems.

## Complete Example

```yaml
---
name: customer-onboarding
description: Manages complete customer onboarding including account creation, payment setup, and welcome emails. Use when user says "onboard new customer", "set up subscription", or "create account".
license: Apache-2.0
compatibility: Requires PayFlow MCP server for payment processing.
metadata:
  author: Your Company
  version: "2.1.0"
  category: workflow
  mcp-server: payflow
  last-updated: 2026-03-14
  team: platform-engineering
allowed-tools: Bash(curl:*) Read Write
---

# Skill content goes here...
```

## Validation Rules

**Format Requirements:**
- ✓ Must start with `---` (three dashes on a line by itself)
- ✓ Must end with `---` (three dashes on a line by itself)
- ✓ Valid YAML syntax
- ✓ UTF-8 encoding

**Naming Requirements:**
- ✓ `name` follows kebab-case rules (no spaces, capitals, underscores)
- ✓ `name` matches parent directory name
- ✓ Filename is exactly `SKILL.md` (case-sensitive)

**Content Requirements:**
- ✓ Both required fields present (`name` and `description`)
- ✓ No forbidden characters (e.g., `<` or `>` in XML context)
- ✓ Description is non-empty and under 1024 characters

## Validation Tools

Use the `skills-ref` tool to validate frontmatter:

```bash
# Validate a skill
skills-ref validate path/to/skill

# View parsed properties
skills-ref read-properties path/to/skill

# Generate XML for agent prompt
skills-ref to-prompt path/to/skill
```

Installation (from [agentskills/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)):

```bash
pip install -e skills-ref/
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "Invalid frontmatter" | YAML syntax error | Check `---` delimiters, colons after field names |
| "Invalid name: contains uppercase" | Name formatting | Use kebab-case: `my-skill` not `MySkill` |
| "Name does not match directory" | Directory mismatch | Rename directory to match `name` field |
| "Skill won't upload" | Filename wrong | File must be exactly `SKILL.md` (case-sensitive) |
| "Skill doesn't activate" | Poor description | Add clearer trigger phrases; test with `skills-ref read-properties` |
| "Triggers too often" | Vague description | Be more specific; mention when NOT to use |

## Related Resources

- **[Official Specification](https://agentskills.io/specification)** — Complete reference
- **[Frontmatter Reference](./frontmatter.md)** — Detailed field explanations
- **[Best Practices](../how-to/best-practices.md)** — How-to guide for effective skills
- **[Optimizing Descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)** — Official guidance on description writing
