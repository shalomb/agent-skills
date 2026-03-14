# AI Agent Guidance for Agent Skills Repository

This guide helps AI assistants (Claude Code, Pi, etc.) understand how to work with and contribute to this repository of specialized Agent Skills.

## Quick Navigation

**Starting with skills?** → Read [docs/explanation/core-principles.md](docs/explanation/core-principles.md)

**Building a new skill?** → Start with [docs/how-to/create-first-skill.md](docs/how-to/create-first-skill.md)

**Need reference details?** → Check [docs/reference/frontmatter.md](docs/reference/frontmatter.md)

**Troubleshooting?** → See [docs/troubleshooting/](docs/troubleshooting/)

## Using the Skill Creator Skill

When creating or updating skills in this repository, use the **official skill-creator skill** from Anthropic:

**Location**: https://github.com/anthropics/skills/tree/main/skills/skill-creator

**When to use it:**
- Creating a new skill from scratch
- Validating an existing skill against the specification
- Refining skill instructions and descriptions
- Iterating on skill design based on execution results

**How to use it:**
1. Load the skill-creator skill from the Anthropic repository
2. Provide the skill-creator with:
   - **Purpose**: What problem does this skill solve?
   - **Use cases**: Real examples of when agents should use it
   - **Context**: Domain expertise, code examples, templates (if available)
3. Follow skill-creator's step-by-step guidance
4. Validate the output using `skills-ref` tooling (see below)

**Key insight**: The skill-creator skill is designed to extract real expertise and create high-quality skills. Don't generate skills from thin air — feed it domain knowledge, examples, and your own hands-on experience.

## Key Documentation to Understand

### 1. Official Agent Skills Specification
**Link**: https://agentskills.io/specification

The authoritative format specification. This is your source of truth for:
- Frontmatter fields and constraints
- Directory structure requirements
- Validation rules
- Progressive disclosure strategy

### 2. Repository Documentation Structure

This repository follows the **Diataxis framework** with four sections:

#### [docs/how-to/](docs/how-to/) — Task-Oriented Guides
Start here when you have a concrete goal:
- [create-first-skill.md](docs/how-to/create-first-skill.md) — 15-30 minute walkthrough
- [structure-skill.md](docs/how-to/structure-skill.md) — Organizing SKILL.md and supporting files
- [add-supporting-files.md](docs/how-to/add-supporting-files.md) — Using scripts/, references/, assets/
- [best-practices.md](docs/how-to/best-practices.md) — Writing effective instructions and descriptions
- [implement-skills-support.md](docs/how-to/implement-skills-support.md) — Adding skills to agent platforms

#### [docs/reference/](docs/reference/) — Lookup & Specifications
Use when you need exact details:
- [frontmatter.md](docs/reference/frontmatter.md) — Complete field reference with examples
- [yaml-frontmatter.md](docs/reference/yaml-frontmatter.md) — Field constraints and validation rules
- [skill-locations.md](docs/reference/skill-locations.md) — Directory structure and file organization
- [skills-ref-tooling.md](docs/reference/skills-ref-tooling.md) — Validation tool usage (CLI + Python API)

#### [docs/explanation/](docs/explanation/) — Design Rationale
Read when you want to understand *why*:
- [core-principles.md](docs/explanation/core-principles.md) — Progressive disclosure, composability, portability
- [architecture-patterns.md](docs/explanation/architecture-patterns.md) — Three skill categories and how to choose

#### [docs/troubleshooting/](docs/troubleshooting/) — Problem Solutions
Check when something doesn't work:
- [common-issues.md](docs/troubleshooting/common-issues.md) — Typical problems and fixes

## Core Principle: Universal Applicability

The primary goal of this repository is to provide high-quality, reusable skills that work for anyone in any organization. When developing or updating skills, follow these standards:

### 1. Strip Sensitive Information

Before committing changes or new skills, ensure they are free of:
- **Hardcoded Credentials**: Tokens, passwords, API keys, secrets
- **Organization-Specific IDs**: AWS account numbers, internal project codes, resource IDs
- **Internal URLs**: Links to private wikis (Atlassian, Confluence), internal Git repos, private docs
- **Internal Personas**: References to specific employees, team names, managers
- **Proprietary Patterns**: Custom internal conventions not useful to outsiders

### 2. Use Generic Placeholders

Replace organization-specific values with clear placeholders:
- Use `{ORGANIZATION}` instead of company names (e.g., "Takeda")
- Use `{WORKSPACE_NAME}` instead of specific TFC workspace names
- Use `{RUN_ID}`, `{PLAN_ID}`, `{APPLY_ID}` for runtime variables
- Use example domains: `example.com`, `your-org.aws.com`
- Use `{ENV}` or `{ENVIRONMENT}` for staging/prod references

**Example before sanitization:**
```yaml
compatibility: Requires access to Takeda's Terraform Cloud workspace prod-us-east-1
```

