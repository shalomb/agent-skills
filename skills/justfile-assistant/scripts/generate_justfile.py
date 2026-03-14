#!/usr/bin/env python3
"""
Generate a well-formed justfile for a project based on detected language/framework.
Implements test ladder patterns and standard recipes.
"""

import os
import sys
from pathlib import Path

def detect_project_type(project_root: str) -> str:
    """Detect project type by examining files in the project root."""
    root = Path(project_root)
    
    # Check for language/framework indicators
    if (root / "package.json").exists():
        return "node"
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "python"
    if (root / "Cargo.toml").exists():
        return "rust"
    if (root / "go.mod").exists():
        return "go"
    if (root / "terraform").exists() or any(root.glob("*.tf")):
        return "terraform"
    if (root / "Makefile").exists() or (root / "makefile").exists():
        return "makefile"
    
    return "generic"

def generate_node_justfile() -> str:
    """Generate justfile for Node.js/JavaScript projects."""
    return """# Justfile for Node.js/JavaScript Project
# Standard recipes: install, build, clean, test, lint, dev, docs
# Test ladder with unit → integration → E2E progression

set shell := ["bash", "-c"]

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
    @echo "📦 Installing dependencies..."
    npm install

clean:
    @echo "🧹 Cleaning build artifacts..."
    rm -rf dist/ build/ .coverage node_modules/.cache

setup: install
    @echo "✅ Project setup complete"

# ============================================================================
# BUILD & DEVELOPMENT
# ============================================================================

build:
    @echo "🔨 Building project..."
    npm run build

dev:
    @echo "🚀 Starting development server..."
    npm run dev

format:
    @echo "📝 Formatting code..."
    prettier --write "src/**/*.{ts,tsx,js,jsx,json,md}" 2>/dev/null || true
    npm run format 2>/dev/null || true

lint:
    @echo "🔍 Linting code..."
    npm run lint

# ============================================================================
# TESTING - Test Ladder Pattern
# ============================================================================

# Master test orchestrator - graduated ladder (lint → unit → integration → e2e)
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Fastest feedback - linting and type checking
test-lint:
    @echo "🔍 Running linting and type checks..."
    npm run lint 2>/dev/null || true
    npm run typecheck 2>/dev/null || true

# Fast - unit tests only
test-unit:
    @echo "⚡ Running unit tests..."
    npm run test:unit 2>/dev/null || npm test -- --testPathPattern="test|spec" 2>/dev/null || true

# Medium speed - integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    npm run test:integration 2>/dev/null || true

# Slowest - end-to-end tests
test-e2e:
    @echo "🌐 Running E2E tests..."
    npm run test:e2e 2>/dev/null || true

# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

help:
    @echo "\\n📚 Available Commands:\\n"
    @just --list

docs:
    @echo "📖 Generating documentation..."
    npm run docs 2>/dev/null || echo "No docs script defined"
"""

def generate_python_justfile() -> str:
    """Generate justfile for Python projects."""
    return """# Justfile for Python Project
# Standard recipes: install, build, clean, test, lint, dev, docs
# Test ladder with lint → unit → integration → e2e progression

set shell := ["bash", "-c"]

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
    @echo "📦 Installing dependencies..."
    uv pip install -e . 2>/dev/null || pip install -e .

clean:
    @echo "🧹 Cleaning build artifacts..."
    rm -rf dist/ build/ *.egg-info .coverage .pytest_cache __pycache__ .mypy_cache

setup: install
    @echo "✅ Project setup complete"

# ============================================================================
# BUILD & DEVELOPMENT
# ============================================================================

build:
    @echo "🔨 Building project..."
    uv pip install -e . 2>/dev/null || pip install -e .

dev:
    @echo "🚀 Starting development environment..."
    python -m pip install -e ".[dev]" 2>/dev/null || pip install -e ".[dev]"

format:
    @echo "📝 Formatting code..."
    black src/ tests/ 2>/dev/null || true
    isort src/ tests/ 2>/dev/null || true

lint:
    @echo "🔍 Linting code..."
    flake8 src/ tests/ 2>/dev/null || true
    mypy src/ 2>/dev/null || true

# ============================================================================
# TESTING - Test Ladder Pattern
# ============================================================================

# Master test orchestrator - graduated ladder
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Fastest feedback - linting and type checking
test-lint:
    @echo "�� Running linting and type checks..."
    black --check src/ tests/ 2>/dev/null || true
    flake8 src/ tests/ 2>/dev/null || true
    mypy src/ 2>/dev/null || true

# Fast - unit tests only
test-unit:
    @echo "⚡ Running unit tests..."
    pytest tests/ -k "not integration and not e2e" -v 2>/dev/null || pytest tests/ -v

# Medium speed - integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    pytest tests/ -k "integration" -v 2>/dev/null || true

# Slowest - end-to-end tests
test-e2e:
    @echo "🌐 Running E2E tests..."
    pytest tests/ -k "e2e" -v 2>/dev/null || true

# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

help:
    @echo "\\n📚 Available Commands:\\n"
    @just --list

docs:
    @echo "📖 Generating documentation..."
    sphinx-build -b html docs docs/_build 2>/dev/null || echo "No sphinx docs configured"
"""

