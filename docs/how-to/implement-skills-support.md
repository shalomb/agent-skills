# How to Implement Skills Support in Your Agent

**Time estimate**: 30-60 minutes  
**Complexity**: Intermediate  
**Audience**: Developers building AI agents and IDEs

## Overview

This guide walks through adding Agent Skills support to an AI agent or development tool. It covers the full lifecycle: discovering skills, telling the model about them, loading their content into context, and keeping that content effective over time.

The core integration is the same regardless of your agent's architecture. The implementation details vary based on:
- **Where do skills live?** Local filesystem (user + project), remote registry, or bundled assets?
- **How does the model access content?** File-reading capability, dedicated tool, or programmatic injection?

## Core Principle: Progressive Disclosure

All skills-compatible agents follow a three-tier loading strategy:

| Tier | What's Loaded | When | Token Cost |
|------|--------------|------|-----------|
| **1. Catalog** | Name + description | Session start | ~50-100 tokens per skill |
| **2. Instructions** | Full SKILL.md body | When activated | < 5,000 tokens |
| **3. Resources** | Scripts, references, assets | On demand | Varies |

**Key insight**: The model sees the catalog from the start, so it knows what skills are available. When it decides a skill is relevant, it loads the full instructions. If those instructions reference supporting files, the model loads them individually as needed. 

Result: An agent with 20 installed skills doesn't pay the token cost of 20 full instruction sets upfront—only the ones actually used.

---

## Step 1: Discover Skills

At session startup, find all available skills and load their metadata.

### Where to Scan

Which directories depends on your agent's environment. Most scan at least two scopes:

| Scope | Path | Purpose |
|-------|------|---------|
| **Project** | `<project>/.agents/skills/` | Project-specific skills (cross-client) |
| **Project** | `<project>/.<your-client>/skills/` | Your client's native location |
| **User** | `~/.agents/skills/` | User-wide skills (cross-client) |
| **User** | `~/.<your-client>/skills/` | Your client's native location |

The `.agents/skills/` paths are a widely-adopted convention for cross-client interoperability. Skills installed by other compliant clients automatically become visible to yours, and vice versa.

Other scopes to consider:
- Ancestor directories up to git root (for monorepos)
- XDG config directories (`~/.config/agent-skills/`)
- User-configured paths
- Organization-wide deployments
- Agent-bundled skills (static assets)

### What to Scan For

Within each skills directory, look for subdirectories containing **exactly** `SKILL.md`:

```
~/.agents/skills/
├── pdf-processing/
│   ├── SKILL.md          ← discovered
│   └── scripts/
│       └── extract.py
├── data-analysis/
│   └── SKILL.md          ← discovered
└── README.md             ← ignored (not in subdirectory)
```

**Practical scanning rules**:
- Skip metadata directories: `.git/`, `node_modules/`, `.env`
- Optionally respect `.gitignore` to avoid build artifacts
- Set reasonable bounds: max depth 4-6 levels, max ~2000 directories
- Log warnings for malformed skill directories

### Handling Name Collisions

When two skills share the same name, apply deterministic precedence:
- **Across scopes**: Project-level skills override user-level skills
- **Within scope**: Either first-found or last-found (be consistent, log warnings)

### Trust Considerations

Project-level skills come from potentially untrusted repositories. Consider gating project-level skill loading on a trust check:
- Only load if the user marked the project as trusted
- Prevents untrusted repos from silently injecting instructions

### Cloud-Hosted and Sandboxed Agents

If your agent runs in a container/sandbox without filesystem access:

**Project-level skills**: Usually work—skills travel with the cloned repo  
**User/org-level skills**: Need external provisioning:
- Clone a configuration repository
- Accept skill URLs or packages through settings
- Let users upload via web UI

**Built-in skills**: Package as static assets in deployment artifact

Once skills reach the agent, the rest of the lifecycle (parsing, disclosure, activation) works identically.

---

## Step 2: Parse SKILL.md Files

For each discovered SKILL.md, extract metadata and body content.

### Frontmatter Extraction

Every SKILL.md has two parts:
1. **YAML frontmatter** between `---` delimiters
2. **Markdown body** after the closing `---`

