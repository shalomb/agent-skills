#!/usr/bin/env python3
"""
Book a workspace reservation on Agilquest with fallback assets.

Tries assets in order, moving to the next on asset_unavailable.

Usage:
  uv run src/book_reservation.py [options]

Options:
  --assets   343,257,14006,14005   Ordered fallback list (default: all four)
  --date     YYYY-MM-DD | +N       Target date; +N = N days from today (default: +7)
  --start    HH:MM AM/PM           Start time (default: 08:30 AM)
  --end      HH:MM AM/PM           End time   (default: 04:00 PM)
  --prestage                       Stage form now, sleep until 23:59:58, then submit

Cron flow:
  23:55  warmup.py
  23:57  book_reservation.py --prestage
  14:00  ensure_reservation.py  (fallback + health-check)
"""

import sys
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)


APP_LAUNCHER = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"
ASSET_URL = "https://login.agilquest.com/asset/{asset_id}"
RESERVATIONS_URL = "https://login.agilquest.com/myreservations/active?viewMode=table"

DEFAULT_ASSETS = ["343", "257", "14006", "14005"]
DEFAULT_START = "08:30 AM"
DEFAULT_END = "04:00 PM"
SUBMIT_RETRIES = 3
RETRY_DELAY_S = 5


def get_user_data_dir() -> Path:
    xdg_state = os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")
    user_data = Path(xdg_state) / "agent-skills" / "agilquest-reservations" / "user_data"
    user_data.mkdir(parents=True, exist_ok=True)
    return user_data


def get_chrome_path() -> str:
    if env := os.getenv("CHROME_PATH"):
        return env
    return (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if sys.platform == "darwin"
        else "/usr/bin/google-chrome"
    )


def parse_date(date_arg: str, prestage: bool = False) -> datetime:
    """Parse '+N' (days from today) or 'YYYY-MM-DD'.

    When --prestage is set the script launches before midnight but submits
    after midnight, so 'today' for the purpose of +N is tomorrow.
    e.g. launched at 23:57 on May 10 with +7 → target is May 18, not May 17.
    """
    if date_arg.startswith("+"):
        base = datetime.now() + timedelta(days=1) if prestage else datetime.now()
        return base + timedelta(days=int(date_arg[1:]))
    return datetime.strptime(date_arg, "%Y-%m-%d")


def check_existing(page, asset_id: str, target: datetime) -> dict | None:
    """Return reservation dict if one already exists for this asset+date, else None."""
    page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)
    try:
        page.wait_for_selector("table tbody tr", timeout=8000)
        label = f"{target.strftime('%b')} {target.day}, {target.year}"
        for row in page.query_selector_all("table tbody tr"):
            asset_link = row.query_selector("td.asset-name-cell a")
            se_cell = row.query_selector("td.start-end-cell")
            if not asset_link or not se_cell:
                continue
            if (
                f"/asset/{asset_id}" in (asset_link.get_attribute("href") or "")
                and label in se_cell.text_content()
            ):
                resv_link = row.query_selector("td.resv-name-cell a")
                resv_href = resv_link.get_attribute("href") if resv_link else ""
                id_parts = [x for x in resv_href.split("/") if x.isdigit()]
                return {
                    "status": "already_exists",
                    "asset_id": asset_id,
                    "target_date": target.strftime("%Y-%m-%d"),
                    "reservation_id": id_parts[0] if id_parts else "",
                    "message": f"Reservation already exists for {target.strftime('%Y-%m-%d')} on asset {asset_id}",
                }
    except Exception:
        pass
    return None


