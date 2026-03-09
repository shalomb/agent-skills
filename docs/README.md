# Agent Skills Documentation

This directory contains comprehensive documentation for building, testing, and maintaining agent skills following the **Diataxis framework**.

## Documentation Structure

The documentation is organized into four sections aligned with the Diataxis framework:

### 📚 [How-To Guides](how-to/)
Step-by-step instructions for accomplishing specific tasks. Start here if you have a concrete goal.

- [Create your first skill](how-to/create-first-skill.md) — 15-30 minute walkthrough
- [Structure a skill](how-to/structure-skill.md) — Folder layout and file organization
- [Write effective instructions](how-to/write-instructions.md) — Best practices for SKILL.md
- [Set up MCP integration](how-to/setup-mcp-integration.md) — Connect skills to MCP servers
- [Test and iterate](how-to/test-and-iterate.md) — Testing patterns and quality gates
- [Distribute your skill](how-to/distribute-skill.md) — Share with teams or communities

### 🎯 [Reference](reference/)
Authoritative information for looking up details. Use when you know what you need and just need the specs.

- [Skill anatomy](reference/skill-anatomy.md) — Complete breakdown of SKILL.md format
- [YAML frontmatter spec](reference/yaml-frontmatter.md) — All frontmatter fields and requirements
- [Directory structure](reference/directory-structure.md) — File organization standards
- [Success criteria](reference/success-criteria.md) — How to measure if your skill works
- [Checklist](reference/checklist.md) — Pre-launch validation checklist

### 💡 [Explanations](explanation/)
Deep-dive background and theory. Read when you want to understand the *why* behind decisions.

- [Core design principles](explanation/core-principles.md) — Progressive disclosure, composability, portability
- [Architecture patterns](explanation/architecture-patterns.md) — Three categories of skills (Document, Workflow, MCP Enhancement)
- [Use case design](explanation/use-case-design.md) — How to identify and define good use cases
- [MCP + Skills](explanation/mcp-plus-skills.md) — Kitchen analogy and integration patterns
- [Quality fundamentals](explanation/quality-fundamentals.md) — Why metrics matter

### ⚡ [Troubleshooting](troubleshooting/)
Solutions for common problems and error patterns.

- [Common issues](troubleshooting/common-issues.md) — Typical problems and fixes
- [Pattern antipatterns](troubleshooting/antipatterns.md) — What NOT to do
- [Debug guide](troubleshooting/debug-guide.md) — Troubleshooting workflows
- [Error messages](troubleshooting/error-reference.md) — Understanding error codes

## Quick Start

**First time?** Go to [Create your first skill](how-to/create-first-skill.md) (15-30 minutes)

**Want reference info?** Check [Skill anatomy](reference/skill-anatomy.md) for specifications

**Building MCP integration?** See [MCP + Skills](explanation/mcp-plus-skills.md) first

**Need to troubleshoot?** Check [Common issues](troubleshooting/common-issues.md)

## Key Concepts

### What is a skill?
A skill is a folder containing:
- **SKILL.md** (required): Instructions in Markdown with YAML frontmatter
- **scripts/** (optional): Executable code (Python, Bash, etc.)
- **references/** (optional): Documentation loaded as needed
- **assets/** (optional): Templates, fonts, icons used in output

### Three design principles
1. **Progressive Disclosure** — Load only what's needed, when it's needed
2. **Composability** — Works alongside other skills without conflicts
3. **Portability** — Same skill works on Claude.ai, Code, and API

### Two paths
- **Standalone skills**: Focus on Fundamentals and Planning/Design
- **MCP-enhanced skills**: Add knowledge layer on top of existing MCP server

## Real-World Examples

### Category 1: Document & Asset Creation
**Frontend Design Skill** — Create distinctive, production-grade interfaces
- Uses: embedded style guides, templates, quality checklists
- Tech: Claude's built-in artifact capabilities

### Category 2: Workflow Automation
**Skill Creator Skill** — Interactive guide for skill creation
- Uses: step-by-step workflows, validation gates, iterative refinement
- Tech: Multi-step prompts with feedback loops

### Category 3: MCP Enhancement
**Sentry Code Review Skill** — Analyzes GitHub PRs using Sentry's error monitoring
- Uses: coordinates multiple MCP calls, embeds domain expertise
- Tech: MCP server + skill knowledge layer

## Getting Help

- **Questions about specific features?** Check [Reference](reference/)
- **Want to understand design decisions?** Read [Explanations](explanation/)
- **Stuck on implementation?** See [How-To Guides](how-to/)
- **Something's broken?** Check [Troubleshooting](troubleshooting/)

## Contributing

Skills improve through community feedback. If you:
- Build an effective skill pattern
- Discover a new use case
- Find a solution to a common problem

Please consider sharing it. See individual sections for contribution guidelines.

---

**Last Updated**: 2026-03-09  
**Based on**: The Complete Guide to Building Skills for Claude  
**Framework**: Diataxis (How-To, Reference, Explanation, Troubleshooting)
