#!/usr/bin/env bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/booking-$(date +%Y-%m-%d).log"
exec >> "$LOG_FILE" 2>&1

set -euo pipefail
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ==="

# Wait for network — machine may have just woken from sleep
echo "Waiting for network..."
for i in $(seq 1 30); do
  if dig @8.8.8.8 +short +time=3 login.agilquest.com | grep -q "\."; then
    echo "Network ready after ${i}s"
    break
  fi
  sleep 2
done

# Clear any stale Chrome singleton lock from a previous run
LOCK="$HOME/.local/state/agent-skills/agilquest-reservations/user_data/SingletonLock"
if [ -L "$LOCK" ]; then
  LOCK_PID=$(readlink "$LOCK" | grep -oE '[0-9]+$' || true)
  if [ -n "$LOCK_PID" ] && ! kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "Removing stale SingletonLock (pid $LOCK_PID gone)"
    rm -f "$LOCK"
  elif [ -n "$LOCK_PID" ]; then
    echo "WARNING: Chrome pid $LOCK_PID still alive — killing"
    kill "$LOCK_PID" 2>/dev/null || true
    sleep 2
    rm -f "$LOCK"
  fi
fi

cd "$(dirname "$0")"
uv run src/book_reservation.py "$@"
echo "Exit: $?"