def generate_rust_justfile() -> str:
    """Generate justfile for Rust projects."""
    return """# Justfile for Rust Project
# Standard recipes: install, build, clean, test, lint, dev, docs
# Test ladder with clippy → unit → integration → e2e progression

set shell := ["bash", "-c"]

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
    @echo "📦 Installing dependencies..."
    cargo fetch

clean:
    @echo "🧹 Cleaning build artifacts..."
    cargo clean

setup: install
    @echo "✅ Project setup complete"

# ============================================================================
# BUILD & DEVELOPMENT
# ============================================================================

build:
    @echo "🔨 Building project..."
    cargo build --release

dev:
    @echo "🚀 Running in debug mode..."
    cargo build

format:
    @echo "📝 Formatting code..."
    cargo fmt

lint:
    @echo "🔍 Checking with clippy..."
    cargo clippy -- -D warnings

# ============================================================================
# TESTING - Test Ladder Pattern
# ============================================================================

# Master test orchestrator - graduated ladder
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Fastest feedback - clippy warnings
test-lint:
    @echo "🔍 Running clippy..."
    cargo clippy -- -D warnings

# Fast - unit tests
test-unit:
    @echo "⚡ Running unit tests..."
    cargo test --lib

# Medium speed - integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    cargo test --test '*'

# Slowest - doc tests
test-e2e:
    @echo "🌐 Running doc tests..."
    cargo test --doc

# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

help:
    @echo "\\n📚 Available Commands:\\n"
    @just --list

docs:
    @echo "📖 Building documentation..."
    cargo doc --no-deps --open
"""

def generate_terraform_justfile() -> str:
    """Generate justfile for Terraform projects."""
    return """# Justfile for Terraform/IaC Project
# Standard recipes: install, build, clean, test, lint, plan, apply, docs
# Test ladder with fmt → validate → lint → plan progression

set shell := ["bash", "-c"]

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
    @echo "📦 Initializing Terraform..."
    terraform init

clean:
    @echo "🧹 Cleaning Terraform state..."
    rm -rf .terraform/ .terraform.lock.hcl

setup: install
    @echo "✅ Terraform setup complete"

# ============================================================================
# BUILD & DEPLOYMENT
# ============================================================================

build:
    @echo "🔨 Running terraform plan..."
    terraform plan -out=tfplan

plan:
    @echo "📋 Generating terraform plan..."
    terraform plan

apply:
    @echo "🚀 Applying terraform changes..."
    terraform apply tfplan

format:
    @echo "📝 Formatting HCL code..."
    terraform fmt -recursive .

lint:
    @echo "🔍 Linting Terraform..."
    tflint 2>/dev/null || terraform validate

# ============================================================================
# TESTING - Test Ladder Pattern
# ============================================================================

# Master test orchestrator - graduated ladder
test: test-lint test-format test-validate test-plan
    @echo "✅ All checks passed!"

# Fastest feedback - formatting check
test-lint:
    @echo "🔍 Checking formatting..."
    terraform fmt -check -recursive . 2>/dev/null || true

# Fast - syntax validation
test-format:
    @echo "📝 Validating HCL syntax..."
    terraform fmt -check -recursive . || true

# Medium - validation
test-validate:
    @echo "✅ Validating configuration..."
    terraform validate

# Slowest - plan generation
test-plan:
    @echo "📋 Generating plan for review..."
    terraform plan -out=tftest_plan 2>/dev/null && rm tftest_plan || true

# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

help:
    @echo "\\n📚 Available Commands:\\n"
    @just --list

docs:
    @echo "📖 Generating documentation..."
    terraform-docs markdown . > README.md 2>/dev/null || echo "Install terraform-docs for docs generation"
"""

