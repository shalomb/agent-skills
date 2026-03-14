# Documentation Guide for Agent Skills Repository

This file provides a quick map of the documentation resources available to agents working with skills.

## For AI Agents Starting Here

**Start by reading**: [AGENTS.md](AGENTS.md)

This document provides:
- Quick navigation to common tasks
- Guidance on using the official skill-creator skill
- Standards and best practices for this repository
- Privacy and generalization guidelines
- Step-by-step workflow for creating skills

## Documentation by Task

### "I want to create a new skill"
1. **Read**: [AGENTS.md](AGENTS.md) — Overview and standards
2. **Understand**: [docs/explanation/core-principles.md](docs/explanation/core-principles.md) — Three core principles
3. **Choose**: [docs/explanation/architecture-patterns.md](docs/explanation/architecture-patterns.md) — Three skill patterns
4. **Build**: Use [skill-creator skill](https://github.com/anthropics/skills/tree/main/skills/skill-creator) from Anthropic
5. **Learn**: [docs/how-to/create-first-skill.md](docs/how-to/create-first-skill.md) — Step-by-step guide
6. **Reference**: [docs/reference/frontmatter.md](docs/reference/frontmatter.md) — Exact field specs
7. **Validate**: [docs/reference/skills-ref-tooling.md](docs/reference/skills-ref-tooling.md) — Validation tools
8. **Sanitize**: Review [AGENTS.md](AGENTS.md) privacy section

### "I want to understand the standard"
1. **Official Spec**: https://agentskills.io/specification (authoritative)
2. **This Repo**: [docs/explanation/README.md](docs/explanation/README.md) — Design rationale
3. **Principles**: [docs/explanation/core-principles.md](docs/explanation/core-principles.md) — Why it's designed this way
4. **Patterns**: [docs/explanation/architecture-patterns.md](docs/explanation/architecture-patterns.md) — Three skill categories

### "I need to look up a specific field"
→ [docs/reference/README.md](docs/reference/README.md) — Quick lookup table

**Key references:**
- [docs/reference/frontmatter.md](docs/reference/frontmatter.md) — Field explanations
- [docs/reference/yaml-frontmatter.md](docs/reference/yaml-frontmatter.md) — Detailed specs
- [docs/reference/skill-locations.md](docs/reference/skill-locations.md) — Directory structure

### "Something's not working"
→ [docs/troubleshooting/README.md](docs/troubleshooting/) — Problem solutions

### "I want to validate a skill"
→ [docs/reference/skills-ref-tooling.md](docs/reference/skills-ref-tooling.md)

Commands:
```bash
# Install
pip install -e ~/projects/agentskills/agentskills/skills-ref/

# Validate
skills-ref validate ./my-skill

# View properties
skills-ref read-properties ./my-skill

# Generate agent XML
skills-ref to-prompt ./my-skill
```

### "I want to understand privacy requirements"
→ [AGENTS.md](AGENTS.md) — Sections 1-4 cover:
- Stripping sensitive information
- Using generic placeholders
- Abstracting logic from configuration
- Privacy-first review process

## Documentation Structure

The documentation follows the **Diataxis framework** with four sections:

### 1. How-To Guides (`docs/how-to/`)
**Use when**: You have a concrete goal and need step-by-step instructions

- [create-first-skill.md](docs/how-to/create-first-skill.md) — 15-30 minute walkthrough
- [structure-skill.md](docs/how-to/structure-skill.md) — Organizing files
- [add-supporting-files.md](docs/how-to/add-supporting-files.md) — Scripts, references, assets
- [best-practices.md](docs/how-to/best-practices.md) — Writing effective skills
- [implement-skills-support.md](docs/how-to/implement-skills-support.md) — Integrating skills into platforms

### 2. Reference (`docs/reference/`)
**Use when**: You know what you need and just need the exact specs

- [frontmatter.md](docs/reference/frontmatter.md) — Complete field reference
- [yaml-frontmatter.md](docs/reference/yaml-frontmatter.md) — Detailed field specs
- [skill-locations.md](docs/reference/skill-locations.md) — Directory structure
- [skills-ref-tooling.md](docs/reference/skills-ref-tooling.md) — Validation tool reference

### 3. Explanations (`docs/explanation/`)
**Use when**: You want to understand the "why" behind decisions

- [core-principles.md](docs/explanation/core-principles.md) — Progressive disclosure, composability, portability
- [architecture-patterns.md](docs/explanation/architecture-patterns.md) — Three skill patterns

### 4. Troubleshooting (`docs/troubleshooting/`)
**Use when**: Something's not working as expected

- [common-issues.md](docs/troubleshooting/common-issues.md) — Typical problems and fixes

## Key Resources

### Official Standards
- **Agent Skills Specification**: https://agentskills.io/specification (authoritative)
- **Skill Creator Skill**: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- **skills-ref Tool**: https://github.com/agentskills/agentskills/tree/main/skills-ref

### This Repository
- **Main Documentation Hub**: [docs/README.md](docs/README.md)
- **Agent Guidance**: [AGENTS.md](AGENTS.md)
- **Reference Section**: [docs/reference/README.md](docs/reference/README.md)
- **Explanation Section**: [docs/explanation/README.md](docs/explanation/README.md)

## Quick Reference: Frontmatter Fields

**Required fields:**
- `name` — Skill identifier (kebab-case, 1-64 chars)
- `description` — What skill does, when to use (max 1024 chars, must include "Use when...")

**Optional fields:**
- `license` — License name (e.g., MIT, Apache-2.0)
- `compatibility` — Environment requirements
- `metadata` — Custom key-value pairs
- `allowed-tools` — Pre-approved tools (experimental)

See [docs/reference/frontmatter.md](docs/reference/frontmatter.md) for complete details.

## Standard Skill Structure

```
skill-name/
├── SKILL.md              # Required: metadata + instructions
├── scripts/              # Optional: executable code
├── references/           # Optional: detailed docs (loaded on-demand)
└── assets/               # Optional: templates, resources, data
```

See [docs/reference/skill-locations.md](docs/reference/skill-locations.md) for details.

## Contributing Checklist

Before committing a new or updated skill:

- [ ] Read [AGENTS.md](AGENTS.md) for standards
- [ ] Skill follows correct directory structure
- [ ] SKILL.md has valid frontmatter
  - [ ] `name` is kebab-case and matches directory
  - [ ] `description` includes "Use when..." trigger
  - [ ] Fields conform to specification
- [ ] Content is clear and follows best practices
  - [ ] Step-by-step instructions (not vague)
  - [ ] Real examples provided
  - [ ] Edge cases documented
- [ ] Privacy and generalization
  - [ ] No hardcoded credentials or secrets
  - [ ] No organization-specific IDs or URLs
  - [ ] No employee names or internal references
  - [ ] Configuration via environment variables
  - [ ] Generic placeholders for org-specific values
- [ ] Validated with tooling
  - [ ] Run: `skills-ref validate ./skill-name`
  - [ ] Run: `skills-ref read-properties ./skill-name`
- [ ] Documentation updated
  - [ ] Skills README updated with listing
  - [ ] SKILL.md references are correct
- [ ] Ready to commit
  - [ ] Commit message explains changes
  - [ ] PR references this guide if needed

## Recommended Workflow

### 1. Understand the Standards
```
Read: AGENTS.md → Official Spec → docs/explanation/
```

### 2. Choose Your Pattern
```
Read: docs/explanation/architecture-patterns.md
Decide: Document Creation? Workflow? MCP Enhancement?
```

### 3. Create Your Skill
```
Use: skill-creator skill from Anthropic
Follow: Its step-by-step guidance
Provide: Real expertise, examples, templates
```

### 4. Structure & Organize
```
Reference: docs/reference/skill-locations.md
Create: skill-name/ with SKILL.md + scripts/ + references/
```

### 5. Validate
```
Run: skills-ref validate ./skill-name
Check: All fields match specification
```

### 6. Sanitize
```
Review: AGENTS.md privacy section
Check: No secrets, IDs, URLs, or internal references
Generalize: Make it work for anyone
```

### 7. Document
```
Update: skills/ README
Verify: All links work
Test: Descriptions trigger correctly
```

### 8. Commit & Contribute
```
Follow: Commit message conventions
Reference: Contributing section of AGENTS.md
Ready: PR is ready for review
```

## For Agents: Key Principles to Remember

### 1. **Progressive Disclosure**
- Load only what's needed at each stage
- SKILL.md body loads on activation
- References load on-demand
- Keeps context and tokens efficient

### 2. **Composability**
- Skills work together, not in isolation
- Know when to recommend another skill
- Clear handoffs between skills
- No interfering instructions

### 3. **Portability**
- Same skill works on Claude.ai, Code, and API
- No platform-specific features
- Configuration via env vars, not hardcoding
- Works for anyone, anywhere

### 4. **Privacy & Generalization**
- Strip all sensitive information
- Use placeholders for org-specific values
- Make skills work universally
- Think about different organizations using this skill

### 5. **Real Expertise Over Generation**
- Extract from real tasks you've done
- Document what you learned
- Collect examples and edge cases
- Feed this to skill-creator for best results

## Getting Help

- **Questions about a field?** → [docs/reference/](docs/reference/)
- **Want to understand design?** → [docs/explanation/](docs/explanation/)
- **Stuck on a task?** → [docs/how-to/](docs/how-to/)
- **Something broken?** → [docs/troubleshooting/](docs/troubleshooting/)
- **Standards and requirements?** → [AGENTS.md](AGENTS.md)
- **Official specification?** → https://agentskills.io/specification

---

**Last Updated**: 2026-03-14  
**Aligned With**: Agent Skills Specification (https://agentskills.io)  
**Framework**: Diataxis (How-To, Reference, Explanation, Troubleshooting)
