#!/usr/bin/env python3
"""
Book a workspace reservation on Agilquest with fallback assets.

Tries assets in order, moving to the next on asset_unavailable.
On auth failure, logs a hint to run `aq setup-auth` (does not auto-launch —
this runs unattended at 00:01, and checkin_and_book.py's 09:00/14:00 jobs
already cover interactive reauth).

Usage:
  aq book [DATE] [options]
  uv run src/agilquest_reservations/book_reservation.py [options]

Options:
  --assets   343,257,14006,14005   Ordered fallback list (default: all four)
  --date     YYYY-MM-DD | +N       Target date; +N = N days from today (default: +7)
  --start    HH:MM AM/PM           Start time (default: 09:00 AM)
  --end      HH:MM AM/PM           End time   (default: 05:00 PM)
  --prestage                       Stage form now, sleep until 23:59:58, then submit

Cron (weekdays only, Mon-Fri):
  00:01  run_aq.sh book
  09:00  run_aq.sh checkin
  14:00  run_aq.sh ensure
  (23:55 Sun-Thu: bare `caffeinate` keeps the machine awake for 00:01 book —
   see crontab, no `aq`/prewarm involved)
"""

import sys
import time
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from agilquest_reservations.lib.browser import launch_headless, verify_auth
from agilquest_reservations.lib.agilquest import (
    RESERVATIONS_URL, get_reservations, find_existing, stage, submit_with_retries,
)
from agilquest_reservations.lib.logging import log_result

DEFAULT_ASSETS = ["343", "257", "14006", "14005"]
DEFAULT_START = "09:00 AM"
DEFAULT_END = "05:00 PM"


def parse_date(date_arg: str, prestage: bool = False) -> datetime:
    """Parse '+N' (days from today) or 'YYYY-MM-DD'.
    With --prestage, base is tomorrow (script runs before midnight, submits after).
    """
    if date_arg.startswith("+"):
        base = datetime.now() + timedelta(days=1) if prestage else datetime.now()
        return base + timedelta(days=int(date_arg[1:]))
    return datetime.strptime(date_arg, "%Y-%m-%d")


def humanize_date(d: datetime) -> str:
    """Format as 'Mon 6th Jul, 2026' — weekday, ordinal day, month, year."""
    n = d.day
    suffix = "th" if 11 <= n <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return d.strftime(f"%a {n}{suffix} %b, %Y")


def trigger_reauth():
    """Log a reauth hint — does NOT auto-launch a Terminal.

    This runs both from the unattended 00:01 cron job and from `aq book`
    run by hand; a popped-up window is useless at midnight (nobody's
    there) and redundant when run interactively (you're already at a
    terminal). checkin_and_book.py's 09:00/14:00 jobs are the ones that
    still auto-launch, since you're plausibly at your desk then.
    """
    print("Session invalid — run: aq setup-auth", file=sys.stderr)


def book_with_fallbacks(
    assets: list[str],
    target: datetime,
    start_time: str,
    end_time: str,
    prestage: bool,
) -> dict:
    target_str = target.strftime("%Y-%m-%d")

    print(
        f"{'[prestage] ' if prestage else ''}"
        f"Booking {target_str} ({humanize_date(target)}) {start_time}-{end_time} "
        f"(assets: {', '.join(assets)})...",
        file=sys.stderr,
    )

    with sync_playwright() as p:
        browser = launch_headless(p)
        try:
            page = browser.new_page()

            print("Checking auth...", file=sys.stderr)
            if not verify_auth(page, context=browser):
                trigger_reauth()
                raise RuntimeError(
                    "Session invalid — run `aq setup-auth`. "
                    "checkin_and_book.py at 09:00 or ensure_reservation.py at 14:00 will rebook."
                )

            # Load all reservations once — used for idempotency across the fallback chain
            reservations = get_reservations(page)

            tried = []
            for asset_id in assets:
                print(f"\n--- Trying asset {asset_id} ---", file=sys.stderr)

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

                try:
                    when_value = stage(page, asset_id, target, start_time, end_time)
                except RuntimeError as e:
                    msg = str(e)
                    if msg == "auth_required":
                        trigger_reauth()
                        raise RuntimeError(
                            "Session expired mid-run — run `aq setup-auth`. "
                            "checkin_and_book.py at 09:00 or ensure_reservation.py at 14:00 will rebook."
                        )
                    if msg.startswith("booking_window_closed:"):
                        raise
                    print(f"Stage failed for {asset_id}: {msg}", file=sys.stderr)
                    tried.append({"asset_id": asset_id, "status": "stage_error", "message": msg})
                    continue

                if prestage and asset_id == assets[0]:
                    now = datetime.now()
                    fire_at = now.replace(hour=23, minute=59, second=58, microsecond=0)
                    if fire_at > now:
                        wait_s = (fire_at - now).total_seconds()
                        print(
                            f"Staged. Sleeping {wait_s:.1f}s until {fire_at.strftime('%H:%M:%S')}...",
                            file=sys.stderr,
                        )
                        time.sleep(wait_s)
                        print(
                            f"Firing SUBMIT at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}.",
                            file=sys.stderr,
                        )
                    else:
                        print("Past fire time — submitting immediately.", file=sys.stderr)

                result = submit_with_retries(
                    page, asset_id, target_str, when_value, start_time, end_time
                )
                tried.append(result)

                if result["status"] in ("success", "already_exists"):
                    return result

                if result["status"] == "asset_unavailable":
                    print(f"Asset {asset_id} unavailable — trying next...", file=sys.stderr)
                    continue

                return result  # unexpected error — stop

            return {
                "status": "all_unavailable",
                "target_date": target_str,
                "start_time": start_time,
                "end_time": end_time,
                "assets_tried": tried,
                "message": (
                    f"All assets unavailable for {target_str} {start_time}-{end_time}: "
                    + ", ".join(assets)
                ),
            }

        finally:
            browser.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--assets", default=",".join(DEFAULT_ASSETS))
    parser.add_argument("--date", default="+7")
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--prestage", action="store_true")
    args = parser.parse_args()

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
        if result["status"] not in ("success", "already_exists"):
            sys.exit(1)
    except Exception as e:
        msg = str(e)
        status = "booking_window_closed" if msg.startswith("booking_window_closed:") else "error"
        log_result({"status": status, "message": msg.splitlines()[0]})
        sys.exit(0 if status == "booking_window_closed" else 1)


if __name__ == "__main__":
    main()
