# Reference Documentation

Authoritative technical specifications for Agent Skills, aligned with the official [Agent Skills specification](https://agentskills.io/specification).

## Available References

### Core Format

- **[SKILL.md Frontmatter](./frontmatter.md)** — Complete reference of all frontmatter fields
  - `name` — Skill identifier (required, kebab-case)
  - `description` — What skill does and when to use (required)
  - `license` — License for the skill (optional)
  - `compatibility` — Environment requirements (optional)
  - `metadata` — Custom key-value pairs (optional)
  - `allowed-tools` — Pre-approved tools (optional, experimental)

- **[YAML Frontmatter Spec](./yaml-frontmatter.md)** — Detailed specifications and validation rules
  - Field constraints and patterns
  - Valid values and examples
  - Troubleshooting guide

### Structure & Organization

- **[Skill Structure & File Organization](./skill-locations.md)** — Standard directory layout
  - `SKILL.md` — Core instructions and metadata
  - `scripts/` — Executable code
  - `references/` — On-demand documentation
  - `assets/` — Templates, resources, and data files
  - Progressive disclosure strategy
  - File naming conventions

### Tooling

- **[skills-ref Validation Tool](./skills-ref-tooling.md)** — Command-line and Python API for validation
  - `skills-ref validate` — Check skill validity
  - `skills-ref read-properties` — Extract metadata (JSON)
  - `skills-ref to-prompt` — Generate agent XML
  - Python API usage
  - CI/CD integration examples

### Supporting Files

- **[Bundled Skills Reference](./bundled-skills.md)** — Pre-built skills in this repository
- **[URLs and Resources](./urls-and-resources.md)** — Links to official documentation and tools

## Quick Lookup

| I need to... | See |
|---|---|
| Check a frontmatter field | [SKILL.md Frontmatter](./frontmatter.md) |
| Understand field constraints | [YAML Frontmatter Spec](./yaml-frontmatter.md) |
| Organize my skill files | [Skill Structure](./skill-locations.md) |
| Validate my skill | [skills-ref Tool](./skills-ref-tooling.md) |
| Find an example skill | [Bundled Skills](./bundled-skills.md) |
| Find official docs | [URLs and Resources](./urls-and-resources.md) |

## When to Use Reference

Use reference documentation when you:
- **Need exact field specifications** — What constraints apply? What are valid values?
- **Want to look up a field name** — Is it `description` or `desc`?
- **Need validation rules** — When does a skill pass or fail validation?
- **Are checking all available options** — What can I put in `metadata`?
- **Setting up tooling** — How do I use `skills-ref`?

**Don't know what you're looking for?** Try [How-To Guides](../how-to/) for task-oriented instructions.

## Related Resources

- **[Official Specification](https://agentskills.io/specification)** — The authoritative spec maintained by Anthropic
- **[How-To Guides](../how-to/)** — Task-oriented instructions for accomplishing goals
- **[Explanations](../explanation/)** — Background and design rationale
- **[Troubleshooting](../troubleshooting/)** — Solutions for common problems
