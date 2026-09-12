#!/usr/bin/env python3
"""
Daily workflow: check in to today's reservation, and ensure next week's
reservation is booked.

1. Check In:
   Finds today's reservation in the active-reservations table, ticks its
   "Check In" checkbox, clicks SUBMIT, and confirms the status flips away
   from "Awaiting Check In". No-ops if already checked in or if there's no
   reservation for today.

2. Book ahead:
   Checks whether a reservation already exists for the same weekday next
   week (today + 7 days). If not, books it via the same asset-fallback
   chain and retries as `aq book` / book_reservation.py.

On auth failure, launches setup_auth.py in a Terminal via osascript and
waits up to 5 minutes for SSO to complete, then retries in place —
deliberately, unlike book_reservation.py's unattended 00:01 run: this job
fires at 09:00, when you're plausibly at your desk to complete SSO.

Usage:
  aq checkin [options]
  uv run src/agilquest_reservations/checkin_and_book.py [options]

Options:
  --skip-checkin   Only run the book-ahead step
  --skip-book      Only run the check-in step
  --assets         343,257,14006,14005   Passed through to book_reservation.py
  --start          HH:MM AM/PM           Passed through to book_reservation.py
  --end            HH:MM AM/PM           Passed through to book_reservation.py

Cron (weekdays only, Mon-Fri):
  09:00  run_aq.sh checkin
  (also: 00:01 run_aq.sh book, 14:00 run_aq.sh ensure)
"""

import sys
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from agilquest_reservations.lib.browser import launch_headless, verify_auth, trigger_reauth_and_wait
from agilquest_reservations.lib.agilquest import get_reservations, find_existing, find_today, check_in
from agilquest_reservations.lib.logging import log_result
from agilquest_reservations.book_reservation import book_with_fallbacks

DEFAULT_ASSETS = "343,257,14006,14005"
DEFAULT_START = "09:00 AM"
DEFAULT_END = "05:00 PM"
LOOK_AHEAD_DAYS = 7


def run_checkin(page) -> dict:
    """Check in to today's reservation, if one exists and isn't already checked in."""
    today = datetime.now()
    reservations = get_reservations(page)
    today_resv = find_today(reservations, today)

    if not today_resv:
        msg = f"No reservation found for today ({today.strftime('%Y-%m-%d')})"
        print(msg, file=sys.stderr)
        return {"status": "no_reservation_today", "message": msg}

    status = today_resv.get("status", "")
    if status.lower() != "awaiting check in":
        msg = f"Reservation {today_resv['id']} already in status '{status}' — nothing to do"
        print(msg, file=sys.stderr)
        return {
            "status": "already_checked_in",
            "reservation_id": today_resv["id"],
            "reservation_status": status,
            "message": msg,
        }

    if not today_resv.get("checkin_checkbox_id"):
        msg = f"Reservation {today_resv['id']} has no Check In checkbox available yet"
        print(msg, file=sys.stderr)
        return {
            "status": "error",
            "reservation_id": today_resv["id"],
            "message": msg,
        }

    return check_in(page, today_resv)


def check_book_ahead_needed(page, assets: str) -> dict | None:
    """Return an 'already_exists' result if a reservation exists for
    today + LOOK_AHEAD_DAYS on any asset, else None (booking is needed).
    """
    target = datetime.now() + timedelta(days=LOOK_AHEAD_DAYS)
    target_str = target.strftime("%Y-%m-%d")
    asset_list = [a.strip() for a in assets.split(",") if a.strip()]

    reservations = get_reservations(page)
    for asset_id in asset_list:
        existing = find_existing(reservations, asset_id, target)
        if existing:
            msg = f"Reservation {existing['id']} already exists for {target_str} on asset {asset_id}"
            print(msg, file=sys.stderr)
            return {
                "status": "already_exists",
                "asset_id": asset_id,
                "target_date": target_str,
                "reservation_id": existing["id"],
                "message": msg,
            }
    return None


def book_ahead(assets: str, start_time: str, end_time: str) -> dict:
    """Book today + LOOK_AHEAD_DAYS via book_with_fallbacks.

    Opens its own browser (a fresh persistent-context session) — call this
    only after any earlier context in this process has been closed, since
    Chrome allows only one owner of the profile dir at a time.
    """
    target = datetime.now() + timedelta(days=LOOK_AHEAD_DAYS)
    target_str = target.strftime("%Y-%m-%d")
    asset_list = [a.strip() for a in assets.split(",") if a.strip()]
    print(f"No reservation for {target_str} — booking now...", file=sys.stderr)

    result = book_with_fallbacks(
        assets=asset_list,
        target=target,
        start_time=start_time,
        end_time=end_time,
        prestage=False,
    )
    return {
        **result,
        "status": "booked" if result.get("status") in ("success", "already_exists") else "book_failed",
    }


def run_checkin_and_book(args) -> dict | None:
    """Run the auth check, check-in, and book-ahead-needed steps.

    Returns None if auth failed (caller decides how to recover), else a
    dict with checkin_result/book_result/needs_booking.
    """
    checkin_result = None
    book_result = None
    needs_booking = False

    with sync_playwright() as p:
        browser = launch_headless(p)
        try:
            page = browser.new_page()

            print("Checking auth...", file=sys.stderr)
            if not verify_auth(page, context=browser):
                return None

            if not args.skip_checkin:
                print("\n--- Check In ---", file=sys.stderr)
                checkin_result = run_checkin(page)

            if not args.skip_book:
                print("\n--- Book Ahead ---", file=sys.stderr)
                book_result = check_book_ahead_needed(page, args.assets)
                needs_booking = book_result is None
        finally:
            browser.close()

    return {
        "checkin_result": checkin_result,
        "book_result": book_result,
        "needs_booking": needs_booking,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--skip-checkin", action="store_true")
    parser.add_argument("--skip-book", action="store_true")
    parser.add_argument("--assets", default=DEFAULT_ASSETS)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    args = parser.parse_args()

    outcome = run_checkin_and_book(args)

    if outcome is None:
        with sync_playwright() as p:
            reauthed = trigger_reauth_and_wait(p)
        if not reauthed:
            log_result({
                "status": "error",
                "message": "Session invalid — run `aq setup-auth`. "
                           "ensure_reservation.py at 14:00 will rebook.",
            })
            sys.exit(1)
        outcome = run_checkin_and_book(args)
        if outcome is None:
            log_result({
                "status": "error",
                "message": "Session still invalid after re-auth — run `aq setup-auth`.",
            })
            sys.exit(1)

    checkin_result = outcome["checkin_result"]
    book_result = outcome["book_result"]

    # book_reservation.py launches its own browser against the same
    # persistent profile — only call it once ours has released the lock.
    if outcome["needs_booking"]:
        book_result = book_ahead(args.assets, args.start, args.end)

    result = {
        "status": "ok",
        "checkin": checkin_result,
        "book_ahead": book_result,
    }
    log_result(result)

    failed = (
        checkin_result and checkin_result["status"] == "error"
    ) or (
        book_result and book_result["status"] == "book_failed"
    )
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
