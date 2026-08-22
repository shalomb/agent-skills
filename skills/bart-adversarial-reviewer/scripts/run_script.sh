#!/bin/bash
#
# Wrapper script to run pr-review Python scripts using uv (if available)
# or fall back to python3
#
# Usage:
#   ./run_script.sh <script_name> [args...]
#   
# Examples:
#   ./run_script.sh parse_pr_url.py "https://github.com/owner/repo/pull/123"
#   ./run_script.sh check_prerequisites.py --verbose
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="${1:?Usage: run_script.sh <script_name> [args...]}"
shift  # Remove first argument

# Check if uv is available
if command -v uv &> /dev/null; then
    # Use uv for faster execution
    uv run "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
else
    # Fall back to python3
    python3 "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
fi
