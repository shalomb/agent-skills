# Reference: Skill Structure and File Organization

This document describes the standard directory structure for Agent Skills, aligned with the [official specification](https://agentskills.io/specification).

## Standard Skill Directory Structure

Every skill is a folder containing, at minimum, a `SKILL.md` file:

```
skill-name/
├── SKILL.md              # Required: metadata + instructions
├── scripts/              # Optional: executable code
├── references/           # Optional: detailed documentation
└── assets/               # Optional: templates, resources, data
```

### `SKILL.md` (Required)

The core skill file containing:
- **YAML frontmatter** — Metadata (`name`, `description`, `license`, etc.)
- **Markdown body** — Instructions, examples, guidance

**Rules:**
- File must be named exactly `SKILL.md` (case-sensitive)
- Must contain valid YAML frontmatter (between `---` delimiters)
- Markdown body has no format restrictions

**Example:**
```markdown
---
name: pdf-processing
description: Extract text and tables from PDFs. Use when working with PDF documents.
license: Apache-2.0
---

# PDF Processing

## When to use this skill

Use this skill when the user needs to work with PDF files, extract content, or manipulate PDF documents.

## How to extract text

Use the `pdfplumber` library for text extraction:

```python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

### `scripts/` (Optional)

Executable code that agents can run. Scripts should be self-contained and include helpful error messages.

**Best practices:**
- Use clear naming: `extract.py`, `validate.sh`, `deploy.js`
- Include shebang line for shell scripts: `#!/bin/bash`
- Document dependencies clearly
- Handle errors gracefully with informative messages
- Make scripts idempotent when possible

**Supported languages** depend on the agent implementation:
- Python (most common)
- Bash / Shell
- JavaScript / Node.js
- Go, Rust, etc. (implementation-dependent)

**Example structure:**
```
pdf-processing/
├── SKILL.md
└── scripts/
    ├── README.md              # Dependencies and usage
    ├── extract_text.py        # Text extraction
    ├── fill_forms.py          # Form filling
    └── merge_pdfs.py          # PDF merging
```

### `references/` (Optional)

Additional documentation loaded on-demand when agents need more context. Keep files focused and well-scoped.

**Common files:**
- `REFERENCE.md` — Detailed technical reference
- `API.md` — API specifications and endpoints
- `ERRORS.md` — Error reference and troubleshooting
- `EXAMPLES.md` — Extended examples and use cases
- `FORMS.md` — Form templates or structured data
- Domain-specific files (e.g., `finance.md`, `legal.md`)

**Why separate files?**
- Progressive disclosure — Load only what's needed
- Reduced context overhead — Less token usage
- Focused content — Each file has a clear purpose
- Better maintainability — Easier to update specific topics

**Example structure:**
```
pdf-processing/
├── SKILL.md
└── references/
    ├── API.md               # pdfplumber API reference
    ├── ERRORS.md            # Common error messages
    └── EXAMPLES.md          # Extended examples
```

**How agents use references:**
```markdown
For detailed API information, see [the API reference](references/API.md).

If you encounter errors, check [Error Reference](references/ERRORS.md).

For more examples, see [Extended Examples](references/EXAMPLES.md).
```

### `assets/` (Optional)

Static resources used by the skill:
- Templates (HTML, Markdown, configuration templates)
- Images (diagrams, screenshots, icons)
- Data files (lookup tables, schemas, sample data, fixtures)

**Example structure:**
```
customer-onboarding/
├── SKILL.md
└── assets/
    ├── welcome-email.html          # Email template
    ├── onboarding-checklist.md     # Template for users
    ├── images/
    │   ├── flow-diagram.png
    │   └── architecture.png
    └── config.json                 # Configuration template
```

## Progressive Disclosure Strategy

Skills are designed to load incrementally for efficiency:

### 1. Discovery Phase (~100 tokens)
Only `name` and `description` are loaded. Used for skill discovery and deciding whether to activate.

### 2. Activation Phase (< 5000 tokens recommended)
Full `SKILL.md` body loads into context when the skill is activated.

### 3. On-Demand Phase (as needed)
Referenced files load only when agents specifically request them.

**Example:**
```markdown
## How to extract text from scanned PDFs

For scanned documents, first try `pdfplumber`. If that doesn't work, see [Advanced OCR techniques](references/OCR.md).
```

In this pattern, the agent loads the OCR reference only if needed.

## File Naming Conventions

### SKILL.md Body Content
- Use clear section headings: `## Step 1`, `## How to...`, `## Troubleshooting`
- Include working examples (not pseudo-code)
- Keep the body under **500 lines** (< 5000 tokens)
- Move detailed reference material to `references/`

### Scripts
- Use descriptive names: `extract_text.py`, `validate_data.sh` (not `script1.py`)
- Use `.py` for Python, `.sh` for Bash, `.js` for JavaScript
- Make executable: `chmod +x script.sh`

### References
- Use UPPERCASE for main reference files: `API.md`, `ERRORS.md`
- Use lowercase for topic files: `finance-calculations.md`, `aws-regions.md`
- Keep files focused: one topic per file

### Assets
- Use lowercase with hyphens: `welcome-email.html`, `flow-diagram.png`
- Organize images in subdirectories: `assets/images/`, `assets/icons/`
- Use semantic names: `success-icon.svg` (not `icon1.svg`)

## File References in SKILL.md

When referencing files within your skill, use relative paths from the skill root:

```markdown
See [the API reference](references/API.md) for details.

Run the extraction script:
scripts/extract.py

Use the template in [assets/welcome-email.html](assets/welcome-email.html).
```

**Keep references one level deep** from `SKILL.md` to avoid confusing nested chains.

## Content Size Guidelines

Keep file sizes reasonable to manage context usage:

| File | Recommended Size | Rationale |
|------|------------------|-----------|
| `SKILL.md` body | < 500 lines / < 5000 tokens | Full load on activation |
| `scripts/*` | < 500 lines each | Execution overhead |
| `references/*.md` | < 200 lines / < 1500 tokens | On-demand loading |
| `assets/` | Any size | Static resources |

## Real-World Examples

### Example 1: PDF Processing Skill

```
pdf-processing/
├── SKILL.md                    # Core instructions
├── scripts/
│   ├── README.md               # Python 3.8+, pdfplumber
│   ├── extract_text.py         # Text extraction
│   ├── fill_forms.py           # PDF form filling
│   └── merge_pdfs.py           # Merge multiple PDFs
├── references/
│   ├── API.md                  # pdfplumber API reference
│   ├── ERRORS.md               # Common errors & fixes
│   └── EXAMPLES.md             # Extended use cases
└── assets/
    └── sample.pdf              # Sample for testing
```

### Example 2: Workflow Automation Skill

```
customer-onboarding/
├── SKILL.md                    # Onboarding workflow
├── scripts/
│   └── execute_workflow.py     # Orchestration logic
├── references/
│   ├── API.md                  # Service APIs (Stripe, etc.)
│   ├── ERRORS.md               # Error handling guide
│   └── FORMS.md                # Data form templates
└── assets/
    ├── welcome-email.html      # Email template
    ├── onboarding-checklist.md # User checklist
    └── images/
        └── flow-diagram.png    # Process flowchart
```

### Example 3: Code Review Skill

```
code-review/
├── SKILL.md                    # Review guidelines
├── scripts/
│   ├── analyze_code.py         # Code analysis
│   └── check_tests.py          # Test coverage check
├── references/
│   ├── CHECKLIST.md            # Review checklist
│   ├── PATTERNS.md             # Anti-patterns to catch
│   └── COMPANY-STANDARDS.md    # Internal standards
└── assets/
    └── style-guide.md          # Code style reference
```

## Validation

Use `skills-ref` to validate directory structure and frontmatter:

```bash
# Validate structure and frontmatter
skills-ref validate path/to/skill

# View parsed properties
skills-ref read-properties path/to/skill

# Generate prompt XML
skills-ref to-prompt path/to/skill
```

Validation checks:
- ✓ Directory name matches `name` field in frontmatter
- ✓ `SKILL.md` exists and contains valid YAML frontmatter
- ✓ Field names and values conform to specification
- ✓ No XML injection or security issues

## Best Practices

1. **Keep SKILL.md focused** — Cover core instructions; move details to `references/`
2. **Use progressive disclosure** — Load complexity on-demand, not upfront
3. **Semantic naming** — Name files clearly so agents know what's where
4. **Documentation first** — Write references that explain non-obvious patterns
5. **Self-contained scripts** — Scripts should work independently with clear error messages
6. **Template clarity** — Assets should be self-documenting

## Related Resources

- **[Official Specification](https://agentskills.io/specification)** — Complete format details
- **[SKILL.md Frontmatter](./frontmatter.md)** — Metadata field reference
- **[Best Practices](../how-to/best-practices.md)** — How-to guide
- **[skills-ref Reference Library](https://github.com/agentskills/agentskills/tree/main/skills-ref)** — Validation tooling
