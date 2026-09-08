#!/usr/bin/env bash
# Generic cron wrapper for `aq` subcommands — replaces the previous
# run_prewarm.sh/run_booking.sh/run_ensure.sh/run_checkin_and_book.sh,
# which were four ~20-line copies differing only in the log filename and
# which `aq` subcommand they invoked. All four `aq` entry points (book,
# checkin, ensure, prewarm) are wired through cli.py, so one wrapper can
# drive all of them.
#
# Usage: run_aq.sh <subcommand> [aq args...]
#   run_aq.sh prewarm
#   run_aq.sh book
#   run_aq.sh ensure
#   run_aq.sh checkin
#
# Crontab lines look like:
#   51 23 * * * .../run_aq.sh prewarm
#   1  0  * * * .../run_aq.sh book
#   0  9  * * * .../run_aq.sh checkin
#   0  14 * * * .../run_aq.sh ensure

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SUBCOMMAND="${1:?Usage: run_aq.sh <subcommand> [aq args...]}"
shift

LOG_DIR="/Users/egn8687/.local/state/agent-skills/agilquest-reservations/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$SUBCOMMAND-$(date +%Y-%m-%d).log"
exec >> "$LOG_FILE" 2>&1

set -uo pipefail
echo "=== $(date '+%Y-%m-%dT%H:%M:%S') ==="

# prewarm runs at 23:51, ahead of the 00:01 booking job — hold the machine
# awake for 10 minutes so it doesn't idle-sleep in between. Backgrounded
# and self-expiring, so it never blocks this script.
if [ "$SUBCOMMAND" = "prewarm" ]; then
  echo "Holding awake for 600s via caffeinate..."
  nohup caffeinate -i -t 600 &
  echo "caffeinate pid: $!"
fi

source "$(dirname "$0")/lib_cron_preamble.sh"
wait_for_network
warn_if_chrome_contended

cd "$(dirname "$0")"
uv run aq "$SUBCOMMAND" "$@"
STATUS=$?
echo "Exit: $STATUS"
exit "$STATUS"
