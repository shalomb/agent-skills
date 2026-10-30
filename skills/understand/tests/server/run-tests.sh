#!/usr/bin/env bash
# Run the report server tests. pytest-bdd 9.0.0 does not work with pytest 9.2
# (it reads a private fixture-manager attribute that pytest 9.2 renamed), so pin pytest below 9.
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --with 'pytest<9' --with pytest-bdd pytest "$@"
