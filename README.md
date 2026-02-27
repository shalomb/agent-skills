# Pi Agent Skills

A collection of specialized skills for the [Pi coding agent](https://github.com/mariozechner/pi-coding-agent), enabling advanced workflows, automation, and domain-specific capabilities.

## Overview

Pi agent skills extend Pi's capabilities with specialized knowledge and workflows. Each skill is self-contained documentation that teaches Pi how to handle specific tasks or domains.

## Available Skills

### Quality & Testing

- **[adzic-index](skills/adzic-index/)** - Evaluate BDD feature files using the Adzic Index (Gojko Adzic's Specification by Example principles)
- **[farley-index](skills/farley-index/)** - Assess test suite quality using Dave Farley's Properties of Good Tests

### Development Agents (Springfield Pattern)

- **[bart](skills/bart/)** - Quality Agent persona (pessimistic, review-focused, bug-finding)
- **[lisa](skills/lisa/)** - Planning Agent persona (logical, architectural, task breakdown)
- **[marge](skills/marge/)** - Product Agent persona (empathetic, user-focused, requirements)
- **[ralph](skills/ralph/)** - Build Agent persona (optimistic, TDD-focused, implementation)
- **[lovejoy](skills/lovejoy/)** - Release Agent persona (ceremonial, shipping, communication)

### Document Automation

- **[docx](skills/docx/)** - Create and manipulate Word documents (.docx)
- **[pdf](skills/pdf/)** - Read, merge, split, fill forms, and manipulate PDFs
- **[pptx](skills/pptx/)** - Create and edit PowerPoint presentations
- **[xlsx](skills/xlsx/)** - Work with Excel spreadsheets and tabular data

### Infrastructure & DevOps

- **[tfc-api](skills/tfc-api/)** - Query Terraform Cloud workspaces, runs, plans, and logs
- **[terraform-dev](skills/terraform-dev/)** - Automated terraform development workflow with file watching
- **[tmux](skills/tmux/)** - Execute commands and monitor output in tmux panes

### Utilities

- **[copilot-cli](skills/copilot-cli/)** - Use GitHub Copilot CLI programmatically for code generation and analysis
- **[github-cli](skills/github-cli/)** - Leverage the GitHub CLI (gh) for repository operations
- **[humanizer](skills/humanizer/)** - Remove AI writing patterns to make text sound more natural
- **[impersonate](skills/impersonate/)** - Discover and assume roles from `.github/agents/` definitions

## Installation

### Method 1: Copy Individual Skills

Copy specific skills to your Pi skills directory:

```bash
# Copy a single skill
cp -r skills/adzic-index ~/.pi/agent/skills/

# Or copy all skills
cp -r skills/* ~/.pi/agent/skills/
```

### Method 2: Symlink

Create symlinks to keep skills updated:

```bash
# Clone the repo
git clone https://github.com/shalomb/agent-skills.git ~/agent-skills

# Symlink skills
ln -s ~/agent-skills/skills/* ~/.pi/agent/skills/
```

### Method 3: Git Submodule

Add as a submodule to your project:

```bash
git submodule add https://github.com/shalomb/agent-skills.git .pi/skills
```

## Usage

Once installed, skills are automatically discovered by Pi. Trigger them by mentioning relevant keywords in your prompts:

```bash
# Quality assessment
pi "Run the Adzic Index on my feature files"

# Development personas
pi "Bart, review this PR for bugs"
pi "Lisa, create an architecture diagram for this"

# Document creation
pi "Create a Word document with our meeting notes"

# Infrastructure
pi "Show me the latest Terraform Cloud run logs"
```

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md          # Main documentation (required)
├── scripts/          # Helper scripts (optional)
│   ├── script1.sh
│   └── script2.py
└── examples/         # Example files (optional)
    └── example.txt
```

The `SKILL.md` file contains:
- Trigger conditions (when to use the skill)
- Prerequisites and setup
- Usage patterns and examples
- Best practices
- Troubleshooting tips

## Creating Your Own Skills

### Basic Template

```markdown
# Skill Name

Brief description of what this skill does.

## Triggers

Use this skill when:
- User mentions "keyword1"
- User wants to accomplish X
- Task involves Y

## Prerequisites

- Tool X installed
- Configuration Y set up

## Usage

Basic usage patterns...

## Examples

Concrete examples...

## Best Practices

Tips and recommendations...
```

See the [Pi documentation on skills](https://github.com/mariozechner/pi-coding-agent/blob/main/docs/skills.md) for detailed guidance.

## Contributing

Contributions welcome! To add a new skill:

1. Fork this repository
2. Create a new directory under `skills/`
3. Add your `SKILL.md` (and optional scripts)
4. Test with Pi to ensure it triggers correctly
5. Submit a pull request

### Skill Guidelines

- **Self-contained**: Skills should document everything needed
- **Clear triggers**: Specify when the skill should activate
- **Practical examples**: Include real-world usage patterns
- **Tested**: Verify the skill works with Pi before submitting
- **Generic**: Avoid organization-specific references (use placeholders instead)

## Credits

### Skill Authors

- **adzic-index**, **farley-index**: BDD/TDD quality assessment frameworks
- **bart, lisa, marge, ralph, lovejoy**: Springfield agent personas for development workflows
- **humanizer**: Original skill by [@blader](https://github.com/blader/humanizer)
- **docx, pdf, pptx, xlsx**: Document automation skills
- **tfc-api, tmux, copilot-cli, github-cli**: DevOps and tooling integrations
- **impersonate**: Agent-driven development pattern

### Framework

Built for [Pi coding agent](https://github.com/mariozechner/pi-coding-agent) by Mario Zechner ([@badlogic](https://github.com/badlogic))

## License

Individual skills may have different licenses. Check each skill's directory for specific licensing information.

Skills without explicit licenses are provided under MIT License.

## Related Projects

- [Pi coding agent](https://github.com/mariozechner/pi-coding-agent) - The agent framework
- [Pi extensions](https://github.com/mariozechner/pi-coding-agent/tree/main/examples/extensions) - Custom Pi extensions
- [Aider](https://github.com/paul-gauthier/aider) - Alternative AI pair programming tool

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/shalomb/agent-skills/issues)
- **Discussions**: Share tips and ask questions in [Discussions](https://github.com/shalomb/agent-skills/discussions)
- **Pi Documentation**: See the [official Pi docs](https://github.com/mariozechner/pi-coding-agent/blob/main/README.md)
