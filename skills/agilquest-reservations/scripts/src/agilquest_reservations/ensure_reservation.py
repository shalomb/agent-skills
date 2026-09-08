#!/usr/bin/env python3
"""
Daily 14:00 health-check: confirm the 7-days-ahead reservation exists,
booking it if missing. Lists all active reservations.

On session failure, launches setup_auth.py in a Terminal via osascript
and waits up to 5 minutes for the user to complete SSO, then retries.

Usage:
  aq ensure
  uv run src/agilquest_reservations/ensure_reservation.py

Cron:
  14:00  run_aq.sh ensure
"""

import sys
import json
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from agilquest_reservations.lib.browser import launch_headless, verify_auth, trigger_reauth_and_wait
from agilquest_reservations.lib.agilquest import get_reservations, find_existing, stage, submit_with_retries
from agilquest_reservations.lib.logging import log_result

PRIMARY_ASSET = "343"
DEFAULT_START = "09:00 AM"
DEFAULT_END = "05:00 PM"


def book_primary(page, target: datetime) -> dict:
    """Book PRIMARY_ASSET for target date using the shared stage/submit logic."""
    target_str = target.strftime("%Y-%m-%d")
    when_value = stage(page, PRIMARY_ASSET, target, DEFAULT_START, DEFAULT_END)
    return submit_with_retries(
        page, PRIMARY_ASSET, target_str, when_value, DEFAULT_START, DEFAULT_END
    )


def run_checks() -> dict:
    target = datetime.now() + timedelta(days=7)
    target_str = target.strftime("%Y-%m-%d")

    with sync_playwright() as p:
        browser = launch_headless(p)
        try:
            page = browser.new_page()

            print("Checking auth...", file=sys.stderr)
            if not verify_auth(page, context=browser):
                return {"status": "auth_required"}

            print(f"Fetching reservations for {target_str}...", file=sys.stderr)
            reservations = get_reservations(page)
            existing = find_existing(reservations, PRIMARY_ASSET, target)

            booking_result = None
            if existing:
                print(f"Reservation {existing['id']} already exists for {target_str}.", file=sys.stderr)
            else:
                print(f"No reservation for {target_str} — booking now...", file=sys.stderr)
                booking_result = book_primary(page, target)
                if booking_result["status"] in ("success",):
                    reservations = get_reservations(page)
                    existing = find_existing(reservations, PRIMARY_ASSET, target)

            return {
                "status": "ok",
                "target_date": target_str,
                "reservation": existing,
                "booking_attempted": booking_result,
                "active_reservations": reservations,
            }
        finally:
            browser.close()


def report(result: dict) -> int:
    """Print result as JSON + a one-line RESULT summary, log on failure.

    Shared by `aq ensure` (cli.py) and this file's own __main__ block, so
    both report identically — the auth-retry loop around run_checks() is
    the only part that differs between the two callers.
    """
    print(json.dumps(result, indent=2))

    reservation = result.get("reservation")
    if result["status"] != "ok" or not reservation:
        log_result({**result, "message": result.get("message", "No confirmed reservation for target date")})
        return 1

    asset_id = (reservation.get("asset_href", "") or "").split("/asset/")[-1] or reservation.get("asset", "")
    action = "booked" if result.get("booking_attempted") else "already_exists"
    print(
        f"RESULT: {action} asset={asset_id} date={result['target_date']} id={reservation.get('id', '')}",
        file=sys.stderr,
    )
    return 0


def main():
    result = run_checks()

    if result["status"] == "auth_required":
        with sync_playwright() as p:
            reauthed = trigger_reauth_and_wait(p)
        if not reauthed:
            log_result({"status": "error", "message": "Re-auth failed or timed out"})
            sys.exit(1)
        result = run_checks()

    sys.exit(report(result))


if __name__ == "__main__":
    main()