**Parsing**:
```
1. Find opening --- at file start
2. Find closing --- after frontmatter
3. Parse YAML block between them
4. Extract name (required) + description (required) + optional fields
5. Everything after closing ---, trimmed = skill body
```

### Handling Malformed YAML

Skills authored for other clients may contain technically invalid YAML that their parsers accept. Most common issue: unquoted values with colons:

```yaml
# Technically invalid YAML
description: Use this skill when: the user asks about PDFs
```

**Workaround**: Fallback that wraps values in quotes or converts to block scalars before retrying. Improves cross-client compatibility at minimal cost.

### Lenient Validation

Warn on issues but still load the skill when possible:

| Issue | Action |
|-------|--------|
| Name doesn't match parent directory | Warn, load anyway |
| Name > 64 characters | Warn, load anyway |
| Description missing/empty | **Skip**, log error |
| YAML completely unparseable | **Skip**, log error |

Record diagnostics surfaced in debug commands, logs, or UI. Don't block on cosmetic issues.

The Agent Skills specification defines strict constraints on `name`. The lenient approach above deliberately relaxes these for compatibility with skills authored for other clients.

### What to Store

**Minimum fields per skill**:

| Field | Source |
|-------|--------|
| `name` | Frontmatter |
| `description` | Frontmatter |
| `location` | Absolute path to SKILL.md |

Store in an in-memory map keyed by `name` for fast lookup during activation.

**Optional**:
- **Store body**: Faster activation, higher memory
- **Read body at activation**: Lower memory, picks up file changes, flexible

**Derive on demand**:
- **Base directory** = parent of `location` path (needed later for resolving relative paths)

---

## Step 3: Disclose Available Skills to the Model

Tell the model what skills exist without loading full content. This is **tier 1** of progressive disclosure.

### Building the Skill Catalog

For each discovered skill, include `name`, `description`, and optionally `location` in structured format (XML, JSON, or list all work):

```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extract text and tables from PDFs. Fill forms, merge documents.</description>
    <location>/home/user/.agents/skills/pdf-processing/SKILL.md</location>
  </skill>
  <skill>
    <name>data-analysis</name>
    <description>Analyze datasets, generate charts, create summary reports.</description>
    <location>/home/user/project/.agents/skills/data-analysis/SKILL.md</location>
  </skill>
</available_skills>
```

**Token efficiency**: Each skill adds ~50-100 tokens. Even with 20+ skills, the catalog stays compact.

### Where to Place the Catalog

**Option 1: System Prompt Section**
- Add catalog as labeled section in system prompt
- Simplest approach
- Works with any model with file-reading tool

**Option 2: Tool Description**
- Embed in dedicated skill-activation tool description
- Keeps system prompt clean
- Couples discovery with activation

Both work. System prompt simpler; tool description cleaner.

### Behavioral Instructions

Include brief instructions telling the model how to use skills:

**If model activates by reading files**:
```
The following skills provide specialized instructions for specific tasks.
When a task matches a skill's description, use your file-read tool to load
the SKILL.md at the listed location before proceeding.
When a skill references relative paths, resolve them against the skill's
directory (the parent of SKILL.md) and use absolute paths in tool calls.
```

**If model activates via dedicated tool**:
```
The following skills provide specialized instructions for specific tasks.
When a task matches a skill's description, call the activate_skill tool
with the skill's name to load its full instructions.
```

Keep instructions concise. The goal: tell the model skills exist and how to load them. The skill content provides detailed instructions once loaded.

### Filtering

Exclude skills from the catalog for:
- User disabled the skill
- Permission system denies access
- Skill opted out of model-driven activation (via flag)

**Hide filtered skills entirely** rather than listing and blocking at activation. Prevents wasted model turns.

### When No Skills Are Available

If no skills discovered, **omit the catalog and instructions entirely**. Don't show empty `<available_skills/>` or register an empty skill tool—this confuses the model.

---

## Step 4: Activate Skills

When the model or user selects a skill, deliver full instructions into conversation context. This is **tier 2** of progressive disclosure.

### Model-Driven Activation

Most implementations rely on the model's own judgment. The model reads the catalog, decides a skill is relevant, and loads it.

**Two patterns**:

#### File-Read Activation
- Model calls standard file-read tool with SKILL.md path from catalog
- No special infrastructure needed
- Model receives file content as tool result
- Simplest when model has file access

