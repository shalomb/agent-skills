#!/usr/bin/env python3
"""
Daily 14:00 health-check: confirm the 7-days-ahead reservation exists,
booking it if missing. Lists all active reservations.

On session failure, launches setup_auth.py in a Terminal via osascript
and waits up to 5 minutes for the user to complete SSO, then retries.

Usage:
  uv run src/ensure_reservation.py
"""

import sys
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from lib.browser import (
    APP_LAUNCHER, launch_headless, launch_headed, verify_auth,
    get_state_dir, get_chrome_path,
)
from lib.agilquest import (
    RESERVATIONS_URL, get_reservations, find_existing, stage, submit_with_retries,
)
from lib.logging import log_result

PRIMARY_ASSET = "343"
DEFAULT_START = "09:00 AM"
DEFAULT_END = "05:00 PM"


def trigger_reauth_and_wait() -> bool:
    """Launch setup_auth.py in a Terminal window, then poll headlessly for up to 5 minutes."""
    scripts_dir = Path(__file__).parent.parent
    print("\nSession invalid — opening Terminal to run setup_auth.py...", file=sys.stderr)
    subprocess.Popen([
        "/usr/bin/osascript", "-e",
        f'tell application "Terminal" to do script "cd {scripts_dir} && uv run src/setup_auth.py"',
    ])
    print("Waiting up to 5 minutes for SSO to complete...", file=sys.stderr)

    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(10)
        try:
            with sync_playwright() as p:
                browser = launch_headless(p)
                try:
                    page = browser.new_page()
                    page.goto(RESERVATIONS_URL, wait_until="commit", timeout=15000)
                    time.sleep(3)
                    if "login.agilquest.com" in page.url and "microsoftonline" not in page.url:
                        print("Session restored.", file=sys.stderr)
                        return True
                finally:
                    browser.close()
        except Exception:
            pass  # profile locked by setup_auth — keep polling

    print("Re-auth timed out after 5 minutes.", file=sys.stderr)
    return False


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
            if not verify_auth(page):
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


def main():
    result = run_checks()

    if result["status"] == "auth_required":
        reauthed = trigger_reauth_and_wait()
        if not reauthed:
            r = {"status": "error", "message": "Re-auth failed or timed out"}
            log_result(r)
            sys.exit(1)
        result = run_checks()

    print(json.dumps(result, indent=2))

    reservation = result.get("reservation")
    if result["status"] != "ok" or not reservation:
        log_result({**result, "message": result.get("message", "No confirmed reservation for target date")})
        sys.exit(1)

    asset_id = (reservation.get("asset_href", "") or "").split("/asset/")[-1] or reservation.get("asset", "")
    action = "booked" if result.get("booking_attempted") else "already_exists"
    print(
        f"RESULT: {action} asset={asset_id} date={result['target_date']} id={reservation.get('id', '')}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
