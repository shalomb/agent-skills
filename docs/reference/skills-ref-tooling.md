# Reference: skills-ref Validation Tool

The `skills-ref` library provides command-line and Python API tools for validating skills against the official [Agent Skills specification](https://agentskills.io/specification).

## Installation

### macOS / Linux

Using pip:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e skills-ref/
```

Or using [uv](https://docs.astral.sh/uv/):
```bash
uv sync
source .venv/bin/activate
```

### Windows

Using pip (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e skills-ref/
```

Using pip (Command Prompt):
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e skills-ref/
```

Or using [uv](https://docs.astral.sh/uv/):
```powershell
uv sync
.venv\Scripts\Activate.ps1
```

After installation, the `skills-ref` command is available in your activated virtual environment.

## Command-Line Usage

### `validate` — Check Skill Validity

Validates a skill directory against the specification:

```bash
skills-ref validate path/to/skill
```

**Checks:**
- ✓ Directory name matches `name` field in frontmatter
- ✓ `SKILL.md` file exists and contains valid YAML frontmatter
- ✓ `name` field is valid kebab-case (1–64 characters, no uppercase or consecutive hyphens)
- ✓ `description` field is present and under 1024 characters
- ✓ Optional fields conform to specification (license, compatibility, metadata, allowed-tools)
- ✓ No forbidden characters or security issues

**Example:**
```bash
$ skills-ref validate ./pdf-processing
✓ pdf-processing is valid

$ skills-ref validate ./invalid-skill
✗ Error: Invalid skill name. Contains uppercase letters.
```

**Exit codes:**
- `0` — Skill is valid
- `1` — Validation failed

### `read-properties` — Extract Metadata

Reads skill metadata and outputs as JSON:

```bash
skills-ref read-properties path/to/skill
```

**Output format:**
```json
{
  "name": "pdf-processing",
  "description": "Extract text and tables from PDFs...",
  "license": "Apache-2.0",
  "compatibility": "Requires pdfplumber",
  "metadata": {
    "author": "Your Organization",
    "version": "1.0.0"
  }
}
```

**Use cases:**
- Integrating skill metadata into CI/CD pipelines
- Building skill registries or catalogs
- Automated skill discovery
- Documentation generation

### `to-prompt` — Generate Agent XML

Generates the suggested `<available_skills>` XML block for agent system prompts:

```bash
skills-ref to-prompt path/to/skill-a path/to/skill-b path/to/skill-c
```

**Output example:**
```xml
<available_skills>
<skill>
<name>
pdf-processing
</name>
<description>
Extract text and tables from PDFs, fill forms, and merge PDFs. Use when working with PDF documents.
</description>
<location>
/path/to/pdf-processing/SKILL.md
</location>
</skill>
<skill>
<name>
code-review
</name>
<description>
Analyzes code for quality issues and performance problems. Use when reviewing PRs or checking for bugs.
</description>
<location>
/path/to/code-review/SKILL.md
</location>
</skill>
</available_skills>
```

**Use in agent system prompt:**
```
Your system prompt here...

<available_skills>
[output from skills-ref to-prompt ...]
</available_skills>

You can use skills when relevant...
```

## Python API

### `validate()` — Validate a Skill

```python
from pathlib import Path
from skills_ref import validate

problems = validate(Path("my-skill"))

if problems:
    print("Validation errors:")
    for problem in problems:
        print(f"  - {problem}")
else:
    print("✓ Skill is valid")
```

### `read_properties()` — Extract Metadata

```python
from pathlib import Path
from skills_ref import read_properties

props = read_properties(Path("my-skill"))

print(f"Skill: {props.name}")
print(f"Description: {props.description}")
print(f"License: {props.license}")
if props.metadata:
    print(f"Author: {props.metadata.get('author', 'Unknown')}")
```

**Return type:** `SkillProperties` object with attributes:
- `name` (str)
- `description` (str)
- `license` (str | None)
- `compatibility` (str | None)
- `allowed_tools` (str | None)
- `metadata` (dict[str, str])

### `to_prompt()` — Generate XML

```python
from pathlib import Path
from skills_ref import to_prompt

skills = [
    Path("pdf-processing"),
    Path("code-review"),
    Path("data-analysis"),
]

xml = to_prompt(skills)
print(xml)
```

## CI/CD Integration

### GitHub Actions Example

Validate all skills in a repository:

```yaml
name: Validate Skills

on: [pull_request, push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install skills-ref
        run: |
          cd skills-ref
          pip install -e .
      
      - name: Validate all skills
        run: |
          for skill in skills/*/; do
            skills-ref validate "$skill"
          done
```

### Generate Skill Registry

```yaml
- name: Generate skill registry
  run: |
    skills-ref to-prompt skills/*/ > .docs/available_skills.xml
    git add .docs/available_skills.xml

- name: Update documentation
  run: |
    for skill in skills/*/; do
      skills-ref read-properties "$skill" > ".docs/$(basename $skill).json"
    done
    git add .docs/*.json
```

## Common Use Cases

### 1. Pre-commit Validation

Validate skills before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

skills-ref validate ./skills/* || exit 1
```

### 2. Documentation Generation

Generate skill listing for README:

```bash
skills-ref read-properties ./skills/* | \
  jq -r '.[] | "- **\(.name)**: \(.description)"' > SKILLS.md
```

### 3. Skill Registry

Build a searchable catalog:

```python
import json
from pathlib import Path
from skills_ref import read_properties

skills = {}
for skill_dir in Path("skills").iterdir():
    if skill_dir.is_dir():
        props = read_properties(skill_dir)
        skills[props.name] = props.to_dict()

with open("skill-registry.json", "w") as f:
    json.dump(skills, f, indent=2)
```

### 4. Skill Discoverability

Check descriptions for clarity:

```python
from pathlib import Path
from skills_ref import read_properties

for skill_dir in Path("skills").iterdir():
    if skill_dir.is_dir():
        props = read_properties(skill_dir)
        
        # Check for "Use when" phrase
        if "Use when" not in props.description:
            print(f"⚠️  {props.name}: Missing 'Use when' trigger phrase")
        
        # Check description length
        if len(props.description) < 50:
            print(f"⚠️  {props.name}: Description too short (< 50 chars)")
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: SKILL.md` | SKILL.md missing | Create SKILL.md with frontmatter |
| `Invalid skill name: contains uppercase` | Name formatting | Use kebab-case: `my-skill` |
| `Name does not match directory` | Directory mismatch | Rename directory to match `name` field |
| `Invalid YAML` | Frontmatter syntax | Check YAML syntax: colons, indentation, `---` delimiters |
| `Description too long` | Description > 1024 chars | Shorten description |
| `Command not found: skills-ref` | Not installed | Activate virtual environment, reinstall |

## Related Resources

- **[Official Specification](https://agentskills.io/specification)** — Complete format details
- **[skills-ref Repository](https://github.com/agentskills/agentskills/tree/main/skills-ref)** — Source code
- **[SKILL.md Frontmatter](./frontmatter.md)** — Metadata field reference
- **[Skill Structure](./skill-locations.md)** — Directory organization
