# How to Structure a Skill

**Time estimate**: 15 minutes  
**Skill level**: Beginner  
**Prerequisite**: Have created basic SKILL.md

## Overview

Learn the recommended folder layout and file organization patterns that make skills maintainable and portable.

*This guide is being written. See [Create your first skill](./create-first-skill.md) for the basics in the meantime.*

## Key Topics
- Folder naming conventions
- File organization best practices
- When to use scripts/ vs references/
- Asset management
- Cross-skill imports

## Quick Reference

```
skill-name/
├── SKILL.md                    # Required
├── scripts/                    # Optional
│   ├── __init__.py            # If Python package
│   ├── main.py                # Entry point
│   └── utils.py               # Helpers
├── references/                 # Optional
│   ├── api-guide.md           # External API docs
│   ├── templates/              # Template files
│   └── examples/               # Real examples
└── assets/                     # Optional
    ├── logo.png               # Branding
    └── style-guide.md         # Visual standards
```

---

**Status**: 🔄 In Progress - Complete version coming soon

**Related**: [Write effective instructions](./write-instructions.md) | [Reference: Skill anatomy](../reference/skill-anatomy.md)
