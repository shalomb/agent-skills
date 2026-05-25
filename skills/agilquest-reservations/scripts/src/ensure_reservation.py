#!/usr/bin/env python3
"""
Daily 14:00 health-check: verify Entra SSO session, confirm the 7-days-ahead
reservation exists (booking it if missing), and print active reservations.

If the session has lapsed, launches a headed Chrome window so you can
complete Entra SSO interactively while you're at your desk, then re-runs
the reservation check automatically once auth is restored.
"""

import sys
import json
import os
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

APP_LAUNCHER = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"
ASSET_ID = "343"
ASSET_URL = f"https://login.agilquest.com/asset/{ASSET_ID}"
RESERVATIONS_URL = "https://login.agilquest.com/myreservations/active?viewMode=table"
START_TIME = "09:00 AM"
END_TIME = "06:00 PM"


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


def launch_browser(p, headless: bool, user_data_dir: Path, chrome_path: str):
    return p.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=headless,
        executable_path=chrome_path,
        args=["--disable-gpu"] + (["--no-sandbox"] if headless else []),
    )


def is_auth_ok(page) -> bool:
    return "microsoftonline" not in page.url and "login.microsoft" not in page.url


def get_active_reservations(page) -> list[dict]:
    page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)
    reservations = []
    try:
        page.wait_for_selector("table tbody tr", timeout=8000)
        for row in page.query_selector_all("table tbody tr"):
            resv_link = row.query_selector("td.resv-name-cell a")
            asset_link = row.query_selector("td.asset-name-cell a")
            se_cell = row.query_selector("td.start-end-cell")
            status_cell = row.query_selector("td.status-cell")

            asset_href = asset_link.get_attribute("href") if asset_link else ""
            spans = se_cell.query_selector_all("span") if se_cell else []
            resv_href = resv_link.get_attribute("href") if resv_link else ""
            id_parts = [x for x in resv_href.split("/") if x.isdigit()]

            reservations.append({
                "id": id_parts[0] if id_parts else "",
                "asset": asset_link.text_content().strip() if asset_link else "",
                "asset_href": asset_href,
                "start": spans[0].text_content().strip() if len(spans) > 0 else "",
                "end": spans[1].text_content().strip() if len(spans) > 1 else "",
                "status": status_cell.text_content().strip() if status_cell else "",
            })
    except Exception:
        pass
    return reservations


def reservation_exists_for_target(reservations: list[dict], target: datetime) -> dict | None:
    label = target.strftime("%B %-d, %Y")  # "June 1, 2026" — matches full month name in table
    for r in reservations:
        if f"/asset/{ASSET_ID}" in r.get("asset_href", "") and label in r.get("start", ""):
            return r
    return None


def book(page, target: datetime) -> dict:
    target_day = str(target.day)
    target_month_idx = str(target.month - 1)
    target_year = str(target.year)
    target_str = target.strftime("%Y-%m-%d")

    print(f"Booking asset {ASSET_ID} for {target_str}...", file=sys.stderr)
    page.goto(ASSET_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)

    if f"/asset/{ASSET_ID}" not in page.url:
        raise RuntimeError(f"Unexpected URL: {page.url}")

    page.locator("#resv_form_when").click()
    page.wait_for_selector(".when-popup", timeout=10000)
    page.wait_for_timeout(500)

    def nav_to_month(panel_index: int):
        expected = target.strftime("%B %Y")
        for _ in range(3):
            label = page.locator(".rdt.date-picker .rdtSwitch").nth(panel_index).text_content() or ""
            if expected in label:
                return
            page.locator(".rdt.date-picker .rdtNext").nth(panel_index).click()
            page.wait_for_timeout(300)
        label = page.locator(".rdt.date-picker .rdtSwitch").nth(panel_index).text_content() or ""
        if expected not in label:
            raise RuntimeError(f"Could not navigate panel {panel_index} to {expected}")

    def click_day(panel_index: int):
        sel = f'td.rdtDay[data-value="{target_day}"][data-month="{target_month_idx}"][data-year="{target_year}"]'
        cells = page.locator(sel)
        if cells.count() == 0:
            raise RuntimeError(f"Day cell not found for {target_str}")
        cell = cells.nth(panel_index if panel_index < cells.count() else 0)
        if "rdtDisabled" in (cell.get_attribute("class") or ""):
            raise RuntimeError(f"Date {target_str} is disabled — outside booking window")
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
            break
    page.wait_for_timeout(300)

    page.locator(".when-popup .save-button").click()
    page.wait_for_selector(".when-popup", state="hidden", timeout=10000)
    page.wait_for_timeout(500)

    when_value = page.locator("#resv_form_when").get_attribute("value") or ""
    print(f"Time window set: {when_value}", file=sys.stderr)

    # Ensure reservation is not private (checkbox is checked by default).
    # Use JS dispatch to avoid viewport constraints in headless mode.
    private_cb = page.locator("#res-private")
    if private_cb.is_checked():
        print("Unchecking Private...", file=sys.stderr)
        page.evaluate("document.querySelector('#res-private').click()")
        page.wait_for_timeout(300)

    page.locator('button[type="submit"]').filter(has_text="SUBMIT").click()
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    success = page.url.rstrip("/").endswith("/home") or "myreservations" in page.url
    return {
        "status": "booked" if success else "submitted",
        "target_date": target_str,
        "when_value": when_value,
    }


