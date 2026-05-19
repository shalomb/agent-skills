#!/usr/bin/env bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/prewarm-$(date +%Y-%m-%d).log"
exec >> "$LOG_FILE" 2>&1

set -euo pipefail
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ==="

# Wait for OS network to be up before even trying Chrome
echo "Waiting for network..."
for i in $(seq 1 30); do
    if dig @8.8.8.8 +short +time=3 login.agilquest.com | grep -q "\."; then
        echo "Network ready after ${i}s"
        break
    fi
    sleep 2
done

cd "$(dirname "$0")"
uv run src/prewarm.py
echo "Exit: $?"
