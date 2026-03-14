# Agent Skills Documentation

This directory contains comprehensive documentation for building, testing, and maintaining agent skills following the **Diataxis framework** and aligned with the official **Agent Skills specification** (https://agentskills.io).

## Documentation Structure

The documentation is organized into four sections aligned with the Diataxis framework:

### 📚 [How-To Guides](how-to/)
**Goal-oriented instructions for accomplishing specific tasks.** Start here if you have a concrete goal.

- [Create Your First Skill](how-to/create-first-skill.md) — Step-by-step walkthrough (15-30 min)
- [Structure a Skill](how-to/structure-skill.md) — Organizing SKILL.md, scripts/, references/, assets/
- [Add Supporting Files](how-to/add-supporting-files.md) — Using scripts, references, and assets effectively
- [Best Practices](how-to/best-practices.md) — Effective descriptions, content structure, error handling
- [Implement Skills Support](how-to/implement-skills-support.md) — Adding skills to your agent platform

### 🎯 [Reference](reference/)
**Authoritative technical specifications for looking up details.** Use when you know what you need and just need the specs.

- [SKILL.md Frontmatter](reference/frontmatter.md) — Complete reference of YAML frontmatter fields
  - `name` (required) — Kebab-case identifier, 1-64 characters
  - `description` (required) — What skill does and when to use it, max 1024 characters
  - `license` (optional) — License name or reference
  - `compatibility` (optional) — Environment requirements
  - `allowed-tools` (optional, experimental) — Pre-approved tool patterns
  - `metadata` (optional) — Custom key-value pairs
- [YAML Frontmatter Spec](reference/yaml-frontmatter.md) — Detailed field specifications and validation rules
- [Skill Directory Structure](reference/skill-locations.md) — Standard layout and file organization
- [Bundled Skills Reference](reference/bundled-skills.md) — Existing skills in this repository

### 💡 [Explanations](explanation/)
**Deep-dive background and theory.** Read when you want to understand the *why* behind decisions.

- [Core Principles](explanation/core-principles.md)
  - Progressive Disclosure — Load only what's needed, when needed
  - Composability — Skills work alongside each other without conflicts
  - Portability — Same skill works on Claude.ai, Claude Code, and API
- [Architecture Patterns](explanation/architecture-patterns.md) — Three skill categories:
  - Document & Asset Creation
  - Workflow Automation
  - MCP Enhancement (expertise layer on existing MCP servers)

### ⚡ [Troubleshooting](troubleshooting/)
**Solutions for common problems and error patterns.**

- [Common Issues](troubleshooting/common-issues.md) — Typical problems and fixes
- [Antipatterns](troubleshooting/antipatterns.md) — What NOT to do

## Quick Start by Learning Style

| I want to... | Start here |
|---|---|
| **BUILD something** | [How-To Guides](how-to/create-first-skill.md) — Step-by-step tasks |
| **UNDERSTAND the design** | [Explanations](explanation/core-principles.md) — Why skills work this way |
| **LOOK UP something** | [Reference](reference/frontmatter.md) — Specifications and fields |
| **FIX a problem** | [Troubleshooting](troubleshooting/common-issues.md) — Problems and solutions |

## Agent Skills Standard

This repository follows the **official Agent Skills specification** maintained by Anthropic. Key concepts:

### What is a skill?
A skill is a folder containing, at minimum, a `SKILL.md` file:

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code (Python, Bash, etc.)
├── references/       # Optional: documentation loaded on-demand
└── assets/           # Optional: templates, resources, data files
```

### Three Core Principles

1. **Progressive Disclosure** — Agents load only name/description at startup, full instructions when activated, referenced files on-demand
2. **Composability** — Multiple skills can work together without conflicts or interference
3. **Portability** — Same skill works unchanged on Claude.ai, Claude Code, and Claude API

### Validation Tooling

The official `skills-ref` library provides command-line and Python API tools:

```bash
# Validate a skill
skills-ref validate path/to/skill

# Read skill properties (JSON output)
skills-ref read-properties path/to/skill

# Generate <available_skills> XML for agent prompts
skills-ref to-prompt path/to/skill-a path/to/skill-b
```

See [Reference: Skill Locations](reference/skill-locations.md) for installation and usage details.

## Real-World Examples

### Category 1: Document & Asset Creation
Create polished documents, designs, and code with consistent quality.
- Example: `frontend-design` skill generates production-grade UI code
- Uses: embedded style guides, templates, quality validation

### Category 2: Workflow Automation
Orchestrate multi-step processes across services.
- Example: `customer-onboarding` skill handles account → payment → welcome sequence
- Uses: step-by-step workflows, validation gates, service integration

### Category 3: MCP Enhancement
Add expertise on top of existing MCP server access.
- Example: `sentry-code-review` skill analyzes PR errors with domain knowledge
- Uses: MCP calls + skill-embedded best practices

## Contributing

To contribute to this repository:

1. **Build effective skills** — Create skills that solve real problems
2. **Improve documentation** — Fix typos, clarify concepts, add examples
3. **Share patterns** — If you discover a useful skill pattern, document it
4. **Validate submissions** — Use `skills-ref validate` to check your work

See [AGENTS.md](../AGENTS.md) for guidelines on stripping sensitive information before public contribution.

## Getting Help

- **Need a specific field?** → [Reference: YAML Frontmatter](reference/frontmatter.md)
- **Want to understand design decisions?** → [Explanations](explanation/)
- **Stuck on a task?** → [How-To Guides](how-to/)
- **Something's broken?** → [Troubleshooting](troubleshooting/)

## Related Resources

- **Official Specification**: https://agentskills.io/specification
- **Reference Library (skills-ref)**: https://github.com/agentskills/agentskills/tree/main/skills-ref
- **Example Skills**: https://github.com/anthropics/skills
- **Agent Skills Homepage**: https://agentskills.io

---

**Last Updated**: 2026-03-14  
**Framework**: Diataxis + Agent Skills Specification  
**Aligned with**: https://agentskills.io (Agent Skills v1.0)
