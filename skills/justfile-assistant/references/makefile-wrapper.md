# Makefile Wrapper Pattern

The Makefile wrapper redirects classic `make` commands to justfile targets, allowing teams to transition gradually from make to just without breaking existing workflows.

## Why a Makefile Wrapper?

1. **Backward Compatibility**: Teams can continue using `make` while adopting `just`
2. **Zero Friction Migration**: No need to force everyone to learn `just` syntax immediately
3. **Dual Support**: Both `make build` and `just build` work identically
4. **CI/CD Compatibility**: Existing CI/CD systems expecting Makefiles continue to work

## Standard Wrapper Pattern

```makefile
# Makefile: Redirect all targets to justfile
# Use 'make <target>' for legacy workflows, or 'just <target>' directly

.PHONY: install build clean test lint dev help setup format docs

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

setup:
	@just setup

format:
	@just format

docs:
	@just docs

help:
	@just help
```

## Key Elements

### `.PHONY` Declaration
```makefile
.PHONY: install build clean test lint dev help setup format docs
```
Tells `make` these are not files, so it always executes them regardless of filesystem state.

### Silent Recipe Prefix (`@`)
```makefile
install:
	@just install
```
The `@` suppresses the command echo, keeping output clean. The `just` command provides its own output.

### Tab Indentation (Critical!)
```makefile
target:
[TAB]@just target  # This MUST be a tab, not spaces
```
Makefiles require tabs. Many editors convert tabs to spaces—configure yours to preserve tabs.

## Extended Wrapper with Test Ladder

```makefile
# Makefile: Redirect all targets to justfile
# Includes test ladder targets

.PHONY: install build clean test lint dev help setup format docs
.PHONY: test-lint test-unit test-integration test-e2e

# ============================================================================
# CORE TARGETS
# ============================================================================

install:
	@just install

build:
	@just build

clean:
	@just clean

setup:
	@just setup

dev:
	@just dev

# ============================================================================
# CODE QUALITY
# ============================================================================

lint:
	@just lint

format:
	@just format

# ============================================================================
# TESTING - Test Ladder Targets
# ============================================================================

test:
	@just test

test-lint:
	@just test-lint

test-unit:
	@just test-unit

test-integration:
	@just test-integration

test-e2e:
	@just test-e2e

# ============================================================================
# DOCUMENTATION
# ============================================================================

help:
	@just help

docs:
	@just docs
```

## Advanced Patterns

### Conditional Recipes

```makefile
# Run with optional arguments
test:
	@just test $(ARGS)

# Usage: make test ARGS="--coverage --watch"
```

### Environment Variable Pass-Through

```makefile
# Pass environment variables to justfile
test:
	@RUST_LOG=debug just test

dev:
	@NODE_ENV=development just dev
```

### Makefile with Pre-checks

```makefile
# Ensure just is installed before running
.PHONY: _ensure-just

_ensure-just:
	@if ! command -v just &> /dev/null; then \
		echo "❌ 'just' is not installed. Install from: https://github.com/casey/just"; \
		exit 1; \
	fi

install: _ensure-just
	@just install

build: _ensure-just
	@just build

test: _ensure-just
	@just test
```

### Makefile with Terraform Targets

```makefile
.PHONY: plan apply destroy fmt validate

# Terraform-specific targets
plan:
	@just plan

apply:
	@just apply

destroy:
	@just destroy

fmt:
	@just format

validate:
	@just lint
```

### Makefile with Git Hooks Integration

```makefile
.PHONY: install-hooks

install-hooks:
	@echo "📦 Installing git hooks..."
	@mkdir -p .git/hooks
	@echo '#!/bin/bash' > .git/hooks/pre-commit
	@echo 'make test-lint' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed"
```

## Common Mistakes

### ❌ Using Spaces Instead of Tabs
```makefile
# WRONG - recipe body uses spaces
install:
    @just install

# RIGHT - recipe body uses a tab
install:
	@just install
```
**Fix**: Configure your editor to preserve tabs in Makefiles.

### ❌ Forgetting `.PHONY` Declaration
```makefile
# Without .PHONY, 'make clean' skips if a 'clean' file exists
clean:
	@just clean

# With .PHONY, 'make clean' always runs
.PHONY: clean
clean:
	@just clean
```

### ❌ Adding Complex Logic
```makefile
# WRONG - Makefiles aren't great at complex logic
test:
	@if [ "$(ENV)" = "ci" ]; then \
		just test-full; \
	else \
		just test; \
	fi

# BETTER - Let justfile handle conditional logic
test:
	@just test ENV=$(ENV)
```

## Testing the Wrapper

```bash
# Verify Makefile syntax
make -n test       # Dry-run, shows what would execute

# Run a target through Makefile
make test           # Should call: just test

# Verify both methods work
just test           # Direct justfile call
make test           # Via Makefile wrapper

# Check that all targets are defined
make --always-make --dry-run 2>&1 | grep -E "^\\[" || echo "All targets OK"
```

## Migration Path: Make → Just

### Phase 1: Introduce Justfile + Wrapper
```bash
# Create both justfile and Makefile
git add justfile Makefile
git commit -m "Add justfile with Makefile wrapper for gradual migration"
```

### Phase 2: Update Documentation
Update README to mention both approaches:
```markdown
Run tests with either:
- `make test` (classic)
- `just test` (recommended)
```

### Phase 3: Update CI/CD Gradually
Change CI/CD to use `just` as you update pipelines:
```yaml
# Before
script: make test

# After
script: just test
```

### Phase 4: Deprecate Makefile (Optional)
Once everyone is comfortable with `just`, you can delete the Makefile.

## Troubleshooting

**Q: `make test` shows "missing separator" error**
A: Check that recipe bodies use tabs, not spaces. Most editors have tab/space settings.

**Q: `make build` hangs**
A: The justfile recipe is waiting for input. Check if it has interactive prompts.

**Q: `.PHONY` isn't working**
A: Ensure it's declared before the recipes and spelled `.PHONY` (not `.PHONEY`).

**Q: Both `make` and `just` should use same `.justfile` path**
A: By convention, use `justfile` (no leading dot). If you need `justfile` in a subdirectory, update recipes in Makefile.