#### Dedicated Tool Activation
- Register tool (e.g., `activate_skill`) taking skill name
- Returns content (optional YAML stripping)
- Advantages:
  - Control what content is returned
  - Wrap in structured tags for context management
  - List bundled resources alongside instructions
  - Enforce permissions or prompt for consent
  - Track activation for analytics

**Tip**: If using dedicated tool, constrain `name` parameter to valid skill names (enum in schema). Prevents hallucinated skill names. If no skills available, don't register the tool.

### User-Explicit Activation

Users should activate skills directly via slash command or mention syntax:
- `/skill-name` or `$skill-name`
- Harness intercepts and injects content
- Autocomplete widget makes this discoverable

### What the Model Receives

**Option A: Full file**
- Model sees entire SKILL.md including YAML frontmatter
- Natural outcome with file-read activation
- Frontmatter may contain useful fields (e.g., `compatibility`)

**Option B: Body only (frontmatter stripped)**
- Harness parses and removes YAML
- Returns only markdown instructions
- Most existing dedicated-tool implementations use this

Both work in practice. Choose based on your needs.

### Structured Wrapping

If using dedicated activation tool, consider wrapping content in identifying tags:

```xml
<skill_content name="pdf-processing">
# PDF Processing

## When to use this skill
Use this skill when the user needs to work with PDF files...

[rest of SKILL.md body]

Skill directory: /home/user/.agents/skills/pdf-processing
Relative paths in this skill are relative to the skill directory.

<skill_resources>
  <file>scripts/extract.py</file>
  <file>scripts/merge.py</file>
  <file>references/pdf-spec-summary.md</file>
</skill_resources>
</skill_content>
```

**Benefits**:
- Model clearly distinguishes skill instructions from conversation
- Harness identifies skill content during context compaction (Step 5)
- Bundled resources surfaced without eager loading

### Listing Bundled Resources

When activation tool returns skill content, enumerate supporting files (scripts, references, assets) in skill directory—but **don't eagerly read them**. Model loads specific files on demand using file-read tools when skill's instructions reference them.

For large directories, cap the listing and note it may be incomplete.

### Permission Allowlisting

If your agent gates file access with permissions, **allowlist skill directories** so the model reads bundled resources without confirmation prompts. Otherwise, every reference triggers a permission dialog and breaks flow.

---

## Step 5: Manage Skill Context Over Time

Once skill instructions are in conversation context, keep them effective for the session duration.

### Protect Skill Content From Context Compaction

If your agent truncates/summarizes older messages when context fills up, **exempt skill content from pruning**. Losing skill instructions mid-conversation silently degrades performance without visible error—the model continues but without specialized guidance.

**Common approaches**:
- Flag skill tool outputs as protected so pruning skips them
- Use structured tags from Step 4 to identify and preserve skill content

### Deduplicate Activations

Track which skills activated in current session. If model (or user) loads a skill already in context, skip re-injection to avoid duplicate instructions.

### Subagent Delegation (Optional)

Advanced pattern: instead of injecting into main conversation, run skill in separate subagent session:
1. Subagent receives skill instructions
2. Performs the task
3. Returns summary to main conversation

Useful when skill's workflow is complex enough to benefit from dedicated, focused session.

---

## Putting It All Together

**Minimal implementation**:
1. Scan `~/.agents/skills/` and `<project>/.agents/skills/`
2. Parse SKILL.md files (extract name, description, location)
3. Build skill catalog, add to system prompt
4. Let model read SKILL.md files directly using file-read tool
5. Protect skill content from context compaction

**Production implementation**:
- Scan all scopes (project, user, org, built-in)
- Dedicated skill-activation tool with structured wrapping
- Skill resource enumeration and permission allowlisting
- Deduplication and context management
- Trust checks for untrusted repositories

---

## See Also

- [Agent Skills Specification](https://agentskills.io/specification) — Complete SKILL.md format and constraints
- [Skill Anatomy Reference](../reference/skill-anatomy.md) — SKILL.md structure breakdown
- [Create Your First Skill](./create-first-skill.md) — For skill authors
- [Core Principles](../explanation/core-principles.md) — Why this design works

---

**Source**: [Agent Skills Documentation](https://agentskills.io/client-implementation/adding-skills-support)
