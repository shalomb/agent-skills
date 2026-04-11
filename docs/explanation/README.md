# Explanations

Deep-dive background and design theory. Read when you want to understand the *why* behind Agent Skills.

## Available Explanations

### Core Design

- **[Agent-Native CLI Design](./agent-native-cli-design.md)** — Principles for tools in 2026
  - **Machine-Interfacing Core** — JSON-first, deterministic exit codes, clean streams
  - **Advanced Agentic Patterns** — MCP support, predictive actions, plan-then-execute
  - **Efficiency & Safety** — Context window protection, dry run, idempotency

- **[Core Design Principles](./core-principles.md)** — Three foundational principles
  - **Progressive Disclosure** — Load only what's needed, when needed
  - **Composability** — Skills work alongside each other without conflicts
  - **Portability** — Same skill works unchanged on Claude.ai, Code, and API
  
  Understand why these principles make skills powerful and how they reduce token usage, improve UX, and enable ecosystem value.

- **[Architecture Patterns](./architecture-patterns.md)** — Three skill categories
  - **Pattern 1: Document & Asset Creation** — Polished output with consistent quality
  - **Pattern 2: Workflow Automation** — Multi-step processes across services
  - **Pattern 3: MCP Enhancement** — Expertise layer on existing MCP servers
  
  Learn how to recognize which pattern fits your use case and structure your skill accordingly.

## How to Use Explanations

Read explanations when you:
- **Want to understand design decisions** — Why are skills structured this way?
- **Need to make architectural choices** — Which pattern fits my use case?
- **Are designing from scratch** — What's the best approach for my skill?
- **Want to understand trade-offs** — Why this design vs. alternatives?
- **Are learning about skills** — How do they work conceptually?

**Looking for instructions instead?** → [How-To Guides](../how-to/)  
**Need specific details?** → [Reference](../reference/)

## The Three Principles Explained

### 1. Progressive Disclosure
Skills load in three phases:
1. **Discovery** (~100 tokens): Name and description only
2. **Activation** (< 5000 tokens): Full SKILL.md instructions
3. **On-demand** (as needed): Referenced files and resources

This keeps agents fast while providing expertise when needed. Unused skills don't cost tokens.

### 2. Composability
Multiple skills can work together:
- Skills should know about each other
- Clear handoffs when one skill should recommend another
- No interfering instructions or conflicts
- Each skill does one coherent unit of work

### 3. Portability
The same skill file works everywhere:
- Claude.ai (web)
- Claude Code (IDE)
- Claude API (programmatic)
- No modifications needed

## The Three Patterns Explained

### Pattern 1: Document & Asset Creation
**Best for:** Creating consistent, high-quality output

- Uses templates and style guides
- Focuses on output quality and consistency
- Examples: design-to-code, documentation generator, presentation builder
- Structure: SKILL.md + templates in references/

### Pattern 2: Workflow Automation
**Best for:** Multi-step processes across services

- Orchestrates multiple MCP servers
- Validates at each step
- Includes error handling and rollback
- Examples: customer onboarding, project setup, issue automation
- Structure: SKILL.md + scripts for validation logic

### Pattern 3: MCP Enhancement
**Best for:** Adding expertise on top of tool access

- Assumes MCP server already works
- Focuses on "how to use it well"
- Embeds domain knowledge and best practices
- Examples: code review with error context, compliance checking
- Structure: SKILL.md + domain logic in scripts/

## Related Resources

- **[Official Specification](https://agentskills.io/specification)** — Formal spec details
- **[How-To Guides](../how-to/)** — Task-oriented instructions
- **[Reference](../reference/)** — Technical specifications
- **[Troubleshooting](../troubleshooting/)** — Solutions for problems

## Next Steps

1. **Understand principles:** Read [Core Design Principles](./core-principles.md)
2. **Pick your pattern:** Review [Architecture Patterns](./architecture-patterns.md)
3. **Build your skill:** Go to [How-To Guides](../how-to/create-first-skill.md)
4. **Look up details:** Check [Reference](../reference/)
