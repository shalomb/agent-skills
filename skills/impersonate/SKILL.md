---
name: impersonate
description: Find and assume roles from agent definitions in .github/agents/*.md files. Load agent context to guide specialized development workflows. Use when you need to discover and adopt specialized agent roles or personas.
---

# Agent Impersonation Skill

This skill allows you to discover and assume roles defined in a repository's `.github/agents/*.md` files, providing context-aware workflows and specialized expertise for agent-driven development.

## Usage Instructions

This skill requires you to parse project-specific agent definitions. **DO NOT GUESS AGENT ROLES OR WORKFLOWS.**

1. Whenever you are asked to impersonate an agent, or you need to find specialized agent definitions, you must first read the detailed reference documentation to understand the impersonation protocols:
   - Use the `read` tool to load `references/impersonate-reference.md`.
   
2. The reference file contains instructions for:
   - Discovering available agents in the `.github/agents/` directory.
   - Reading and extracting the role context, persona, and expertise.
   - Applying the agent-specific workflows, checklists, and quality standards to your current task.

3. Follow the protocol exactly as defined in the reference to ensure consistent behavior across different specialized agent roles.
