# AI Agent Guidance for Pi Skills

This guide helps AI assistants (Pi, Claude, etc.) understand how to maintain, update, and contribute to this repository of specialized skills.

## Core Principle: Universal Applicability

The primary goal of this repository is to provide high-quality, reusable skills that can be used by anyone in any organization. When developing or updating skills, follow these privacy and generalization standards.

### 1. Strip Sensitive Information

Before committing any changes or new skills, ensure they are free of:
- **Hardcoded Credentials**: Tokens, passwords, API keys, or secrets.
- **Organization-Specific IDs**: AWS account numbers, APMS IDs, project codes, or internal resource names.
- **Internal URLs**: Links to private wikis (Atlassian, Confluence), internal Git repositories, or private documentation.
- **Internal Personas**: References to specific employees, team names, or internal managers.

### 2. Use Generic Placeholders

Replace organization-specific values with clear placeholders:
- Use `{ORG}` or `{ORGANIZATION}` instead of "Takeda".
- Use `{WORKSPACE}` or `{WORKSPACE_NAME}` instead of specific TFC workspace names.
- Use `{RUN_ID}`, `{PLAN_ID}`, or `{APPLY_ID}` for runtime variables.
- Use example domains like `example.com` or `your-org.aws.com`.

### 3. Abstract Logic from Configuration

Design scripts and documentation to be configurable:
- **Scripts**: Read tokens from standard locations (e.g., `~/.terraform.d/credentials.tfrc.json`) rather than hardcoding.
- **Parameters**: Use command-line arguments or environment variables for variable values.
- **Documentation**: Provide examples that show how to customize the skill for a different environment.

### 4. Privacy-First Review

When an agent is asked to "sync" or "copy" a skill from a private environment (like a specific client project) to this public repository, it must:
1. **Sanitize**: Audit every file (SKILL.md, scripts, examples) for private data.
2. **Generalize**: Transform specific workflows into generic patterns.
3. **Verify**: Double-check that all links and references are public-facing or correctly placeholder-ized.

## Contributing Guidelines for Agents

When you are tasked with adding a new skill to this repository:
- **Check for existing patterns**: Follow the structure of existing skills (`SKILL.md` + `scripts/`).
- **Update the Root README**: Add the new skill to the appropriate category in the main `README.md`.
- **Maintain Universal Compatibility**: Ensure the skill doesn't rely on private extensions or proprietary internal tools unless clearly documented as a prerequisite.

---

**Note**: This repository is intended for the public domain. Your adherence to these guidelines ensures the safety and utility of the tools provided here.