**Example after sanitization:**
```yaml
compatibility: Requires Terraform Cloud API token and workspace name (set via {WORKSPACE_NAME})
```

### 3. Abstract Logic from Configuration

Design scripts and documentation to be configurable:
- **Scripts**: Read configuration from standard locations (env vars, config files) rather than hardcoding
- **Parameters**: Use command-line arguments or environment variables for all variable values
- **Documentation**: Show how to customize the skill for a different environment
- **Examples**: Use realistic but non-proprietary scenarios

**Example before abstraction:**
```python
# Bad: Hardcoded to specific organization
tfc_token = "glpat-abc123xyz..."
workspace = "takeda-prod-us-east-1"
```

**Example after abstraction:**
```python
# Good: Configurable via environment
import os
tfc_token = os.getenv("TFC_TOKEN")
workspace = os.getenv("TFC_WORKSPACE", "default")
```

### 4. Privacy-First Review Process

When syncing or copying a skill from a private environment to this public repository:

**Step 1: Sanitize**
- Audit every file: SKILL.md, scripts/, references/, assets/
- Remove all credentials, IDs, URLs, employee names
- Check for private documentation links
- Verify example data contains no real information

**Step 2: Generalize**
- Transform specific workflows into reusable patterns
- Replace internal tools with industry-standard equivalents
- Convert proprietary processes to general principles
- Ensure instructions work in different organizations

**Step 3: Verify**
- All links are public or use `{PLACEHOLDER}` syntax
- Examples use generic data (example.com, fictional scenarios)
- Environment setup instructions work standalone
- No references to internal systems remain

**Step 4: Document Requirements**
- Be clear about what users must provide
- Include setup instructions for non-obvious dependencies
- Explain how to adapt the skill to their environment

## Workflow: Creating a New Skill

### 1. Identify Real Expertise
- Start from a real task you or your team has done
- Document what you learned during execution
- Collect code examples, templates, edge cases
- Note decisions you made and why

### 2. Use skill-creator to Build
- Load the [skill-creator skill](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
- Provide your domain knowledge as context
- Follow its step-by-step guidance
- Iterate based on execution results

### 3. Sanitize for Public Use
- Review SKILL.md for sensitive information
- Check scripts/ for hardcoded values
- Verify references/ contains no private docs
- Test with placeholders, not real credentials

### 4. Validate Structure
```bash
# Install skills-ref (from agentskills/agentskills)
pip install -e ../agentskills/agentskills/skills-ref/

# Validate your skill
skills-ref validate ./my-skill

# View properties
skills-ref read-properties ./my-skill
```

### 5. Document & Commit
- Update [skills/README.md](skills/README.md) with skill listing
- Ensure directory structure follows spec:
  ```
  my-skill/
  ├── SKILL.md              # Required
  ├── scripts/              # Optional
  ├── references/           # Optional
  └── assets/               # Optional
  ```
- Follow commit message conventions
- Reference this guide in PR description if needed

## Contributing Guidelines for Agents

When adding or updating skills in this repository:

### Structure
- ✓ Every skill has `SKILL.md` with valid YAML frontmatter
- ✓ Follow directory structure: `skill-name/SKILL.md`
- ✓ `name` field matches directory name (kebab-case)
- ✓ `description` includes "Use when..." trigger conditions
- ✓ Keep SKILL.md body under 500 lines (< 5000 tokens)
- ✓ Move detailed content to `references/` for on-demand loading

### Content Quality
- ✓ Clear, step-by-step instructions (not vague guidance)
- ✓ Real examples that agents can follow
- ✓ Edge cases and error handling documented
- ✓ Links to relevant `references/` files when needed

### Privacy & Generalization
- ✓ No hardcoded credentials, API keys, or secrets
- ✓ No organization-specific IDs or internal URLs
- ✓ No employee names or internal team references
- ✓ Configuration via environment variables, not hardcoding
- ✓ Generic placeholders for organization-specific values
- ✓ Works for anyone, not tied to one org

### Validation & Testing
- ✓ Run `skills-ref validate` before committing
- ✓ Test skill descriptions trigger on realistic queries
- ✓ Verify scripts work with example inputs
- ✓ Check that progressive disclosure pattern is used

### Documentation
- ✓ Update skills/ README with new skill listing
- ✓ Link to official spec if field definitions are needed
- ✓ Include setup/configuration examples
- ✓ Document dependencies (Python version, libraries, etc.)

## Standards Alignment

This repository aligns with:
- **Official Agent Skills Specification**: https://agentskills.io/specification
- **Anthropic's Skill Creator**: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- **Diataxis Documentation Framework**: Progressive disclosure through how-to, reference, explanation, troubleshooting
- **Public Repository Standards**: Privacy-first, generalizable, reusable

---

**Responsibility**: Your adherence to these guidelines ensures this repository remains a valuable, safe resource for the community.

**Questions?** Check [docs/troubleshooting/](docs/troubleshooting/) or the official specification at https://agentskills.io
