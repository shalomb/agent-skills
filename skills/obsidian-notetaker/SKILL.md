---
name: obsidian-notetaker
description: >
  Find, create, edit, and update notes in an Obsidian vault using the `ob` CLI
  and direct file operations. Manages TODO lists (checking off tasks, adding
  items), commits changes with git, and syncs the vault. Use when the user asks
  to: take a note, capture an idea, update _todo.md, check off a task, find a
  note, add to Incoming.md, review TODOs, commit vault changes, or sync the
  obsidian vault. Triggers on keywords like "note", "obsidian", "vault", "todo",
  "_todo", "capture", "jot down", "add to inbox", "ob ", "sync vault", or "commit
  notes".
---

# Obsidian Notetaker

## Environment

The Obsidian vault lives at `/media/psf/Home/obsidian/` (a macOS Parallels shared
folder). It is a git repository — commit and push changes when asked to save or sync.

```bash
VAULT=/media/psf/Home/obsidian
```

The `ob` CLI (`~/.config/bin/ob`) opens notes interactively in nvim. For
non-interactive agent use, operate directly on vault files with standard shell tools.

## Workflow Decision Tree

**Finding a note?** → Use `find` + `grep`/`rg` (see Finding Notes)  
**Creating a new note?** → Write file with frontmatter + commit (see Creating Notes)  
**Editing an existing note?** → Read → edit → commit (see Editing Notes)  
**Updating _todo.md?** → Read file, apply checkbox changes, write back (see TODOs)  
**Syncing/committing?** → See Committing & Syncing

---

## Finding Notes

```bash
VAULT=/media/psf/Home/obsidian

# List all notes
find "$VAULT" -name "*.md" -not -path "*/.git/*" | sort

# Fuzzy search by filename
find "$VAULT" -name "*keyword*" -not -path "*/.git/*"

# Full-text search
rg -l "search term" "$VAULT" --glob "*.md" --ignore-file <(echo ".git")

# Show matching lines with context
rg -n "search term" "$VAULT" --glob "*.md" -g "!.git"
```

## Creating Notes

New notes use YAML frontmatter. Match existing style:

```markdown
---
id: Note Title
aliases:
  - Note Title
tags:
  - tag1
  - tag2
created: 2026-03-27T10:00
---

# Note Title

Content here.
```

Create the file, then commit:

```bash
VAULT=/media/psf/Home/obsidian

# Create parent dirs if needed
mkdir -p "$VAULT/Tech/AI"

# Write note (use write tool or heredoc)
# Then commit
git -C "$VAULT" add .
git -C "$VAULT" commit -m "docs: add note - Note Title"
```

**Naming:** Use descriptive kebab-case filenames or natural names matching the `id` field.  
**Location:** Match the topic to existing vault folders (Tech/, Takeda/, notes/, ideas/, etc).

## Editing Notes

1. Read the file with the `read` tool.
2. Make edits with the `edit` tool (preserve frontmatter exactly).
3. Update `modified:` timestamp in frontmatter if it exists.
4. Commit.

## TODO Lists

The vault has two main TODO files:
- `$VAULT/_todo.md` — personal todos
- `$VAULT/Takeda/_todo.md` — work todos

### Checking off a task

Find the line, change `- [ ]` to `- [x]`:

```bash
# Preview the task
grep -n "task description" /media/psf/Home/obsidian/_todo.md
```

Then use the `edit` tool to change `- [ ] task description` → `- [x] task description`.

### Adding a task

Append to the active task list (before the `- [x]` completed section):

```bash
# Check current structure
grep -n "^\- \[" /media/psf/Home/obsidian/_todo.md | head -20
```

Use the `edit` tool to insert `- [ ] new task` at the right position.

### Adding to Incoming.md

`$VAULT/Incoming.md` is the capture inbox for unprocessed resources and ideas.
Append new items under the relevant `##` section or at the top of `## 📚 Pending Resources`.

## Committing & Syncing

```bash
VAULT=/media/psf/Home/obsidian

# Check what's changed
git -C "$VAULT" status --short

# Stage and commit
git -C "$VAULT" add .
git -C "$VAULT" commit -m "docs: <description of changes>"

# Sync (pull then push)
git -C "$VAULT" pull --rebase && git -C "$VAULT" push
```

**Commit message conventions:**
- New notes: `docs: add note - <title>`
- Edits: `docs: update <filename>`
- TODOs: `chore: update _todo.md`
- Bulk captures: `chore: capture inbox items`
- Auto-style WIP: `WIP: <description>`

## Vault Structure

```
obsidian/
├── _todo.md          Personal TODO list
├── Incoming.md       Capture inbox (unprocessed resources)
├── Agile/            Agile / lean engineering notes
├── Books/            Book notes
├── DevOps/           DevOps topics
├── ideas/            Speculative / brainstorming notes
├── notes/
│   ├── dailies/      Daily notes
│   ├── meetings/     Meeting notes
│   └── weeks/        Weekly reviews
├── Personal/         Personal notes (non-Takeda)
├── Projects/         Project notes
├── Scratch/          Scratch / drafts
├── Takeda/           Work notes
│   └── _todo.md      Work TODO list
└── Tech/             Technology notes
    └── AI/           AI-specific notes
```
