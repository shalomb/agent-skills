# Tutorial: Create Your First Skill

**Time to complete: 10 minutes**

This tutorial guides you through creating a working skill from scratch. We'll build a skill that teaches Claude to explain code using visual diagrams and analogies.

## Prerequisites

- Claude Code installed and configured
- A text editor
- Basic understanding of Markdown

## Step 1: Create the skill directory

First, create a directory for your skill in your personal skills folder. Personal skills are available across all your projects.

```bash
mkdir -p ~/.claude/skills/explain-code
```

## Step 2: Write the SKILL.md file

Every skill needs a `SKILL.md` file with two parts:

1. **YAML frontmatter** (between `---` markers) - tells Claude when to use the skill
2. **Markdown content** - instructions Claude follows when the skill is invoked

Create `~/.claude/skills/explain-code/SKILL.md`:

```yaml
---
name: explain-code
description: Explains code with visual diagrams and analogies. Use when explaining how code works, teaching about a codebase, or when the user asks "how does this work?"
invocation_type: autonomous
---

## Code Explanation Framework

When explaining code, always include:

1. **Start with an analogy**: Compare the code to something from everyday life
2. **Draw a diagram**: Use ASCII art to show the flow, structure, or relationships
3. **Walk through the code**: Explain step-by-step what happens
4. **Highlight a gotcha**: What's a common mistake or misconception?

## Guidelines

- Keep explanations conversational
- For complex concepts, use multiple analogies
- Make diagrams clear and easy to follow
- Always explain the "why" behind the code
```

## Step 3: Test the skill

You can test your skill two ways:

### Method 1: Automatic invocation

Let Claude invoke it automatically by asking something that matches the description:

```
How does this Redux store work?
```

Claude will recognize the request matches your skill's description and invoke it automatically.

### Method 2: Direct invocation

Or invoke it directly using the slash command:

```
/explain-code Show me how authentication works in this app
```

## Step 4: Verify it works

You should see Claude:
1. Load your skill
2. Follow the framework you defined
3. Provide explanations with analogies and ASCII diagrams

## Next Steps

- Add supporting files to your skill (see [How-to: Add supporting files](../how-to/add-supporting-files.md))
- Learn about skill configuration (see [Reference: Frontmatter](../reference/frontmatter.md))
- Explore advanced patterns (see [How-to: Advanced patterns](../how-to/advanced-patterns.md))

## Troubleshooting

**Skill not appearing?**
- Check that the file is named exactly `SKILL.md`
- Verify the YAML frontmatter is properly formatted
- Ensure `~/.claude/skills/` directory exists

**Claude not invoking it automatically?**
- The `description` field needs to clearly describe when the skill should be used
- Try using `/explain-code` to invoke it directly
- Check that the skill directory structure is correct
