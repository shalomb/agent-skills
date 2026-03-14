---
name: justfile-assistant
description: Create well-formed justfiles with test ladder patterns, standard recipes (install, build, test, clean, lint, dev, docs), and Makefile compatibility wrappers. Detects project type and generates appropriate recipes for Node.js, Python, Rust, Go, Terraform, and generic projects. Use when creating or updating justfiles for any project type.
---

# Justfile Assistant

This skill helps you create well-formed, maintainable justfiles for any project. It handles the mechanical work of scaffolding justified recipes with standard patterns, test ladder implementations, and backward-compatible Makefile redirects.

## Quick Start

Invoke this skill in your project directory:

```bash
# From your project root, invoke the skill:
gh copilot workspace

# The skill will:
# 1. Detect your project type (Node.js, Python, Rust, Terraform, etc.)
# 2. Generate a contextual justfile with standard recipes
# 3. Create a Makefile that redirects to justfile targets
# 4. Walk you through customization
```

## What Gets Created

### 1. **justfile** (Main file)
A well-structured justfile with:
- Standard recipe categories (install, build, clean, test, lint, dev, docs)
- Test ladder pattern (fast feedback → detailed testing)
- Language-specific build/test commands
- Consistent formatting and documentation

### 2. **Makefile** (Backward compatibility)
A thin wrapper that redirects classic `make` commands to justfile equivalents:
```bash
make test    # → just test
make build   # → just build
make clean   # → just clean
```

Allows teams to transition gradually without breaking existing workflows.

## Standard Recipes

Every generated justfile includes these core recipes:

### Installation & Setup
- `just install` - Install all dependencies
- `just clean` - Remove build artifacts and cache
- `just setup` - One-time project setup (runs install)

### Build & Development
- `just build` - Build the project
- `just dev` - Run development server/watcher
- `just format` - Auto-format code
- `just lint` - Check code quality

### Testing (Test Ladder)
- `just test` - Run full test suite (graduated ladder)
- `just test-lint` - Fast: linting/type checks
- `just test-unit` - Unit tests only
- `just test-integration` - Integration tests
- `just test-e2e` - End-to-end tests

### Documentation
- `just help` - Display available commands
- `just docs` - Generate or view documentation

## Test Ladder Concept

The **test ladder** is a graduated testing strategy where `just test` orchestrates multiple focused test recipes in order of feedback speed:

```
just test (Master Orchestrator)
├─ just test-lint           ⚡ 1-2 seconds  (linting, type checks)
├─ just test-unit           🔋 ~10 seconds (unit tests)
├─ just test-integration    🔗 ~30 seconds (integration tests)
└─ just test-e2e            🌐 ~2 minutes  (full E2E tests)
```

**Benefits:**
- Developers get feedback on the fastest checks first (lint/format)
- CI/CD doesn't run slow E2E tests if linting fails
- Each rung stops on failure—no wasted time on subsequent tiers
- Encourages breaking test suites into focused, purposeful groups

## Project Type Detection & Customization

The skill auto-detects your project type and generates appropriate recipes:

| Project Type | Detection | Test Runner | Build Tool | Notes |
|---|---|---|---|---|
| **Node.js/JS** | `package.json` | jest/vitest/npm test | npm/yarn | TypeScript support |
| **Python** | `pyproject.toml` or `requirements.txt` | pytest | uv/pip | Virtual env aware |
| **Rust** | `Cargo.toml` | cargo test | cargo | clippy integration |
| **Go** | `go.mod` | go test | go | Built-in patterns |
| **Terraform** | `*.tf` files or `terraform/` dir | terraform validate | terraform | Plan/apply patterns |
| **Generic** | No recognized files | (TODO) | (TODO) | Minimal template |

After generation, customize recipes to match your actual commands.

## Customization Examples

### Add a custom recipe
```justfile
# ============================================================================
# CUSTOM RECIPES
# ============================================================================

publish:
    @echo "📦 Publishing to npm..."
    npm publish
```

### Override a test command
```justfile
test-unit:
    @echo "⚡ Running unit tests..."
    npm run test:unit -- --coverage --watch=false
```

### Add environment variables
```justfile
set env_var := "production"
set db_url := env("DATABASE_URL")

deploy:
    @echo "Deploying to $env_var..."
    DB_URL={{db_url}} ./deploy.sh
```

## Workflow: Generating a Justfile

### Step 1: Invoke the skill
```bash
# In your project root
cd /path/to/your/project
gh copilot workspace  # Activate skill context
```

### Step 2: Let the skill generate files
The skill runs:
```bash
python scripts/generate_justfile.py . --output justfile
```

This creates:
- `justfile` with project-specific recipes
- `Makefile` that redirects to justfile targets

### Step 3: Customize if needed
```bash
# Edit justfile to add/modify recipes
vim justfile

# Verify it works
just help       # List all recipes
just test       # Run the test ladder
just build      # Build the project
```

### Step 4: Commit to version control
```bash
git add justfile Makefile
git commit -m "Add justfile with test ladder and standard recipes"
```

## References

For detailed patterns, examples, and advanced justfile techniques, see:
- [`justfile-template.md`](justfile-template.md) - Full template reference with all patterns
- [`test-ladder-patterns.md`](test-ladder-patterns.md) - Test ladder implementation patterns
- [`makefile-wrapper.md`](makefile-wrapper.md) - Makefile redirect patterns

## Key Design Principles

1. **Auto-detection**: Scan project files to choose appropriate recipes
2. **Convention over configuration**: Standard recipe names everyone recognizes
3. **Test ladder first**: `test` is the master orchestrator, not a simple wrapper
4. **Stop on failure**: Test recipes fail fast—no cascading slow tests on lint failure
5. **Backward compatible**: Makefile redirects let teams use `make` if they prefer
6. **Self-documenting**: Section headers and recipe comments explain purpose
7. **Language-agnostic**: Works for any project type with sensible defaults

## Troubleshooting

**Q: My custom recipe isn't working**
A: Check your shell syntax. Justfile uses `bash -c` by default. Use `@just --list` to see if the recipe appears.

**Q: `just test` runs too slowly**
A: Review `test-e2e` recipe and move slow tests to a separate `just test-full` recipe. The default test ladder should complete in ~1 minute.

**Q: Makefile redirects don't work**
A: Ensure `just` is installed. The Makefile assumes `just` is available in PATH.

**Q: I have language-specific test setup**
A: Customize `test-unit`, `test-integration`, and `test-e2e` recipes with your specific test commands. See [`test-ladder-patterns.md`](test-ladder-patterns.md) for examples.

## See Also

- **just official docs**: https://github.com/casey/just
- **Task automation patterns**: The skill is modeled after best practices from large open-source projects
