---
name: obsidian-notetaker
description: >
  Find, create, edit, and update notes across personal Obsidian vault and agent
  operational memory using the deterministic non-interactive `ob-cli` tool.
  Manages TODO lists (checking off tasks, adding items), captures ideas and
  syntheses, commits changes with git, and syncs vault notes. Use when the user
  or agent asks to: take a note, capture an idea, update _todo.md, check off a task,
  find a note, add to Incoming.md, review TODOs, record agent operational memory,
  commit vault changes, or sync notes.
  Triggers on: 'obsidian', 'vault', 'take a note', 'capture an idea', 'jot
  down', 'add to inbox', '_todo', 'my todo list', 'sync vault', 'commit vault',
  'agent memory', 'ob-cli'.
---

# Obsidian Notetaker

## Environments & Tooling

Notes are managed deterministically using `ob-cli` without launching an interactive editor (`nvim`).

```bash
# Tier 1: Personal Obsidian Vault (enduring human + agent knowledge)
ob-cli --mode=obsidian ...
# Default path: /media/psf/Home/obsidian

# Tier 2: XDG Operational Memory (agent execution state & workstation quirks)
ob-cli --mode=memory ...
# Default path: ~/.local/state/pi-moe/memory
```

When targeting a specific custom root or writing tests, supply `--dir <path>`.

---

## Memory Admission Gate (Tier 1 vs. Tier 2 vs. Tier 3)

To avoid cluttering the human Obsidian vault or losing crucial execution context, adhere to the three-tier admission policy:

| Tier | Target Mode / Location | Retention Horizon | What Belongs Here | What DOES NOT Belong Here |
|---|---|---|---|---|
| **Tier 1** | `--mode=obsidian`<br>`/media/psf/Home/obsidian` | Months to Years | • Enduring human + agent knowledge<br>• Architectural syntheses & cross-project patterns<br>• Raw inbox capture in `Incoming.md`<br>• Personal/work action items in `_todo.md` and `Work/_todo.md`<br>• Curated domain reference guides | • Temporary session scratchpads<br>• Raw CLI debugging traces<br>• Workstation or tool-chain quirks<br>• Codebase backlog items (use Tier 3) |
| **Tier 2** | `--mode=memory`<br>`~/.local/state/pi-moe/memory` | Days to Months | • Operational agent context & receipts<br>• Host-specific workstation quirks & environment gotchas<br>• Skill execution friction logs (`skill-friction.md`)<br>• Cross-session delegate memories & run summaries | • High-level human knowledge base notes<br>• Permanent project architecture docs<br>• Repo task tracking |
| **Tier 3** | Codebase `TODO.md` / `docs/` | Codebase Lifetime | • Repo-specific implementation backlogs (use `todo` tool)<br>• Repo architectural guides & Diátaxis documentation (`docs/`) | • Personal vault notes<br>• Transient workstation-level agent memory |

---

## Non-Interactive `ob-cli` Command Reference

The Librarian agent executes `ob-cli` commands non-interactively using deterministic CLI flags.

### 1. Listing Notes

```bash
# List all files in Obsidian vault
ob-cli --mode=obsidian --list

# List all files in agent operational memory
ob-cli --mode=memory --list
```

### 2. Searching by Tag or Query (JSON & Tag Lists)

When searching notes programmatically, **always supply `--json`** with `--query` or `--tag` to avoid interactive `fzf` prompt invocation:

```bash
# Search notes matching a substring query as JSON array (MUST include --json)
ob-cli --mode=obsidian --query "vector index" --json
ob-cli --mode=memory --query "pi-moe" --json

# Search by tag as JSON array
ob-cli --mode=obsidian --tag architecture --json
ob-cli --mode=memory --tag delegate-receipt --json

# Plain-text file list matching a tag
ob-cli --mode=obsidian --tag architecture
```

The JSON array returns objects formatted as:
```json
[
  {
    "path": "Tech/AI/vector-index.md",
    "id": "542505f6",
    "tags": ["architecture", "ai"],
    "updated": "2026-10-24T20:51:45Z"
  }
]
```

