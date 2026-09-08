#!/usr/bin/env bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/prewarm-$(date +%Y-%m-%d).log"
exec >> "$LOG_FILE" 2>&1

set -uo pipefail
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ==="

# Hold machine awake for 10 minutes (23:51–00:01) so the 23:57 booking
# job fires before idle sleep kicks in. Runs in background; exits on its
# own so it doesn't block the prewarm script.
echo "Holding awake for 600s via caffeinate..."
nohup caffeinate -i -t 600 &
CAFFEINATE_PID=$!
echo "caffeinate pid: $CAFFEINATE_PID"

source "$(dirname "$0")/lib_cron_preamble.sh"
wait_for_network
warn_if_chrome_contended

cd "$(dirname "$0")"
uv run src/agilquest_reservations/prewarm.py
STATUS=$?
echo "Exit: $STATUS"
exit "$STATUS"
