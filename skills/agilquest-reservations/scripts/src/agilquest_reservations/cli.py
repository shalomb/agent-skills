#!/usr/bin/env python3
"""
aq — command-line front end for the Agilquest reservation scripts.

Install once (from this scripts/ directory):
  uv tool install --editable .

Then run from anywhere:
  aq checkin              Check in to today's reservation, then book
                           today + 7 days if it isn't already reserved.
  aq book                 Book today + 7 days (same as `aq checkin`'s
                           book-ahead step, run standalone).
  aq book DATE             Book a specific date (YYYY-MM-DD or +N days).
  aq status                Today's status + 14-day calendar. Reads the
                           local cache only — no browser, instant.
  aq setup-auth            One-time/renewed interactive SSO login.

Run `aq <command> --help` for a command's options.
"""

import sys
import argparse
from datetime import datetime, timedelta

from agilquest_reservations.lib.logging import log_result
from agilquest_reservations.book_reservation import (
    DEFAULT_ASSETS as BOOK_DEFAULT_ASSETS,
    DEFAULT_START,
    DEFAULT_END,
    parse_date,
    book_with_fallbacks,
)
from agilquest_reservations.checkin_and_book import (
    DEFAULT_ASSETS as CHECKIN_DEFAULT_ASSETS,
    trigger_reauth,
    run_checkin,
    check_book_ahead_needed,
    book_ahead,
)
from agilquest_reservations.lib.browser import launch_headless, verify_auth
from agilquest_reservations.lib.cache import load_reservations
from agilquest_reservations.lib.status import render_status, STATUS_GLYPH


def cmd_checkin(args) -> int:
    """`aq checkin` — check in to today's reservation, then ensure next
    week's reservation exists, booking it if missing."""
    checkin_result = None
    book_result = None
    needs_booking = False

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = launch_headless(p)
        try:
            page = browser.new_page()
            print("Checking auth...", file=sys.stderr)
            if not verify_auth(page):
                trigger_reauth()
                log_result({
                    "status": "error",
                    "message": "Session invalid — complete SSO in the Terminal window that just opened.",
                })
                return 1

            if not args.skip_checkin:
                print("\n--- Check In ---", file=sys.stderr)
                checkin_result = run_checkin(page)

            if not args.skip_book:
                print("\n--- Book Ahead ---", file=sys.stderr)
                book_result = check_book_ahead_needed(page, args.assets)
                needs_booking = book_result is None
        finally:
            browser.close()

    # book_ahead() opens its own browser context — only call it once ours
    # above has released the persistent-profile lock.
    if needs_booking:
        book_result = book_ahead(args.assets, args.start, args.end)

    result = {"status": "ok", "checkin": checkin_result, "book_ahead": book_result}
    log_result(result)

    failed = (
        checkin_result and checkin_result["status"] == "error"
    ) or (
        book_result and book_result["status"] == "book_failed"
    )
    return 1 if failed else 0


def cmd_book(args) -> int:
    """`aq book [DATE]` — book a single date (default: +7 days from today)."""
    try:
        target = parse_date(args.date, prestage=args.prestage)
        assets = [a.strip() for a in args.assets.split(",") if a.strip()]
        result = book_with_fallbacks(
            assets=assets,
            target=target,
            start_time=args.start,
            end_time=args.end,
            prestage=args.prestage,
        )
        log_result(result)
        return 0 if result["status"] in ("success", "already_exists") else 1
    except Exception as e:
        msg = str(e)
        status = "booking_window_closed" if msg.startswith("booking_window_closed:") else "error"
        log_result({"status": status, "message": msg.splitlines()[0]})
        return 0 if status == "booking_window_closed" else 1


def cmd_status(args) -> int:
    """`aq status` — offline: render today's status + a 14-day calendar
    from the local cache. Never launches Chrome, so this is instant."""
    cache = load_reservations()
    print(render_status(cache, days_ahead=args.days))
    legend = "  ".join(f"{glyph}={label}" for label, glyph in STATUS_GLYPH.items())
    print(f"\nLegend: {legend}  [N]=today")
    return 0 if cache is not None else 1


def cmd_setup_auth(args) -> int:
    """`aq setup-auth` — interactive SSO login (opens a headed Chrome window)."""
    from agilquest_reservations.setup_auth import main as setup_auth_main
    setup_auth_main()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aq",
        description="Agilquest reservation CLI: check in and book workspace reservations.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_checkin = sub.add_parser("checkin", help="Check in to today's reservation, then book +7 days if missing")
    p_checkin.add_argument("--skip-checkin", action="store_true", help="Only run the book-ahead step")
    p_checkin.add_argument("--skip-book", action="store_true", help="Only run the check-in step")
    p_checkin.add_argument("--assets", default=CHECKIN_DEFAULT_ASSETS, help="Ordered fallback asset IDs")
    p_checkin.add_argument("--start", default=DEFAULT_START, help="Start time, e.g. '09:00 AM'")
    p_checkin.add_argument("--end", default=DEFAULT_END, help="End time, e.g. '05:00 PM'")
    p_checkin.set_defaults(func=cmd_checkin)

    p_book = sub.add_parser("book", help="Book a workspace reservation (default: +7 days from today)")
    p_book.add_argument(
        "date", nargs="?", default="+7",
        help="Target date: YYYY-MM-DD, or +N days from today (default: +7)",
    )
    p_book.add_argument("--assets", default=",".join(BOOK_DEFAULT_ASSETS), help="Ordered fallback asset IDs")
    p_book.add_argument("--start", default=DEFAULT_START, help="Start time, e.g. '09:00 AM'")
    p_book.add_argument("--end", default=DEFAULT_END, help="End time, e.g. '05:00 PM'")
    p_book.add_argument(
        "--prestage", action="store_true",
        help="Stage the form now, sleep until 23:59:58, then submit",
    )
    p_book.set_defaults(func=cmd_book)

    p_status = sub.add_parser("status", help="Show today's status + calendar, from cache only (no browser)")
    p_status.add_argument("--days", type=int, default=14, help="Days ahead to show (default: 14)")
    p_status.set_defaults(func=cmd_status)

    p_auth = sub.add_parser("setup-auth", help="Interactive SSO login (one-time, or when sessions expire)")
    p_auth.set_defaults(func=cmd_setup_auth)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
