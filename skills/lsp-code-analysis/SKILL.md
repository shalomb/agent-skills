---
name: lsp-code-analysis
description: >
  Semantic code analysis via LSP. Navigate code (definitions, references,
  implementations), search symbols, get file outlines, and safely rename
  symbols. Use when exploring unfamiliar codebases, tracing call chains, or
  performing structural code changes. Prefer over grep/read for any question
  about code structure. Supports Python, Rust, TypeScript/JS, Go, Java via
  language servers already installed by Mason.
---

# LSP Code Analysis

Compiler-accurate code navigation using language servers from Mason
(`~/.local/share/nvim/mason/bin`). No separate server installation.

## Setup (run once)

```bash
export PATH="$HOME/.local/share/nvim/mason/bin:$PATH"
bash scripts/lsp-setup.sh
```

Re-run after `uv tool upgrade lsp-cli`. The script is idempotent.

## Targeting syntax

Most commands take `FILE` then optional `--scope` and `--find`:

```
--scope MyClass                  # class by name
--scope MyClass.my_method        # method by dotted path  (most precise)
--scope 42                       # line number
--scope 10,50                    # line range
--scope MyClass.run --find "self.<|>logger"   # position within a symbol
```

The `<|>` marker pins the cursor to the character immediately to its right —
use it inside `--find` when multiple tokens are on the line and you need to
distinguish between them.

## Commands

All commands accept `--project DIR`. Without it the project root is inferred
by walking up for `pyproject.toml`, `Cargo.toml`, `go.mod`, `package.json`.

---

### `lsp outline` — file structure at a glance

Get the symbol tree without reading the file. Use this before `read`.

```bash
lsp outline src/models.py
lsp outline src/models.py --symbol MyClass      # narrow to one class
```

---

### `lsp definition` — jump to where a symbol is defined

```bash
lsp definition src/api.py --scope UserService.get_user
lsp definition src/api.py --scope 42 --find "<|>config"     # variable on line 42
lsp definition src/api.py --scope 42 --find "<|>user" --mode type_definition
```

Modes: `definition` (default), `declaration`, `type_definition`

---

### `lsp reference` — find all usages

```bash
lsp reference src/models.py --scope User
lsp reference src/models.py --scope User --max-items 50
```

> **Note**: `--mode implementations` requires the language server to support
> `textDocument/implementation`. pyright does not — use `references` mode and
> filter the results, or `search --kinds class` to find concrete subclasses.

---

### `lsp symbol` — full source of a symbol

Read a single function or class without opening the whole file.

```bash
lsp symbol src/models.py --scope User.validate
lsp symbol src/models.py --scope 15               # symbol containing line 15
```

---

### `lsp search` — workspace-wide symbol lookup

Use when you don't know which file a symbol is in.

```bash
lsp search "UserModel"
lsp search "validate" --kinds function --max-items 20
lsp search "Config"   --kinds class
```

Useful `--kinds` values: `function`, `method`, `class`, `interface`,
`variable`, `constant`, `module`.

---

### `lsp locate` — verify a target exists before acting

Check that a scope or find pattern resolves before running a heavier command.

```bash
lsp locate src/models.py --scope User.validate
lsp locate src/models.py --scope 42 --find "<|>process_data"
```

---

### `lsp rename` — safe workspace-wide rename

Always preview before executing.

```bash
# Step 1: preview — shows every file and line that will change
lsp rename preview src/models.py new_name --scope OldClassName

# Step 2: execute using the ID from the preview
lsp rename execute <rename_id>

# Exclude paths from the rename
lsp rename execute <rename_id> --exclude tests/ --exclude legacy/
```

**Never run `execute` without reviewing `preview` output first.**

---

## Exploration workflow

For an unfamiliar file or subsystem:

```bash
# 1. Map the structure — avoid reading the full file
lsp outline src/service.py

# 2. Get the contract of something interesting
lsp symbol src/service.py --scope UserService.process

# 3. Find where it's called from
lsp reference src/service.py --scope UserService.process

# 4. Jump to a dependency
lsp definition src/service.py --scope UserService.process --find "<|>validator"
```

## Tool selection

| Task | Skip | Use |
|------|------|-----|
| Find a function definition | `grep -r def foo` | `lsp search "foo" --kinds function` |
| Find all call sites | `grep -rn foo` | `lsp reference file --scope foo` |
| Understand a file | `read file` | `lsp outline file` |
| Read one method | `read file` | `lsp symbol file --scope Class.method` |
| Get type/docstring | `read file` | `lsp symbol file --scope symbol` |
| Rename across codebase | `sed -i` | `lsp rename preview` then `execute` |

## Performance

- First call: ~3s (manager + pyright start)
- Subsequent calls: ~2s (manager warm)
- Config at `~/.config/lsp-cli/config.toml`: `warmup_time=0`, `idle_timeout=30`

## Supported languages (via Mason)

| Language | Server |
|----------|--------|
| Python | `pyright-langserver` |
| Rust | `rust-analyzer` |
| TypeScript/JS | `typescript-language-server` |
| Go | `gopls` |

## What doesn't work (yet)

- `lsp doc` — not implemented in this version of lsp-cli; use `lsp symbol` instead
- `--mode implementations` with pyright — pyright doesn't support
  `textDocument/implementation`; use `lsp reference` or `lsp search --kinds class`
- Upstream bugs patched by `lsp-setup.sh` — see `references/upstream-patches.md`