def stage(page, asset_id: str, target: datetime, start_time: str, end_time: str) -> str:
    """
    Navigate to asset page, set date/time in picker, click APPLY.
    Returns the confirmed when_value string.
    Raises RuntimeError with booking_window_closed: prefix if date is out of window.
    """
    target_day = str(target.day)
    target_month_idx = str(target.month - 1)
    target_year = str(target.year)
    target_str = target.strftime("%Y-%m-%d")

    print(f"Navigating to asset {asset_id}...", file=sys.stderr)
    page.goto(ASSET_URL.format(asset_id=asset_id), wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)

    if f"/asset/{asset_id}" not in page.url:
        raise RuntimeError(f"Unexpected URL after navigation: {page.url}")

    print("Opening date/time picker...", file=sys.stderr)
    page.locator("#resv_form_when").click()
    page.wait_for_selector(".when-popup", timeout=10000)
    page.wait_for_timeout(500)

    def nav_to_month(panel_index: int):
        expected = target.strftime("%B %Y")
        for _ in range(3):
            label = page.locator(".rdt.date-picker .rdtSwitch").nth(panel_index).text_content() or ""
            if expected in label:
                return
            print(f"Panel {panel_index}: advancing from {label}...", file=sys.stderr)
            page.locator(".rdt.date-picker .rdtNext").nth(panel_index).click()
            page.wait_for_timeout(300)
        if expected not in (page.locator(".rdt.date-picker .rdtSwitch").nth(panel_index).text_content() or ""):
            raise RuntimeError(f"Could not navigate panel {panel_index} to {expected}")

    def click_day(panel_index: int):
        sel = (
            f'td.rdtDay[data-value="{target_day}"]'
            f'[data-month="{target_month_idx}"][data-year="{target_year}"]'
        )
        cells = page.locator(sel)
        if cells.count() == 0:
            raise RuntimeError(f"Day cell not found for {target_str}")
        cell = cells.nth(panel_index if panel_index < cells.count() else 0)
        if "rdtDisabled" in (cell.get_attribute("class") or ""):
            raise RuntimeError(f"Date {target_str} is disabled — outside 7-day booking window")
        print(f"Selecting day {target_day} (panel {panel_index})...", file=sys.stderr)
        cell.click()
        page.wait_for_timeout(500)

    nav_to_month(0)
    click_day(0)

    time_selectors = page.locator(".when-popup .time-selector")
    start_opt = time_selectors.nth(0).locator(".time-selector-option").filter(has_text=start_time).first
    start_opt.scroll_into_view_if_needed()
    start_opt.click()
    page.wait_for_timeout(500)

    nav_to_month(1)
    click_day(1)

    end_opts = time_selectors.nth(1).locator(".time-selector-option")
    for i in range(end_opts.count()):
        opt = end_opts.nth(i)
        if opt.text_content().strip().startswith(end_time):
            opt.scroll_into_view_if_needed()
            opt.click()
            print(f"Selected end time: {opt.text_content().strip()}", file=sys.stderr)
            break
    else:
        raise RuntimeError(f"End time option starting with '{end_time}' not found")
    page.wait_for_timeout(300)

    print("Clicking APPLY...", file=sys.stderr)
    page.locator(".when-popup .save-button").click()
    page.wait_for_timeout(1000)

    # Booking window error appears inside the popup
    error_el = page.locator(".popup .error-message.font-error")
    if error_el.count() > 0:
        error_text = error_el.first.text_content().strip()
        print(f"Booking window error: {error_text}", file=sys.stderr)
        raise RuntimeError(f"booking_window_closed: {error_text}")

    if page.locator(".when-popup").is_visible():
        raise RuntimeError(
            f"booking_window_closed: {target_str} is not yet bookable "
            f"(booking window opens at midnight exactly 7 days before)"
        )

    page.wait_for_timeout(500)
    when_value = page.locator("#resv_form_when").get_attribute("value") or ""
    print(f"Staged: {when_value}", file=sys.stderr)
    if target.strftime("%b").upper() not in when_value.upper():
        raise RuntimeError(
            f"booking_window_closed: {target_str} is not yet bookable — "
            f"when input shows: '{when_value}'"
        )
    return when_value


def submit_with_retries(
    page, target_str: str, asset_id: str, when_value: str,
    start_time: str, end_time: str,
) -> dict:
    """Click SUBMIT up to SUBMIT_RETRIES times. Returns on first definitive outcome."""
    last_error = ""
    target = datetime.strptime(target_str, "%Y-%m-%d")

    for attempt in range(1, SUBMIT_RETRIES + 1):
        try:
            print(
                f"SUBMIT attempt {attempt}/{SUBMIT_RETRIES} at "
                f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}...",
                file=sys.stderr,
            )
            page.locator('button[type="submit"]').filter(has_text="SUBMIT").click(timeout=10000)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            final_url = page.url

            # Asset unavailable — Agilquest renders error on the asset page
            error_el = page.locator(".error-message.font-error")
            if error_el.count() > 0:
                error_text = error_el.first.text_content().strip()
                print(f"Asset unavailable: {error_text}", file=sys.stderr)
                return {
                    "status": "asset_unavailable",
                    "asset_id": asset_id,
                    "target_date": target_str,
                    "when_value": when_value,
                    "attempts": attempt,
                    "message": error_text,
                    "url": final_url,
                }

            success = (
                final_url.rstrip("/").endswith("/home")
                or "myreservations" in final_url.lower()
                or "confirmation" in page.inner_text("body").lower()
                or "successfully" in page.inner_text("body").lower()
            )

            if success:
                print(f"SUBMIT succeeded on attempt {attempt}.", file=sys.stderr)
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "target_date": target_str,
                    "start_time": start_time,
                    "end_time": end_time,
                    "when_value": when_value,
                    "attempts": attempt,
                    "message": f"Reservation booked for {target_str} on asset {asset_id}",
                    "url": final_url,
                }

            last_error = f"Unexpected URL after submit: {final_url}"
            print(f"Attempt {attempt} inconclusive — {last_error}", file=sys.stderr)

            if attempt < SUBMIT_RETRIES:
                # Check whether booking silently succeeded before retrying
                print("Verifying reservation wasn't silently created...", file=sys.stderr)
                time.sleep(RETRY_DELAY_S)
                page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=30000)
                existing = check_existing(page, asset_id, target)
                if existing:
                    print(f"Reservation confirmed on attempt {attempt} — stopping.", file=sys.stderr)
                    return {
                        "status": "success",
                        "asset_id": asset_id,
                        "target_date": target_str,
                        "start_time": start_time,
                        "end_time": end_time,
                        "when_value": when_value,
                        "attempts": attempt,
                        "message": f"Reservation booked for {target_str} on asset {asset_id}",
                        "url": page.url,
                    }
                print("Not confirmed — re-staging for retry...", file=sys.stderr)
                page.goto(ASSET_URL.format(asset_id=asset_id), wait_until="domcontentloaded", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=30000)

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt} failed: {last_error}", file=sys.stderr)
            if attempt < SUBMIT_RETRIES:
                time.sleep(RETRY_DELAY_S)

    return {
        "status": "error",
        "asset_id": asset_id,
        "target_date": target_str,
        "when_value": when_value,
        "attempts": SUBMIT_RETRIES,
        "message": f"All {SUBMIT_RETRIES} submit attempts failed. Last: {last_error}",
    }


