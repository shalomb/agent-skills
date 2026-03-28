# Agent Skills Collection

A personal collection of 27 reusable AI agent skills for various task domains. These skills follow the [Agent Skills specification](https://agentskills.io/specification) and work across multiple agent platforms.

**What are skills?** Extensions that teach AI agents specialized knowledge, workflows, and best practices. A skill is a folder containing a `SKILL.md` file (instructions + metadata) and optional supporting files (scripts, references, assets).

## Quick Start

### Install Skills to Your Agent

Choose your agent platform and copy skills to the appropriate directory:

**Claude Code**
```bash
# Copy individual skills to Claude Code directory
cp -r skills/pdf ~/.claude/skills/
cp -r skills/github-cli ~/.claude/skills/
cp -r skills/jira ~/.claude/skills/

# Or copy all skills at once
cp -r skills/* ~/.claude/skills/
```

**Copilot CLI**
```bash
cp -r skills/* ~/.copilot/skills/
```

**Pi (Anthropic's coding agent)**
```bash
cp -r skills/* ~/.pi/agent/skills/
```

**Kiro**
```bash
cp -r skills/* ~/.kiro/skills/
```

**Gemini Code Assist**
```bash
cp -r skills/* ~/.gemini/skills/
```

### Verify Installation

After copying skills, restart your agent and try triggering one:

```
# In Claude Code or other agent interface:
/pdf
# Then ask: "Extract text from this PDF"

/github-cli
# Then ask: "List all open PRs in this repo"
```

## Available Skills (27 total)

### Quality & Analysis
- **adzic-index** - Evaluate BDD/Gherkin feature file quality (Specification by Example)
- **farley-index** - Evaluate test suite quality (Dave Farley's properties)
- **lessons-learned** - Extract engineering lessons from recent code changes
- **pr-review** - Automated GitHub PR review and analysis

### Document Processing
- **pdf** - Extract text, merge, split, fill forms, OCR on PDFs
- **docx** - Create, read, edit Word documents
- **pptx** - Process PowerPoint presentations
- **xlsx** - Process spreadsheets (Excel, CSV, TSV)

### Development Tools
- **github-cli** - Query/manage GitHub repos, issues, PRs, workflows via `gh` CLI
- **copilot-sub-agent** - Launch GitHub Copilot CLI as a headless sub-agent with JSONL monitoring
- **gemini-sub-agent** - Launch Gemini CLI as a headless sub-agent with stream-json monitoring
- **claude-sub-agent** - Launch Claude Code CLI as a headless sub-agent with stream-json monitoring
- **terraform-dev** - Watch & validate Terraform files continuously
- **justfile-assistant** - Create well-formed justfiles with test patterns

### Infrastructure & Cloud
- **tfc-api** - Query Terraform Cloud workspaces, runs, plans, logs
- **harness-idp** - Execute Harness IDP templates and discover 1685+ APIs
- **c4-architecture** - Generate C4 model architecture diagrams

### Project Management
- **jira** - Query and manage Jira issues, projects, entities
- **targetprocess** - Query TargetProcess/Apptio work items

### Agent Personas
- **bart** (Quality Agent) - Pessimism, review, verification, bug-finding
- **lisa** (Planning Agent) - Logic, structure, architecture, task breakdown
- **lovejoy** (Release Agent) - Ceremony, shipping, learning, communication
- **marge** (Product Agent) - Empathy, user needs, product definition
- **ralph** (Build Agent) - TDD, optimism, implementation, code

### Utilities & Helpers
- **humanizer** - Remove AI writing patterns, make text sound natural
- **impersonate** - Discover and assume agent roles from `.github/agents/*.md`
- **tmux** - Execute commands in tmux panes
- **agent-md-refactor** - Refactor bloated agent instruction files
- **teams-transcript-processor** - Extract meeting minutes from Teams transcripts

## Testing Skills

### 1. Unit Test (SKILL.md Format)

Every skill's `SKILL.md` should validate:
```bash
# Using the official validator (requires skills-ref)
pip install git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref

skills-ref validate skills/pdf/
skills-ref validate skills/github-cli/
```

All skills in this repo pass validation ✓

### 2. Integration Test (Try the Skill)

Copy a skill to your agent directory and test it:

```bash
# For PDF skill
cp -r skills/pdf ~/.claude/skills/
# Then in Claude Code:
# /pdf
# "Extract text from document.pdf"

# For GitHub CLI skill
cp -r skills/github-cli ~/.claude/skills/
# Then in Claude Code:
# /github-cli
# "List all PRs in this repo with status"
```

### 3. Validation Checklist

Before using a skill, verify:
- [ ] Skill has proper `SKILL.md` with frontmatter (`name`, `description`)
- [ ] `description` includes "Use when..." trigger conditions
- [ ] Directory structure follows standard (SKILL.md + optional scripts/, references/, assets/)
- [ ] Scripts (if any) are executable and documented
- [ ] No hardcoded credentials or sensitive data

## Skill Structure

Each skill follows this standard structure:

```
skill-name/
├── SKILL.md              # Required: instructions + YAML frontmatter
├── scripts/              # Optional: executable code (Python, Bash, etc.)
│   ├── script1.py
│   └── README.md (if complex)
├── references/           # Optional: detailed docs (loaded on-demand)
│   ├── api-reference.md
│   ├── examples.md
│   └── troubleshooting.md
└── assets/               # Optional: templates, configs, images
    ├── template.html
    ├── config.json
    └── images/
```

**Progressive Disclosure Pattern**:
- `SKILL.md` frontmatter: ~100 tokens (discovery)
- `SKILL.md` body: < 5000 tokens (activation)
- `references/`: loaded only when needed

## Developing New Skills

For guidance on creating your own skills, see [AGENTS.md](AGENTS.md) and the documentation:

- **[How to Create Your First Skill](docs/how-to/create-first-skill.md)** - Step-by-step tutorial
- **[Best Practices](docs/how-to/best-practices.md)** - Writing effective skills
- **[Reference: SKILL.md Frontmatter](docs/reference/frontmatter.md)** - Field specifications
- **[Architecture Patterns](docs/explanation/architecture-patterns.md)** - Three skill design patterns

### Quick Example

Create a new skill:
```bash
mkdir skills/my-skill
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Does something useful. Use when you need to [specific task].
---

# My Skill

## What This Skill Does
[Explanation]

## How to Use It
1. [Step 1]
2. [Step 2]

## Examples
[Real examples]

## Error Handling
[Common issues and fixes]
EOF
```

Test it:
```bash
cp -r skills/my-skill ~/.claude/skills/
# Try it in Claude Code
```

## Documentation

- **[docs/README.md](docs/README.md)** - Documentation overview
- **[docs/how-to/](docs/how-to/)** - Task-oriented guides
- **[docs/reference/](docs/reference/)** - Technical specifications
- **[docs/explanation/](docs/explanation/)** - Design principles
- **[AGENTS.md](AGENTS.md)** - Guidelines for agents working with this repo

## Standards

This collection follows:
- [Agent Skills Specification](https://agentskills.io/specification)
- [Diataxis Documentation Framework](https://diataxis.fr/) (How-To, Reference, Explanation, Troubleshooting)
- Progressive Disclosure Pattern (load only what's needed, when needed)
- Clear trigger conditions in all skill descriptions

## License

MIT - Use, modify, share freely. See [LICENSE](LICENSE) for details.

## Contributing

Found a bug? Want to improve a skill? Have a new skill to add?

1. Check [AGENTS.md](AGENTS.md) for guidelines
2. Make changes and validate (see Testing section above)
3. Commit with clear messages
4. Push and create a PR

## References

- **[Official Agent Skills Specification](https://agentskills.io/specification)** - Format and standards
- **[Anthropic's Skill Creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)** - Tool for building skills
- **[skills-ref Validator](https://github.com/agentskills/agentskills/tree/main/skills-ref)** - Validation tool and CLI

---

**Want to use these skills?** Copy them to your agent's skills directory (see Quick Start above).

**Want to build your own?** Start with the [How to Create Your First Skill](docs/how-to/create-first-skill.md) guide.

**Questions?** Check the [documentation](docs/README.md) or [AGENTS.md](AGENTS.md).
