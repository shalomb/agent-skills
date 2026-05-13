#!/usr/bin/env bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/warmup-$(date +%Y-%m-%d).log"
exec >> "$LOG_FILE" 2>&1

set -euo pipefail
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ==="

# Wait for network — machine may have just woken from sleep
echo "Waiting for network..."
for i in $(seq 1 30); do
  if curl -sf --max-time 3 https://login.agilquest.com > /dev/null 2>&1; then
    echo "Network ready after ${i}s"
    break
  fi
  sleep 2
done

cd "$(dirname "$0")"
uv run src/warmup.py
echo "Exit: $?"
