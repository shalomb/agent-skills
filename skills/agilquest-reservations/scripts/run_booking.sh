#!/usr/bin/env bash
# Wrapper for cron: run the booking script with proper env.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/booking-$(date +%Y-%m-%d).log"

echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ===" >> "$LOG_FILE"
cd "$SCRIPT_DIR"
uv run src/book_reservation.py "$@" >> "$LOG_FILE" 2>&1
echo "Exit code: $?" >> "$LOG_FILE"