def interactive_reauth(user_data_dir: Path, chrome_path: str) -> bool:
    """
    Launch setup_auth.py in a Terminal window via osascript so the user can
    complete Entra SSO using the correct Playwright Chrome profile.

    osascript routes through the macOS Aqua session and works from cron.
    setup_auth.py clears any stale SingletonLock and opens a headed Playwright
    Chrome window pointed at the correct user_data_dir.

    Polls headlessly every 10s for up to 5 minutes until session is valid.
    """
    scripts_dir = Path(__file__).parent.parent
    print("\nSession has lapsed — opening Terminal to run setup_auth.py...", file=sys.stderr)
    subprocess.Popen([
        "/usr/bin/osascript", "-e",
        f'tell application "Terminal" to do script "cd {scripts_dir} && uv run src/setup_auth.py"'
    ])
    print("Terminal opened. Waiting up to 5 minutes for SSO to complete...", file=sys.stderr)

    # Poll headlessly until setup_auth has saved a valid session
    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(10)
        try:
            with sync_playwright() as p:
                browser = launch_browser(p, headless=True, user_data_dir=user_data_dir, chrome_path=chrome_path)
                try:
                    page = browser.new_page()
                    page.goto(APP_LAUNCHER, wait_until="commit", timeout=15000)
                    time.sleep(3)
                    if "login.agilquest.com" in page.url:
                        print("Session restored — auth complete.", file=sys.stderr)
                        return True
                finally:
                    browser.close()
        except Exception:
            pass  # lock contention while setup_auth is running — keep polling

    print("Re-auth timed out after 5 minutes.", file=sys.stderr)
    return False


AUTH_RETRIES = 5
AUTH_RETRY_DELAY = 20  # seconds


def run_checks(headless: bool = True) -> dict:
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()
    target = datetime.now() + timedelta(days=7)
    target_str = target.strftime("%Y-%m-%d")

    with sync_playwright() as p:
        browser = launch_browser(p, headless=headless, user_data_dir=user_data_dir, chrome_path=chrome_path)
        try:
            page = browser.new_page()

            print("Checking auth via app launcher...", file=sys.stderr)
            last_exc = None
            for attempt in range(1, AUTH_RETRIES + 1):
                try:
                    page.goto(APP_LAUNCHER, wait_until="commit", timeout=45000)
                    page.wait_for_load_state("networkidle", timeout=45000)
                    last_exc = None
                    break
                except Exception as e:
                    last_exc = e
                    print(
                        f"Auth navigation attempt {attempt}/{AUTH_RETRIES} failed: {e}",
                        file=sys.stderr,
                    )
                    if attempt < AUTH_RETRIES:
                        time.sleep(AUTH_RETRY_DELAY)
            if last_exc:
                raise RuntimeError(f"App launcher unreachable after {AUTH_RETRIES} attempts: {last_exc}")

            if not is_auth_ok(page):
                return {"status": "auth_required", "url": page.url}

            # Check whether target reservation already exists
            print(f"Checking reservations for {target_str}...", file=sys.stderr)
            reservations = get_active_reservations(page)
            existing = reservation_exists_for_target(reservations, target)

            booking_result = None
            if existing:
                print(f"Reservation {existing['id']} already exists for {target_str}.", file=sys.stderr)
            else:
                print(f"No reservation found for {target_str} — booking now...", file=sys.stderr)
                booking_result = book(page, target)
                # Refresh reservation list after booking
                reservations = get_active_reservations(page)
                existing = reservation_exists_for_target(reservations, target)

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
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()

    result = run_checks(headless=True)

    if result["status"] == "auth_required":
        # Session lapsed — prompt interactive re-auth then re-run checks
        reauthed = interactive_reauth(user_data_dir, chrome_path)
        if not reauthed:
            print(json.dumps({"status": "error", "message": "Re-auth failed or timed out"}))
            sys.exit(1)
        result = run_checks(headless=True)

    print(json.dumps(result, indent=2))

    if result["status"] != "ok" or not result.get("reservation"):
        print("\nWARNING: No confirmed reservation for target date.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
