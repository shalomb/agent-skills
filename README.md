# Agent Skills: Build, Share, and Deploy AI Skills at Scale

A comprehensive framework for creating reusable AI skills that work across Claude.ai, Claude Code, and the API. Skills embed expertise, workflows, and best practices so Claude can accomplish complex tasks consistently.

**📚 New to skills?** Start with the [documentation system](docs/README.md) (Diataxis-framework organized).

**⚡ Already building?** Jump to [Create Your First Skill](docs/how-to/create-first-skill.md) (15-30 min).

## What Are Skills?

A skill is a folder containing:
- **SKILL.md** (required): Instructions in Markdown with YAML frontmatter
- **scripts/** (optional): Executable code (Python, Bash, etc.)
- **references/** (optional): Documentation and templates
- **assets/** (optional): Branding, icons, templates

### Three Core Principles

1. **Progressive Disclosure** — Load only what's needed, when it's needed
2. **Composability** — Skills work alongside each other without conflicts
3. **Portability** — Same skill works on Claude.ai, Code, and API

### Real-World Examples

**Pattern 1: Document & Asset Creation**
- Create polished documents, designs, code with consistent quality
- Example: `frontend-design` skill generates production-grade UI code

**Pattern 2: Workflow Automation**
- Orchestrate multi-step processes across services
- Example: `customer-onboarding` skill handles account → payment → welcome

**Pattern 3: MCP Enhancement**
- Add expertise on top of existing MCP server access
- Example: `sentry-code-review` skill analyzes errors with best practices

## Quick Start

### Build Your First Skill (15-30 minutes)

1. **Create the folder**
   ```bash
   mkdir my-skill && cd my-skill
   touch SKILL.md
   mkdir scripts references assets
   ```

2. **Write SKILL.md**
   ```yaml
   ---
   name: my-skill-name
   description: What it does. Use when user [trigger phrases].
   ---
   
   # My Skill
   
   ## Instructions
   
   ### Step 1: First Major Step
   [Clear explanation]
   
   ### Step 2: Second Major Step
   [Clear explanation]
   ```

3. **Test in Claude.ai**
   - Settings → Skills → Upload → Select SKILL.md
   - Ask Claude something that triggers your skill
   - Iterate based on feedback

4. **Deploy**
   - Push to GitHub
   - Share the folder
   - Use in Claude.ai, Code, or API

### Complete Tutorial
See **[How to Create Your First Skill](docs/how-to/create-first-skill.md)** for step-by-step guide with examples.

## Documentation Structure

All docs follow the **Diataxis framework** for clarity:

```
docs/
├── README.md                    ← Start here
├── how-to/                      (Task-focused, step-by-step)
│   ├── create-first-skill.md   ✅ Complete
│   ├── structure-skill.md       (In progress)
│   └── ...                      (5 more guides)
├── reference/                   (Technical specs, lookup)
│   ├── yaml-frontmatter.md     ✅ Complete
│   ├── skill-anatomy.md         (In progress)
│   └── ...                      (4 more specs)
├── explanation/                 (Conceptual, why)
│   ├── core-principles.md       ✅ Complete
│   ├── architecture-patterns.md ✅ Complete
│   └── ...                      (3 more explanations)
└── troubleshooting/             (Problems, solutions)
    └── ...                      (4 guides)
```

### Documentation by Learning Style

**I want to BUILD something**
→ [How-To Guides](docs/how-to/) — Step-by-step tasks

**I want to UNDERSTAND the design**
→ [Explanations](docs/explanation/) — Why skills work this way

**I need to LOOK UP something**
→ [Reference](docs/reference/) — Specifications and fields

**Something's BROKEN**
→ [Troubleshooting](docs/troubleshooting/) — Problems and solutions

## Features

### ✅ Works Everywhere
- Claude.ai (web interface)
- Claude Code (IDE integration)
- Claude API (programmatic)
- Same skill, no modifications needed

### ✅ Progressive Disclosure
- Frontmatter tells Claude when to load
- Full instructions load when relevant
- References load on-demand
- Minimal token usage

### ✅ Composability
- Multiple skills active simultaneously
- Skills inform each other
- No conflicts or interference
- Clear handoff patterns

### ✅ Production-Ready
- Error handling and recovery
- Validation at each step
- Real-world examples
- Measurement framework

## Real Skill Examples

### 1. Frontend Design Skill
Creates production-grade web components following brand guidelines.

```yaml
---
name: frontend-design
description: Creates responsive web components and designs. Use for building UI, pages, components, or design systems.
---
```

**Capabilities**:
- Generate HTML/CSS from requirements
- Follow brand style guides
- Validate accessibility (WCAG AA)
- Test responsive design

### 2. Customer Onboarding Skill
Automates multi-step account setup across services.

**Workflow**:
1. Create account
2. Setup payment method
3. Create subscription
4. Send welcome email

**Integrations**: Works with PayFlow, Stripe, Sendgrid via MCP

### 3. Code Review Skill
Analyzes GitHub PRs with Sentry error context.

**Capabilities**:
- Fetch PR details and affected code
- Cross-reference with Sentry errors
- Identify risky changes
- Provide targeted fixes

## Architecture Patterns

### Choose Your Pattern

| Pattern | Use Case | Example |
|---------|----------|---------|
| **Document Creation** | Polished output (docs, designs, code) | Frontend design, docx writer |
| **Workflow Automation** | Multi-step processes | Customer onboarding, project setup |
| **MCP Enhancement** | Expertise layer | Code review, compliance checker |

See **[Architecture Patterns](docs/explanation/architecture-patterns.md)** for detailed guide on each pattern.

## Key Files

### SKILL.md Format

```yaml
---
name: skill-name                    # kebab-case, matches folder
description: What it does. Use when [trigger phrases].
license: MIT                        # Optional
compatibility: Requires Python 3.10 # Optional
metadata:                           # Optional
  author: Your Name
  version: 1.0.0
---

# Skill Name

## Instructions
### Step 1: [Major Step]
...

## Examples
### [Real-world scenario]
...

## Error Handling
### [Common Error]
...
```

**Key Rules**:
- `name` must be kebab-case
- `description` must include trigger phrases
- Start with `---` and end with `---`
- Use standard Markdown below frontmatter

See **[YAML Frontmatter Spec](docs/reference/yaml-frontmatter.md)** for complete reference.

## Getting Help

### Common Questions

**Q: What's the difference between skills and MCP?**
A: MCP provides tool access (what Claude *can* do). Skills provide methodology (how Claude *should* do it). Together they're powerful.

**Q: Can I use Python in my skill?**
A: Yes! Put scripts in `scripts/` folder. They'll run in Claude Code and API (Code Execution Tool required).

**Q: How do I know my skill is working?**
A: Use the success criteria framework: Does it trigger when it should? Complete workflows without user correction? Produce consistent results?

**Q: Can skills call other skills?**
A: Not directly, but they can recommend each other or assume the other skill is available.

### Get More Help

- **[Common Issues](docs/troubleshooting/common-issues.md)** — Typical problems + fixes (coming soon)
- **[Antipatterns](docs/troubleshooting/antipatterns.md)** — What NOT to do (coming soon)
- **[Core Principles](docs/explanation/core-principles.md)** — Why skills work this way

## Distribution

### Share Your Skill

1. **Host on GitHub**
   - Public repo with skill folder
   - Clear README (separate from SKILL.md)
   - Example usage and screenshots

2. **Document in MCP Repo** (if MCP)
   - Link to skill GitHub repo
   - Explain why both together are valuable
   - Provide quick-start guide

3. **Use in Claude**
   - Upload to Claude.ai
   - Share folder with team
   - Deploy via API

## Integration with Harness IDP

This repository includes the **harness-idp skill** for Infrastructure as Code workflows:

- Provision Harness workspaces
- Execute pipelines
- Self-discover 1685 Harness APIs via OpenAPI spec
- Terraform Cloud integration

See **[harness-idp skill docs](skills/harness-idp/README.md)** for details.

## Contributing

### Share Your Skills
Build something useful? Share it:
- Create a GitHub repo for your skill
- Add the `agent-skills` topic
- Link in discussions/issues

### Improve Documentation
See issues tagged `documentation` — help us complete scaffolded guides.

### Report Issues
Found a bug or unclear docs? Open an issue with:
- What you were trying to do
- What happened
- What you expected

## Statistics

- **Total skills framework**: ✅ Production-ready
- **Documentation**: 4/20 sections complete (21%)
- **Example skills**: 3+ documented patterns
- **API coverage**: 1685 Harness endpoints discoverable
- **Time to first skill**: 15-30 minutes

## License

MIT — Use skills however you want. Share, modify, build on them.

## Learn More

- **[Agent Skills Documentation](docs/README.md)** — Full learning system
- **[Create Your First Skill](docs/how-to/create-first-skill.md)** — Tutorial (15-30 min)
- **[Architecture Patterns](docs/explanation/architecture-patterns.md)** — Choose your pattern
- **[API Reference](docs/reference/yaml-frontmatter.md)** — Field specifications

---

**Ready?** Start with **[Create Your First Skill](docs/how-to/create-first-skill.md)** or browse **[Documentation](docs/README.md)**.

**Questions?** Check **[Common Issues](docs/troubleshooting/common-issues.md)** or open an issue.

**Building something cool?** Share it! Tag with `agent-skills` on GitHub.
