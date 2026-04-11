# How-to: Add Supporting Files to Skills

This guide shows how to organize supporting files alongside your skill's `SKILL.md` file.

## File Structure

Skills can include additional files in their directory:

```
~/.claude/skills/my-skill/
├── SKILL.md              # Required: Main skill definition
├── helper.py             # Optional: Supporting files
├── template.txt          # Optional: Templates or data files
└── docs/                 # Optional: Additional documentation
    └── examples.md
```

## Using Python Scripts

For Python scripts, leverage `uv` for speed, caching, and isolation:

### One-off Commands (`uvx`)
Use `uvx` directly in your `SKILL.md` for simple CLI tools. Always pin versions for reproducibility.
```bash
uvx ruff@0.8.0 check .
uvx black@24.10.0 .
```

### Complex Scripts (`uv run`)
For more complex domain logic, use dedicated Python scripts in the `scripts/` directory. Use PEP 723 inline metadata to declare dependencies so the script can be run standalone via `uv run`.

```python
# /// script
# dependencies = [
#   "httpx",
#   "rich",
# ]
# ///

import httpx
from rich import print
# ... script logic
```

Invoke this from `SKILL.md` via:
```bash
uv run scripts/my_script.py
```

**Note:** Always state in your `SKILL.md` that `uv` is a prerequisite if you use these patterns.

## Supported File Types

Skills can include:

- **Code files**: `.py`, `.js`, `.ts`, `.go`, `.rb`, `.java`, etc.
- **Data files**: `.json`, `.yaml`, `.csv`, `.txt`
- **Template files**: Any plain text format
- **Documentation**: Additional `.md` files for reference

## Using Supporting Files

### Reference in SKILL.md

You can reference supporting files in your skill's instructions:

```yaml
---
name: code-formatter
description: Formats code according to project style guide
---

Use the formatting rules in `style-guide.md` to format code.

For Python files, apply the rules in `python-rules.json`.
```

### File Paths

When Claude processes your skill, it has access to:
- Files in the skill directory
- File paths relative to the skill directory
- The content of referenced files

Example:

```yaml
---
name: code-generator
description: Generates boilerplate code from templates
---

Templates are available in the `templates/` directory.
Use template-react.jsx for React components.
```

## Best Practices

### 1. Organize by Purpose

```
~/.claude/skills/python-tester/
├── SKILL.md
├── pytest-config.ini
├── test-templates/
│   ├── unit-test.py
│   ├── integration-test.py
│   └── mock-setup.py
└── docs/
    └── testing-patterns.md
```

### 2. Include Clear Documentation

```yaml
---
name: documentation-generator
description: Generates project documentation from docstrings
---

See `docs/conventions.md` for our documentation style.

For examples, refer to `examples/` directory.
```

### 3. Keep Files Small

- Supporting files should be focused and concise
- Large files (>10KB) should be split into smaller modules
- Consider what Claude actually needs to reference

### 4. Version Supporting Files

If your skill depends on specific versions of templates or config:

```yaml
---
name: legacy-code-converter
description: Converts legacy Python 2 code to Python 3
notes: Uses Python 3.9 syntax conventions. See python39-rules.json
---
```

## Example: Complex Skill with Supporting Files

Here's a realistic example of a skill for generating test cases:

```
~/.claude/skills/test-case-generator/
├── SKILL.md
├── patterns.md           # Testing patterns guide
├── pytest-best-practices.md
├── templates/
│   ├── unit_test.py.template
│   ├── integration_test.py.template
│   └── fixture_setup.py.template
└── examples/
    ├── api_test_example.py
    └── database_test_example.py
```

**SKILL.md content:**

```yaml
---
name: test-case-generator
description: Generates comprehensive test cases for Python code
invocation_type: autonomous
---

## Test Generation Framework

Refer to `patterns.md` for recommended testing patterns.

## Setup

Use the fixtures defined in `templates/fixture_setup.py.template`.

## Examples

See `examples/` for real test case examples.

## Guidelines

- Follow pytest conventions from `pytest-best-practices.md`
- Use templates from `templates/` directory
- Ensure 80%+ code coverage
```

## Sharing Skills with Supporting Files

When sharing a skill, include the entire skill directory:

```bash
# Share the complete skill with all supporting files
cp -r ~/.claude/skills/my-skill ~/shared-skills/
```

The recipient should copy the entire directory to their `~/.claude/skills/` folder.
