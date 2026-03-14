# Test Ladder Patterns

The test ladder is a graduated testing strategy that provides fast feedback early and saves slow tests for later. This document shows patterns for different project types.

## Core Pattern

```justfile
# Master orchestrator - coordinates all test levels
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Tier 1 - Instant feedback (1-2 seconds)
test-lint:
    # Linting, formatting, type checks

# Tier 2 - Fast (5-30 seconds)
test-unit:
    # Unit tests only, no external dependencies

# Tier 3 - Medium (30 seconds - 2 minutes)
test-integration:
    # Tests that require external services, databases, etc.

# Tier 4 - Slow (2+ minutes)
test-e2e:
    # Full end-to-end tests, browser tests, etc.
```

## Node.js/JavaScript Pattern

```justfile
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Tier 1: Linting and type checking
test-lint:
    @echo "🔍 Running ESLint, TypeScript, Prettier..."
    npm run lint
    npm run typecheck 2>/dev/null || true
    prettier --check "src/**/*.{ts,tsx,js}"

# Tier 2: Unit tests (no external deps)
test-unit:
    @echo "⚡ Running unit tests (no network)..."
    npm run test:unit -- --coverage --testPathIgnorePatterns="integration|e2e"

# Tier 3: Integration tests (may need DB/API mocks)
test-integration:
    @echo "🔗 Running integration tests..."
    npm run test:integration -- --testPathPattern="integration"

# Tier 4: E2E tests (full system)
test-e2e:
    @echo "🌐 Running E2E tests..."
    npm run test:e2e -- --testPathPattern="e2e"
```

## Python Pattern

```justfile
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Tier 1: Linting, type checking, formatting
test-lint:
    @echo "🔍 Running Black, isort, Flake8, mypy..."
    black --check src/ tests/
    isort --check-only src/ tests/
    flake8 src/ tests/
    mypy src/

# Tier 2: Unit tests
test-unit:
    @echo "⚡ Running pytest (unit tests)..."
    pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Tier 3: Integration tests
test-integration:
    @echo "🔗 Running pytest (integration)..."
    pytest tests/integration/ -v -m "integration"

# Tier 4: E2E tests
test-e2e:
    @echo "🌐 Running pytest (E2E)..."
    pytest tests/e2e/ -v -m "e2e" --timeout=300
```

## Rust Pattern

```justfile
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Tier 1: clippy warnings, formatting
test-lint:
    @echo "🔍 Running clippy and checking formatting..."
    cargo clippy --all-targets --all-features -- -D warnings
    cargo fmt --check

# Tier 2: Unit tests
test-unit:
    @echo "⚡ Running unit tests..."
    cargo test --lib --all-features

# Tier 3: Integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    cargo test --test '*' --all-features

# Tier 4: Doc tests and examples
test-e2e:
    @echo "🌐 Running doc tests and examples..."
    cargo test --doc --all-features
    cargo build --examples
```

## Go Pattern

```justfile
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Tier 1: Linting and vet
test-lint:
    @echo "🔍 Running golangci-lint and go vet..."
    golangci-lint run ./...
    go vet ./...

# Tier 2: Unit tests
test-unit:
    @echo "⚡ Running unit tests..."
    go test ./... -v -short -race -coverprofile=coverage.out

# Tier 3: Integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    go test ./... -v -run Integration -race

# Tier 4: Full tests with coverage
test-e2e:
    @echo "🌐 Running full test suite with coverage..."
    go test ./... -v -race -coverprofile=coverage.out
    go tool cover -html=coverage.out
```

## Terraform Pattern

```justfile
test: test-lint test-validate test-plan test-security
    @echo "✅ All checks passed!"

# Tier 1: Format checking
test-lint:
    @echo "🔍 Checking HCL formatting..."
    terraform fmt -check -recursive .

# Tier 2: Syntax validation
test-validate:
    @echo "✅ Validating configuration..."
    terraform validate

# Tier 3: Security scanning
test-security:
    @echo "🔒 Running security checks..."
    tflint .
    terrascan scan -t aws 2>/dev/null || true

# Tier 4: Plan generation for review
test-plan:
    @echo "📋 Generating terraform plan..."
    terraform init -backend=false
    terraform plan -out=tftest.plan
    rm -f tftest.plan
```

## Advanced Patterns

### Conditional Test Execution

```justfile
test: test-lint test-unit test-integration
    @echo "✅ All tests passed!"

# Run only integration tests if INTEGRATION env var is set
test-integration:
    @if [[ "{{env('INTEGRATION', '')}}" == "true" ]]; then \\
        echo "🔗 Running integration tests..."; \\
        npm run test:integration; \\
    else \\
        echo "⏭️ Skipping integration tests (set INTEGRATION=true to run)"; \\
    fi
```

### Parallel Test Execution

```justfile
# Run tests in parallel with paralleltest tool
test-unit:
    @echo "⚡ Running unit tests in parallel..."
    paralleltest -p 4 npm run test -- --maxWorkers=4
```

### Test Coverage Reporting

```justfile
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"
    @echo "📊 Coverage report:"
    @coverage report --skip-empty

test-unit:
    @echo "⚡ Running unit tests with coverage..."
    pytest tests/unit --cov=src --cov-report=html --cov-report=term-missing
```

### Watch Mode for Development

```justfile
test-watch:
    @echo "👀 Watching for changes and running tests..."
    pytest-watch tests/ -- -v --tb=short
```

## Best Practices

1. **Keep each tier under expected time limit**
   - Tier 1: < 5 seconds
   - Tier 2: < 30 seconds
   - Tier 3: < 2 minutes
   - Tier 4: < 5 minutes

2. **Fail fast at each tier**
   - Don't run tier 3 if tier 2 fails
   - Just recipes naturally stop on failure (no need for `|| true`)

3. **Group tests logically**
   - Unit tests have no external dependencies
   - Integration tests use mocked/test services
   - E2E tests use real deployments or full stacks

4. **Make individual recipes useful**
   - `just test-unit` should be runnable standalone
   - `just test-integration` should be runnable standalone
   - Developers can run `just test-unit --watch` for development

5. **Document what each tier does**
   - Comments explain what's being tested and why
   - Help developers understand when to use each target

## Debugging Test Failures

Run individual tiers to isolate issues:

```bash
# Test tier by tier
just test-lint          # Does code pass linting?
just test-unit          # Do units work?
just test-integration   # Do systems integrate?
just test-e2e           # Does full stack work?

# Run with verbose output
just test-unit -- --verbose

# Run specific test pattern
just test-unit -- --testNamePattern="auth"
```
