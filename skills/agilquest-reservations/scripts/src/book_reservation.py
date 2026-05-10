#!/usr/bin/env python3
"""
Book a reservation 7 days in advance on Agilquest.

Normal cron flow (two jobs):
  23:57  warmup.py           — auth check + preload
  23:57  book_reservation.py --prestage
                             — auth, navigate, stage date/time, sleep until
                               23:59:58, then SUBMIT with up to 3 retries
  (the --prestage job holds the browser open across the minute boundary)

Alternatively run without --prestage for an immediate book (used by
ensure_reservation.py as a fallback).
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
START_TIME = "09:00 AM"
END_TIME = "06:00 PM"
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


def check_existing(page, asset_id: str, target: datetime) -> dict | None:
    """Return existing reservation dict if one already exists for target date, else None."""
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
                    "message": f"Reservation already exists for {target.strftime('%Y-%m-%d')}",
                }
    except Exception:
        pass
    return None


def stage(page, asset_id: str, target: datetime) -> str:
    """
    Navigate to asset page, fill in date/time picker, click APPLY.
    Returns the confirmed when_value string.
    Does NOT click SUBMIT — caller decides when to fire that.
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
    start_opt = time_selectors.nth(0).locator(".time-selector-option").filter(has_text=START_TIME).first
    start_opt.scroll_into_view_if_needed()
    start_opt.click()
    page.wait_for_timeout(500)

    nav_to_month(1)
    click_day(1)

    end_opts = time_selectors.nth(1).locator(".time-selector-option")
    for i in range(end_opts.count()):
        opt = end_opts.nth(i)
        if opt.text_content().strip().startswith(END_TIME):
            opt.scroll_into_view_if_needed()
            opt.click()
            print(f"Selected end time: {opt.text_content().strip()}", file=sys.stderr)
            break
    else:
        raise RuntimeError(f"End time option starting with '{END_TIME}' not found")
    page.wait_for_timeout(300)

    print("Clicking APPLY...", file=sys.stderr)
    page.locator(".when-popup .save-button").click()
    page.wait_for_timeout(1000)

    # Check for the explicit booking-window error Agilquest shows inside the popup
    error_el = page.locator(".popup .error-message.font-error")
    if error_el.count() > 0:
        error_text = error_el.first.text_content().strip()
        print(f"Booking window error: {error_text}", file=sys.stderr)
        raise RuntimeError(f"booking_window_closed: {error_text}")

    # Fallback: if popup is still visible with no error text, the date was also rejected
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


def submit_with_retries(page, target_str: str, asset_id: str, when_value: str) -> dict:
    """Click SUBMIT up to SUBMIT_RETRIES times, returning on first success."""
    last_error = ""
    for attempt in range(1, SUBMIT_RETRIES + 1):
        try:
            print(f"SUBMIT attempt {attempt}/{SUBMIT_RETRIES} at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}...", file=sys.stderr)
            page.locator('button[type="submit"]').filter(has_text="SUBMIT").click(timeout=10000)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            final_url = page.url
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
                    "start_time": START_TIME,
                    "end_time": END_TIME,
                    "when_value": when_value,
                    "attempts": attempt,
                    "message": f"Reservation booked for {target_str}",
                    "url": final_url,
                }

            last_error = f"Unexpected URL after submit: {final_url}"
            print(f"Attempt {attempt} inconclusive — {last_error}", file=sys.stderr)

            # Navigate back to asset page to retry
            if attempt < SUBMIT_RETRIES:
                print(f"Returning to asset page for retry in {RETRY_DELAY_S}s...", file=sys.stderr)
                time.sleep(RETRY_DELAY_S)
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
        "message": f"All {SUBMIT_RETRIES} submit attempts failed. Last error: {last_error}",
    }


def book_reservation(asset_id: str = "343", prestage: bool = False) -> dict:
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()
    target = datetime.now() + timedelta(days=7)
    target_str = target.strftime("%Y-%m-%d")

    print(f"{'[prestage] ' if prestage else ''}Booking asset {asset_id} for {target_str} ({START_TIME}-{END_TIME})...", file=sys.stderr)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            executable_path=chrome_path,
            args=["--disable-gpu", "--no-sandbox"],
        )
        try:
            page = browser.new_page()

            print("Authenticating via app launcher...", file=sys.stderr)
            page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "microsoftonline" in page.url or "login.microsoft" in page.url:
                raise RuntimeError("Not authenticated — run setup_auth.py to establish session")

            existing = check_existing(page, asset_id, target)
            if existing:
                print(existing["message"], file=sys.stderr)
                return existing

            when_value = stage(page, asset_id, target)

            if prestage:
                # Sleep until 23:59:58, then fire SUBMIT
                now = datetime.now()
                fire_at = now.replace(hour=23, minute=59, second=58, microsecond=0)
                if fire_at <= now:
                    # Already past 23:59:58 (e.g. running in testing) — fire immediately
                    print("Past fire time — submitting immediately.", file=sys.stderr)
                else:
                    wait_s = (fire_at - now).total_seconds()
                    print(f"Staged. Sleeping {wait_s:.1f}s until {fire_at.strftime('%H:%M:%S')}...", file=sys.stderr)
                    time.sleep(wait_s)
                    print(f"Firing SUBMIT at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}.", file=sys.stderr)

            return submit_with_retries(page, target_str, asset_id, when_value)

        finally:
            browser.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_id", nargs="?", default="343")
    parser.add_argument("--prestage", action="store_true",
                        help="Stage form now, sleep until 23:59:58, then submit")
    args = parser.parse_args()

    try:
        result = book_reservation(args.asset_id, prestage=args.prestage)
        print(json.dumps(result, indent=2))
        if result["status"] == "error":
            sys.exit(1)
    except Exception as e:
        msg = str(e)
        status = "booking_window_closed" if msg.startswith("booking_window_closed:") else "error"
        print(json.dumps({"status": status, "message": msg}))
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1 if status == "error" else 0)


if __name__ == "__main__":
    main()
