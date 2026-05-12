#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/ensure-$(date +%Y-%m-%d).log"
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" >> "$LOG_FILE"
cd "$SCRIPT_DIR"
uv run src/ensure_reservation.py >> "$LOG_FILE" 2>&1
echo "Exit: $?" >> "$LOG_FILE"
