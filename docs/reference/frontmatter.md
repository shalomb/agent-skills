# Reference: SKILL.md Frontmatter

The `SKILL.md` file begins with YAML frontmatter that configures the skill's metadata. This reference aligns with the official [Agent Skills specification](https://agentskills.io/specification).

## Minimal Example

Every skill requires only two fields:

```yaml
---
name: skill-name
description: What this skill does and when to use it.
---
```

## Complete Example

```yaml
---
name: pdf-processing
description: Extract text and tables from PDFs, fill forms, and merge multiple PDFs. Use when working with PDF documents.
license: Apache-2.0
compatibility: Requires pdfplumber and pdf2image libraries
metadata:
  author: Your Organization
  version: "1.0.0"
allowed-tools: Bash(pdfplumber:*) Bash(pdf2image:*)
---
```

## Field Reference

### Required Fields

#### `name`
**Type:** String  
**Length:** 1–64 characters  
**Rules:**
- Lowercase letters (a–z), numbers (0–9), and hyphens (−) only
- Must not start or end with a hyphen
- Must not contain consecutive hyphens (−−)
- Must match the parent directory name

**Purpose:** Unique identifier for the skill. Used for discovery and invocation.

**Examples:**
```yaml
name: pdf-processing      ✓ Valid
name: data-analysis       ✓ Valid
name: code-review         ✓ Valid
name: PDF-Processing      ✗ Uppercase not allowed
name: -pdf                ✗ Cannot start with hyphen
name: pdf--processing     ✗ No consecutive hyphens
```

#### `description`
**Type:** String  
**Length:** 1–1024 characters  
**Purpose:** Describes what the skill does and when the agent should use it.

The description is critical for skill activation — agents use it to decide whether a skill is relevant to the current task.

**Best practices:**
- Be specific about what the skill does
- Include keywords agents can match against
- Describe both the capability and the trigger condition
- Include the phrase "Use when..." to clarify invocation

**Good example:**
```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

**Poor example:**
```yaml
description: Helps with PDFs.
```

### Optional Fields

#### `license`
**Type:** String  
**Length:** Up to 500 characters  
**Purpose:** Specifies the license under which the skill is shared.

**Examples:**
```yaml
license: Apache-2.0
license: MIT
license: Proprietary. See LICENSE.txt for complete terms
```

#### `compatibility`
**Type:** String  
**Length:** 1–500 characters  
**Purpose:** Indicates environment requirements or constraints.

Use this field to communicate:
- Required system packages (git, docker, jq)
- Minimum Python/Node/Go versions
- Network access requirements
- Intended product (Claude Code, Claude API, Claude.ai)
- API or library dependencies

**Examples:**
```yaml
compatibility: Designed for Claude Code (or similar products)
compatibility: Requires git, docker, jq, and access to the internet
compatibility: Requires Python 3.11+ and the requests library
compatibility: Works with Terraform Cloud API (requires TFC_TOKEN)
```

**Note:** Most skills do not need this field. Include it only when your skill has specific environmental constraints.

#### `metadata`
**Type:** Map (string keys → string values)  
**Purpose:** Custom key-value pairs for client-specific or application-specific properties.

The specification does not define required keys. Clients and organizations can define their own conventions.

**Examples:**
```yaml
metadata:
  author: Your Organization
  version: "1.0.0"
  category: "data-processing"
  team: "platform-eng"
```

#### `allowed-tools`
**Type:** String (space-delimited list)  
**Status:** Experimental  
**Purpose:** Pre-approves tools the skill may execute.

Format: `ToolName(pattern:subpattern)` separated by spaces. This is a forward-looking field for implementing capability-based access control in future agent implementations.

**Example:**
```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

**Note:** Support for this field varies between agent implementations. Do not rely on it for security in production systems.

## Body Content

The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions — write whatever helps agents perform the task effectively.

**Recommended sections:**
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases or error handling
- When to use vs. not use the skill

## Directory Structure

A skill is organized as:

```
skill-name/
├── SKILL.md              # Required: metadata + instructions
├── scripts/              # Optional: executable code
│   ├── script1.py
│   ├── script2.sh
│   └── README.md
├── references/           # Optional: detailed docs (loaded on-demand)
│   ├── API.md
│   ├── ERRORS.md
│   └── EXAMPLES.md
└── assets/               # Optional: templates, data files, images
    ├── template.html
    ├── config.json
    └── images/
```

### `scripts/` Directory

Executable code that agents can run. Scripts should:
- Be self-contained or clearly document dependencies
- Include helpful error messages
- Handle edge cases gracefully
- Be idempotent when possible

Supported languages depend on the agent implementation (commonly Python, Bash, JavaScript).

### `references/` Directory

Additional documentation loaded on-demand when agents need more context. Keep files focused:
- `REFERENCE.md` — Detailed technical reference
- `FORMS.md` — Form templates or structured data
- `API.md` — API specifications
- `ERRORS.md` — Error reference and troubleshooting
- Domain-specific files (e.g., `finance.md`, `legal.md`)

Reference files load only when needed, so smaller, focused files are more efficient than large documents.

### `assets/` Directory

Static resources:
- Templates (document, config, code templates)
- Images (diagrams, screenshots, examples)
- Data files (lookup tables, schemas, sample data)

## Progressive Disclosure

Skills are designed to load incrementally:

1. **Discovery (100 tokens)**: Only `name` and `description` loaded
2. **Activation (< 5000 tokens recommended)**: Full `SKILL.md` body loaded
3. **On-demand (as needed)**: Referenced files loaded when required

**Keep `SKILL.md` body lean, ideally under 100-350 lines.** Move detailed reference material to separate files in `references/` or `assets/`.

## File References

Reference other files within your skill using relative paths from the skill root:

```markdown
For detailed API information, see [the API reference](references/API.md).

To troubleshoot errors, check [Error Reference](references/ERRORS.md).

Run the extraction script:
```bash
./scripts/extract.py input.pdf
```
```

Keep references one level deep from `SKILL.md` to avoid deeply nested reference chains.

## Validation

Use the `skills-ref` tool to validate your frontmatter:

```bash
# Install (from agentskills/skills-ref)
pip install -e .

# Validate
skills-ref validate path/to/skill

# View properties
skills-ref read-properties path/to/skill

# Generate prompt XML
skills-ref to-prompt path/to/skill
```

Validation checks:
- ✓ `name` follows kebab-case rules
- ✓ `description` is non-empty and under 1024 characters
- ✓ Required fields are present
- ✓ Directory name matches skill name
- ✓ YAML syntax is valid

## Best Practices

1. **Specific Descriptions** — Include keywords and trigger conditions. Avoid vague language.
2. **Consistent Naming** — Use kebab-case, keep names short (2–4 words).
3. **Clear Scope** — Skills should cover one coherent unit of work.
4. **Moderate Content** — Focus on what agents *wouldn't* know without the skill.
5. **Progressive Disclosure** — Keep `SKILL.md` body concise; reference files for detailed content.

## Related Resources

- **[Official Specification](https://agentskills.io/specification)** — Complete format details
- **[skills-ref Reference Library](https://github.com/agentskills/agentskills/tree/main/skills-ref)** — Validation and tooling
- **[Best Practices for Skill Creators](https://agentskills.io/skill-creation/best-practices)** — Writing effective skills
- **[Optimizing Descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)** — How agents match skills to tasks