### 3. Reading Note Content

Use `--cat` to output the exact note content with frontmatter to stdout without spawning nvim:

```bash
# Read a note from the vault
ob-cli --mode=obsidian --cat Tech/AI/vector-index.md

# Read an operational memory note
ob-cli --mode=memory --cat skill-friction.md
```

### 4. Capturing & Appending Notes

`ob-cli` automatically manages YAML frontmatter (`id`, `aliases`, `tags`, `created`, `modified`):

- **New Note Creation**: Passing `--capture`, `--tags`, and `--title` generates YAML frontmatter and initial markdown heading:
```bash
# Create a Tier 1 architectural note
ob-cli --mode=obsidian Tech/AI/hybrid-search.md \
  --title "Hybrid Search Architecture" \
  --tags "architecture,ai,search" \
  --capture "Combines sparse BM25 indexing with dense embedding retrieval."

# Create a Tier 2 memory note
ob-cli --mode=memory workstation-quirks.md \
  --title "Workstation Environment Quirks" \
  --tags "environment,quirks" \
  --capture "Parallels shared folder requires explicit file flushing before git commits."
```

- **Appending to an Existing Note**: Running capture against an existing note appends the text after a newline while updating the `modified` frontmatter timestamp:
```bash
ob-cli --mode=memory skill-friction.md \
  --capture "2026-10-24: ob-cli requires relative path arguments without leading slashes."
```

---

## Memory Grooming Guidelines

To prevent noise accumulation and maintain high retrieval precision:

1. **Deduplicate & Consolidate**:
   - Before capturing a new note, run `ob-cli --mode=<mode> --query "<keyword>" --json` to inspect existing entries.
   - If an existing note covers the topic, append new findings or edit the note rather than spawning a duplicate file.
2. **Resolve Contradictions**:
   - When new observations refute earlier notes, update the text to record the corrected truth. Do not leave stale contradictory notes unaddressed.
3. **Use Sharp Semantic Anchors**:
   - Always supply explicit `--tags` (e.g. `architecture,evals,harness`).
   - Use meaningful file paths (e.g. `Tech/AI/eval-framework.md` instead of `notes/note1.md`).
4. **Prune Stale Operational Memory**:
   - Tier 2 operational memories that represent solved one-off bugs or obsolete sessions should be consolidated into permanent patterns or removed.

---

## Vault TODO Lists & Inboxes

### Checking off a task in `_todo.md`
The vault has two main TODO files:
- `_todo.md` — personal todos
- `Work/_todo.md` — work todos

1. Preview task:
   ```bash
   ob-cli --mode=obsidian --cat _todo.md
   ```
2. Use the `edit` tool on `/media/psf/Home/obsidian/_todo.md` to change `- [ ] description` to `- [x] description`.

### Adding a task to `_todo.md`
Use the `edit` tool to insert `- [ ] new task` into `/media/psf/Home/obsidian/_todo.md` before the completed items section.

### Adding to Incoming.md
`/media/psf/Home/obsidian/Incoming.md` is the capture inbox for unprocessed resources and ideas.
Append new items under the relevant `##` section or at the top of `## 📚 Pending Resources`:
```bash
ob-cli --mode=obsidian Incoming.md --capture "- [ ] https://example.com/spec - High-speed vector index design"
```

---

## Committing & Syncing

For Tier 1 Obsidian Vault:

```bash
VAULT=/media/psf/Home/obsidian

# Check what's changed
git -C "$VAULT" status --short

# Stage and commit
git -C "$VAULT" add .
git -C "$VAULT" commit -m "docs: <description of changes>"

# Sync with remote
ob-cli --mode=obsidian --sync
```

**Commit message conventions:**
- New notes: `docs: add note - <title>`
- Edits: `docs: update <filename>`
- TODOs: `chore: update _todo.md`
- Bulk captures: `chore: capture inbox items`

