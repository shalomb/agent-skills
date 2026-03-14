# Justfile Template Reference

This is the model justfile structure for the justfile-assistant skill. It demonstrates best practices for well-formed justfiles with standard recipes and test ladder patterns.

## Standard Recipe Categories

Every justfile should include these top-level recipe categories:

### 1. Installation & Setup
- `install` - Install all dependencies
- `clean` - Remove build artifacts and cache
- `setup` - One-time project setup

### 2. Build & Development
- `build` - Build the project
- `dev` - Run development server/watcher
- `format` - Auto-format code
- `lint` - Check code quality

### 3. Testing (Test Ladder)
- `test` - Run full test suite (graduated ladder, not a simple wrapper)
- `test-unit` - Unit tests only (fast)
- `test-integration` - Integration tests (medium speed)
- `test-e2e` - End-to-end tests (slower)
- `test-lint` - Linting checks

### 4. Documentation & Help
- `help` - Display available commands
- `docs` - Generate or view documentation

## Test Ladder Concept

The test ladder is a graduated testing strategy where `just test` coordinates multiple focused test recipes in order of execution time and feedback speed:

```
┌─────────────────────────────────────────────────────┐
│ just test (Master Orchestrator)                     │
├─────────────────────────────────────────────────────┤
│ 1. just test-lint      (fastest, instant feedback)  │
│ 2. just test-unit      (medium, unit tests)         │
│ 3. just test-integration (slower, integration tests)│
│ 4. just test-e2e       (slowest, full E2E)          │
└─────────────────────────────────────────────────────┘
```

Each rung stops on failure, allowing developers to fix fast-running tests before committing to slow tests.

## Makefile Wrapper Pattern

Create a dummy Makefile that redirects to justfile targets for backward compatibility:

```makefile
# This Makefile redirects all targets to justfile equivalents
# Modern projects use: just <target> instead of: make <target>

.PHONY: install build clean test lint dev help

install:
	@just install

build:
	@just build

clean:
	@just clean

test:
	@just test

lint:
	@just lint

dev:
	@just dev

help:
	@just help
```

This allows:
- `make test` → `just test`
- `make build` → `just build`
- etc.

## Example Full Justfile Structure

```justfile
# Comments describe purpose
# Top-level structure is self-documenting

set shell := ["bash", "-c"]

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
    @echo "Installing dependencies..."
    npm install

clean:
    @echo "Cleaning artifacts..."
    rm -rf dist/ build/ .coverage

setup: install
    @echo "Setup complete"

# ============================================================================
# BUILD & DEVELOPMENT
# ============================================================================

build:
    @echo "Building project..."
    npm run build

dev:
    @echo "Starting development server..."
    npm run dev

format:
    @echo "Formatting code..."
    prettier --write src/

lint:
    @echo "Linting code..."
    eslint src/

# ============================================================================
# TESTING - Test Ladder Pattern
# ============================================================================

# Master test orchestrator - graduated ladder, stops on first failure
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Fastest feedback - linting
test-lint:
    @echo "🔍 Running linting..."
    eslint src/

# Fast - unit tests
test-unit:
    @echo "⚡ Running unit tests..."
    npm run test:unit

# Medium speed - integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    npm run test:integration

# Slowest - end-to-end tests
test-e2e:
    @echo "🌐 Running E2E tests..."
    npm run test:e2e

# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

help:
    @echo "Available commands:"
    @just --list

docs:
    @echo "Generating documentation..."
    npm run docs
```

## Project Type Customization

The skill adapts these recipes based on project type:

| Project Type | Language | Build Tool | Test Runner | Notes |
|---|---|---|---|---|
| Node.js/JS | JavaScript | npm/yarn | jest/vitest | typescript support |
| Python | Python | pip/uv | pytest | virtual env handling |
| Rust | Rust | cargo | cargo test | clippy linting |
| Go | Go | go | go test | goreleaser builds |
| Terraform | HCL | terraform | custom/tflint | aws integration |
| Generic | Any | manual | manual | minimal templates |

## Key Design Principles

1. **Section Headers**: Use consistent comment blocks for visual organization
2. **Recipe Names**: Verb-based, kebab-case (e.g., `test-unit`, `build-prod`)
3. **Help Text**: Each recipe should have a comment explaining its purpose
4. **Gradual Complexity**: `test` is simple entry point, detailed recipes do the work
5. **Stop on Failure**: Test ladder recipes fail fast and don't continue on error
6. **Minimal Magic**: Keep recipes readable, avoid nested complexity
7. **Compatibility**: Always provide Makefile wrapper for users expecting make
