---
name: lsp-code-analysis
description: >
  Semantic code analysis via LSP. Navigate code (definitions, references,
  implementations), search symbols, and get file outlines. Use for exploring
  unfamiliar codebases or tracing call chains. Prefer over grep/read for any
  structural code question. Supports Python, Rust, TypeScript/JS, Go, Java.
---

# LSP Code Analysis

Compiler-accurate code navigation using language servers already installed by
Mason (`~/.local/share/nvim/mason/bin`). No separate server installation needed.

## PREREQUISITE: Setup

Run once (and again after `uv tool upgrade lsp-cli`):

```bash
bash scripts/lsp-setup.sh
```

This installs `lsp-cli`, applies upstream bug fixes, and pins compatible
submodule versions. The setup script is idempotent.

Also ensure Mason's bin is on PATH in your shell session:

```bash
export PATH="$HOME/.local/share/nvim/mason/bin:$PATH"
```

## Commands

All commands accept `--project DIR` to set the project root explicitly.
Without it, the root is inferred by walking up for `pyproject.toml`, `Cargo.toml`, etc.

### Outline — file structure without reading the file

```bash
lsp outline <file>
lsp outline <file> --scope MyClass          # narrow to a symbol
```

### Definition — jump to where a symbol is defined

```bash
lsp definition <file> --scope MyClass.my_method
lsp definition <file> --scope 42 --find "<|>config"  # by line + pattern
```

### Reference — find all usages

```bash
lsp reference <file> --scope MyClass.my_method
lsp reference <file> --scope IUserService --mode implementations
```

### Symbol — full source of a symbol

```bash
lsp symbol <file> --scope MyClass.my_method
```

### Search — workspace-wide symbol lookup

```bash
lsp search "UserModel"
lsp search "validate" --kinds function --max-items 20
```

### Doc — docstring and type info

```bash
lsp doc <file> --scope my_function
```

## Tool Selection

Prefer LSP commands over text search for any structural question:

| Task | Instead of | Use |
|------|-----------|-----|
| Find definition | `grep -r` | `lsp definition` |
| Find all usages | `grep -rn` | `lsp reference` |
| Understand a file | `read file` | `lsp outline` |
| Understand an API | `read file` | `lsp doc` |
| Find a class/function | `grep -r` | `lsp search --kinds class` |

## Performance

- First call: ~3s (manager + pyright startup)
- Subsequent calls: ~2s (manager warm, pyright warm)
- Config: `~/.config/lsp-cli/config.toml` (`warmup_time=0`, `idle_timeout=30`)

## Supported Languages (via Mason)

| Language | Server |
|----------|--------|
| Python | `pyright-langserver` |
| Rust | `rust-analyzer` |
| TypeScript/JS | `typescript-language-server` |
| Go | `gopls` |

## Known Issues / Upstream Status

These are patched by `lsp-setup.sh` but not yet merged upstream:

1. **Manager murder-chain** (`lsp-cli` manager `__main__.py`): every `lsp`
   invocation spawns a new manager that kills the previous one → 15s per call.
   Fix: guard against starting a manager if one is already alive.

2. **`OutlineRequest` field rename** (`cli/outline.py`): `file_path` →
   `path` in newer `lsap-sdk`, but `lsp-cli@0.4.0` wasn't updated.

3. **pyrefly default** (`lsp-client/lang.py`): `lsp-client` main switched
   Python default to pyrefly, which exits immediately — use pyright instead.

4. **LSAP submodule pin**: `lsp-cli@0.4.0` requires LSAP API before the
   Symbol→Inspect rename (`bdd8d2c`). Setup pins to that commit.
