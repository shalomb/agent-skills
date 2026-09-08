#!/usr/bin/env bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/checkin-and-book-$(date +%Y-%m-%d).log"
exec >> "$LOG_FILE" 2>&1

set -uo pipefail
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ==="

source "$(dirname "$0")/lib_cron_preamble.sh"
wait_for_network
warn_if_chrome_contended

cd "$(dirname "$0")"
uv run src/agilquest_reservations/checkin_and_book.py "$@"
STATUS=$?
echo "Exit: $STATUS"
exit "$STATUS"
