#!/usr/bin/env bash
# Shared helpers for agilquest-reservations cron wrappers. Source the
# specific function(s) you need after setting LOG_FILE and redirecting
# output, before `set -e`.

wait_for_network() {
  echo "Waiting for network..."
  for i in $(seq 1 30); do
    if dig @8.8.8.8 +short +time=3 login.agilquest.com | grep -q "\."; then
      echo "Network ready after ${i}s"
      return 0
    fi
    sleep 2
  done
}

warn_if_chrome_contended() {
  # UNCONFIRMED HEURISTIC — logs a data point, does not diagnose anything.
  #
  # On 2026-09-08, launch_persistent_context() navigations intermittently
  # hung 30s+ per attempt (curl to the same URL: 0.3s). First seen with
  # ~30 other Chrome processes running, which looked like the cause — but
  # the same hang reproduced later with ZERO other Chrome processes
  # running, and a brand-new empty profile hung identically to the real
  # one. So process count is NOT the (or at least not the whole) cause;
  # that theory is retired. Root cause is still unknown.
  #
  # This function only logs the Chrome process count on every run — a
  # cheap, honest, always-on data point — plus a clearly-labelled
  # low-confidence flag above a loose threshold, so that IF process count
  # ever does turn out to correlate, the log history has it. Absence of
  # this warning proves nothing about whether a run will hang.
  local chrome_procs
  chrome_procs=$(pgrep -c "Google Chrome$" 2>/dev/null || echo 0)
  echo "Chrome process count at launch: $chrome_procs"
  if [ "$chrome_procs" -gt 15 ]; then
    echo "NOTE (low confidence, unconfirmed): $chrome_procs Google Chrome" \
         "processes running. This correlated with a launcher hang once on" \
         "2026-09-08 but the same hang has also occurred with 0 processes" \
         "running, so this is a data point, not a diagnosis."
  fi
}

# Stale Chrome ProcessSingleton lock from a crashed prior run is now
# cleared automatically by clear_singleton_lock() inside every
# launch_headless()/launch_headed() call in lib/browser.py — it used to
# be duplicated here in bash; removed so there is exactly one
# implementation and the two can no longer drift apart.

# On $?  and `set -e` in every wrapper that sources this file:
#
# `set -e` used to be `set -euo pipefail`. Under `set -e`, if the `uv run`
# line below exits non-zero, the shell exits AT THAT LINE — the
# `echo "Exit: $?"` after it never runs. Confirmed in production logs
# (e.g. ensure-2026-09-05.log ends right after the script's own
# `RESULT: error` line, no `Exit:` marker at all). Every wrapper now uses
# `set -uo pipefail` (no `-e`) and explicitly captures $? into STATUS
# immediately after the uv run call, so the Exit: line — and the
# wrapper's own final `exit "$STATUS"` — always run, success or failure.
