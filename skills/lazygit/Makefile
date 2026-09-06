# Makefile for Lazygit Skill
# Graduated Test Ladder: Inner Loop (3-5s) + Full Verification

SHELL := /usr/bin/env bash
UV := uv
PYTHONPATH := .

.PHONY: all help fast-fail test-unit test-bdd test lint format clean

all: help

help:
	@echo "Lazygit Skill - Development & Verification Ladder"
	@echo ""
	@echo "  make fast-fail    Inner loop (3-5s): syntax, formatting, lint checks"
	@echo "  make test-unit    Run atomic TDD unit tests"
	@echo "  make test-bdd     Run BDD specification-by-example scenarios"
	@echo "  make test         Full ladder: fast-fail + unit + bdd"
	@echo "  make lint         Run ruff linter checks"
	@echo "  make format       Format code with ruff"
	@echo "  make clean        Remove cache and temporary files"
	@echo ""

fast-fail: lint
	@echo "⚡ Fast-fail checks passed."

lint:
	@echo "🔍 Checking code with ruff..."
	@uvx ruff check scripts/ tests/
	@uvx ruff format --check scripts/ tests/

format:
	@echo "🎨 Formatting code with ruff..."
	@uvx ruff format scripts/ tests/
	@uvx ruff check --fix scripts/ tests/

test-unit:
	@echo "🧪 Running TDD unit tests..."
	@PYTHONPATH=$(PYTHONPATH) $(UV) run python -m unittest discover -s tests/unit

test-bdd:
	@echo "🥒 Running BDD scenario tests..."
	@PYTHONPATH=$(PYTHONPATH) $(UV) run python -m unittest discover -s tests/bdd

test: fast-fail test-unit test-bdd
	@echo "✅ Full test ladder passed!"

clean:
	@rm -rf .ruff_cache __pycache__ scripts/__pycache__ tests/__pycache__ tests/*/__pycache__