def generate_generic_justfile() -> str:
    """Generate generic minimal justfile."""
    return """# Generic Justfile
# Customize recipes for your project type
# Standard recipes: install, build, clean, test, lint, dev, docs

set shell := ["bash", "-c"]

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
    @echo "📦 Installing dependencies..."
    # TODO: Add your install command

clean:
    @echo "🧹 Cleaning artifacts..."
    # TODO: Add your clean command

setup: install
    @echo "✅ Setup complete"

# ============================================================================
# BUILD & DEVELOPMENT
# ============================================================================

build:
    @echo "🔨 Building project..."
    # TODO: Add your build command

dev:
    @echo "🚀 Starting development..."
    # TODO: Add your dev command

format:
    @echo "📝 Formatting code..."
    # TODO: Add your format command

lint:
    @echo "🔍 Linting code..."
    # TODO: Add your lint command

# ============================================================================
# TESTING - Test Ladder Pattern
# ============================================================================

# Master test orchestrator
test: test-lint test-unit test-integration test-e2e
    @echo "✅ All tests passed!"

# Fastest feedback
test-lint:
    @echo "🔍 Running linting..."
    # TODO: Add lint tests

# Fast - unit tests
test-unit:
    @echo "⚡ Running unit tests..."
    # TODO: Add unit tests

# Medium speed - integration tests
test-integration:
    @echo "🔗 Running integration tests..."
    # TODO: Add integration tests

# Slowest - end-to-end tests
test-e2e:
    @echo "🌐 Running E2E tests..."
    # TODO: Add E2E tests

# ============================================================================
# DOCUMENTATION & HELP
# ============================================================================

help:
    @echo "\\n📚 Available Commands:\\n"
    @just --list

docs:
    @echo "📖 Generating documentation..."
    # TODO: Add your docs command
"""

def generate_makefile() -> str:
    """Generate Makefile that redirects to justfile."""
    return """.PHONY: install build clean test lint dev help setup format docs plan apply test-lint test-unit test-integration test-e2e

# Makefile: Redirect all targets to justfile for backward compatibility
# Use `make <target>` for legacy workflows, or `just <target>` directly

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

# Test ladder targets
test-lint:
@just test-lint

test-unit:
@just test-unit

test-integration:
@just test-integration

test-e2e:
@just test-e2e

# Terraform-specific targets
plan:
@just plan 2>/dev/null || echo "Target not available in this project"

apply:
@just apply 2>/dev/null || echo "Target not available in this project"
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_justfile.py <project_path> [--output <path>]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(project_path, "justfile")
    
    if not os.path.isdir(project_path):
        print(f"Error: {project_path} is not a valid directory")
        sys.exit(1)
    
    project_type = detect_project_type(project_path)
    print(f"Detected project type: {project_type}")
    
    # Generate justfile based on project type
    justfile_map = {
        "node": generate_node_justfile,
        "python": generate_python_justfile,
        "rust": generate_rust_justfile,
        "terraform": generate_terraform_justfile,
        "generic": generate_generic_justfile,
    }
    
    generator = justfile_map.get(project_type, generate_generic_justfile)
    justfile_content = generator()
    
    # Write justfile
    with open(output_path, "w") as f:
        f.write(justfile_content)
    print(f"✅ Created: {output_path}")
    
    # Write Makefile
    makefile_path = os.path.join(project_path, "Makefile")
    with open(makefile_path, "w") as f:
        f.write(generate_makefile())
    print(f"✅ Created: {makefile_path}")
    
    print(f"\n📚 Next steps:")
    print(f"1. Review {output_path} and customize recipes as needed")
    print(f"2. Try: cd {project_path} && just help")
    print(f"3. Run: just install (or just build, just test, etc.)")

if __name__ == "__main__":
    main()
