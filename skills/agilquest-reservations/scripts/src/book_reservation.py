#!/usr/bin/env python3
"""
Book a workspace reservation on Agilquest with fallback assets.

Tries assets in order, moving to the next on asset_unavailable.
On auth failure, launches setup_auth.py in a Terminal via osascript.

Usage:
  uv run src/book_reservation.py [options]

Options:
  --assets   343,257,14006,14005   Ordered fallback list (default: all four)
  --date     YYYY-MM-DD | +N       Target date; +N = N days from today (default: +7)
  --start    HH:MM AM/PM           Start time (default: 08:30 AM)
  --end      HH:MM AM/PM           End time   (default: 04:00 PM)
  --prestage                       Stage form now, sleep until 23:59:58, then submit

Cron:
  23:51  run_prewarm.sh
  23:57  run_booking.sh  (--prestage)
  14:00  run_ensure.sh
  07:24  run_prewarm.sh
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

from lib.browser import launch_headless, save_auth, verify_auth
from lib.agilquest import (
    RESERVATIONS_URL, get_reservations, find_existing, stage, submit_with_retries,
)
from lib.logging import log_result

DEFAULT_ASSETS = ["343", "257", "14006", "14005"]
DEFAULT_START = "08:30 AM"
DEFAULT_END = "04:00 PM"


def parse_date(date_arg: str, prestage: bool = False) -> datetime:
    """Parse '+N' (days from today) or 'YYYY-MM-DD'.
    With --prestage, base is tomorrow (script runs before midnight, submits after).
    """
    if date_arg.startswith("+"):
        base = datetime.now() + timedelta(days=1) if prestage else datetime.now()
        return base + timedelta(days=int(date_arg[1:]))
    return datetime.strptime(date_arg, "%Y-%m-%d")


def trigger_reauth():
    scripts_dir = Path(__file__).parent.parent
    print("Session invalid — opening Terminal to run setup_auth.py...", file=sys.stderr)
    subprocess.Popen([
        "/usr/bin/osascript", "-e",
        f'tell application "Terminal" to do script "cd {scripts_dir} && uv run src/setup_auth.py"',
    ])


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
        f"Booking {target_str} {start_time}-{end_time} "
        f"(assets: {', '.join(assets)})...",
        file=sys.stderr,
    )

    with sync_playwright() as p:
        browser = launch_headless(p)
        try:
            page = browser.new_page()

            print("Checking auth...", file=sys.stderr)
            if not verify_auth(page):
                trigger_reauth()
                raise RuntimeError(
                    "Session invalid — complete SSO in the Terminal window that just opened. "
                    "ensure_reservation.py at 14:00 will rebook."
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
                            "Session expired mid-run — complete SSO in the Terminal window. "
                            "ensure_reservation.py at 14:00 will rebook."
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
                    save_auth(browser)
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