def book_with_fallbacks(
    assets: list[str],
    target: datetime,
    start_time: str,
    end_time: str,
    prestage: bool,
) -> dict:
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()
    target_str = target.strftime("%Y-%m-%d")

    print(
        f"{'[prestage] ' if prestage else ''}"
        f"Booking {target_str} {start_time}-{end_time} "
        f"(assets: {', '.join(assets)})...",
        file=sys.stderr,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            executable_path=chrome_path,
            args=["--disable-gpu", "--no-sandbox"],
        )
        try:
            page = browser.new_page()

            # Retry app launcher navigation — Chrome network stack can lag behind
            # the OS network stack after wake from sleep
            print("Authenticating via app launcher...", file=sys.stderr)
            for attempt in range(1, 6):
                try:
                    page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=30000)
                    break
                except Exception as e:
                    if attempt == 5:
                        raise
                    print(f"Auth attempt {attempt} failed ({e}), retrying in 20s...", file=sys.stderr)
                    time.sleep(20)

            if "microsoftonline" in page.url or "login.microsoft" in page.url:
                raise RuntimeError("Not authenticated — run setup_auth.py to establish session")

            tried = []
            for asset_id in assets:
                print(f"\n--- Trying asset {asset_id} ---", file=sys.stderr)

                # Idempotency check
                existing = check_existing(page, asset_id, target)
                if existing:
                    print(existing["message"], file=sys.stderr)
                    return existing

                # Stage the form
                try:
                    when_value = stage(page, asset_id, target, start_time, end_time)
                except RuntimeError as e:
                    msg = str(e)
                    if msg.startswith("booking_window_closed:"):
                        raise  # window not open yet — no point trying other assets
                    print(f"Stage failed for {asset_id}: {msg}", file=sys.stderr)
                    tried.append({"asset_id": asset_id, "status": "stage_error", "message": msg})
                    continue

                # Prestage sleep on first asset only
                if prestage and asset_id == assets[0]:
                    now = datetime.now()
                    fire_at = now.replace(hour=23, minute=59, second=58, microsecond=0)
                    if fire_at <= now:
                        print("Past fire time — submitting immediately.", file=sys.stderr)
                    else:
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

                result = submit_with_retries(page, target_str, asset_id, when_value, start_time, end_time)
                tried.append(result)

                if result["status"] in ("success", "already_exists"):
                    return result

                if result["status"] == "asset_unavailable":
                    print(f"Asset {asset_id} unavailable — trying next fallback...", file=sys.stderr)
                    continue

                # Any other error (unexpected) — stop
                return result

            # All assets exhausted
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

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--assets", default=",".join(DEFAULT_ASSETS),
        help=f"Comma-separated ordered asset IDs (default: {','.join(DEFAULT_ASSETS)})",
    )
    parser.add_argument(
        "--date", default="+7",
        help="Target date as YYYY-MM-DD or +N days from today (default: +7)",
    )
    parser.add_argument(
        "--start", default=DEFAULT_START,
        help=f"Start time e.g. '08:30 AM' (default: {DEFAULT_START})",
    )
    parser.add_argument(
        "--end", default=DEFAULT_END,
        help=f"End time e.g. '04:00 PM' (default: {DEFAULT_END})",
    )
    parser.add_argument(
        "--prestage", action="store_true",
        help="Stage form now, sleep until 23:59:58, then submit",
    )
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
        print(json.dumps(result, indent=2))
        if result["status"] in ("error", "all_unavailable"):
            sys.exit(1)
        if result["status"] == "asset_unavailable":
            sys.exit(1)
    except Exception as e:
        msg = str(e)
        status = "booking_window_closed" if msg.startswith("booking_window_closed:") else "error"
        print(json.dumps({"status": status, "message": msg}))
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1 if status == "error" else 0)


if __name__ == "__main__":
    main()
