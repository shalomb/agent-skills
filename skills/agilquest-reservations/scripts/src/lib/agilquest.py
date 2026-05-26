"""Agilquest page interactions: reservations, staging, submitting."""

import sys
import time
from datetime import datetime

RESERVATIONS_URL = "https://login.agilquest.com/myreservations/active?viewMode=table"
ASSET_URL = "https://login.agilquest.com/asset/{asset_id}"

SUBMIT_RETRIES = 3
RETRY_DELAY_S = 5


def get_reservations(page) -> list[dict]:
    """Scrape the active reservations table. Returns list of reservation dicts."""
    page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
    reservations = []
    try:
        page.wait_for_selector("table tbody tr", timeout=10000)
        for row in page.query_selector_all("table tbody tr"):
            resv_link = row.query_selector("td.resv-name-cell a")
            asset_link = row.query_selector("td.asset-name-cell a")
            se_cell = row.query_selector("td.start-end-cell")
            status_cell = row.query_selector("td.status-cell")
            location_cell = row.query_selector("td.location-cell")

            asset_href = asset_link.get_attribute("href") if asset_link else ""
            resv_href = resv_link.get_attribute("href") if resv_link else ""
            id_parts = [x for x in resv_href.split("/") if x.isdigit()]
            spans = se_cell.query_selector_all("span") if se_cell else []

            reservations.append({
                "id": id_parts[0] if id_parts else "",
                "name": resv_link.text_content().strip() if resv_link else "",
                "asset": asset_link.text_content().strip() if asset_link else "",
                "asset_href": asset_href,
                "location": location_cell.text_content().strip() if location_cell else "",
                "start": spans[0].text_content().strip() if len(spans) > 0 else "",
                "end": spans[1].text_content().strip() if len(spans) > 1 else "",
                "status": status_cell.text_content().strip() if status_cell else "",
            })
    except Exception:
        pass
    return reservations


def find_existing(reservations: list[dict], asset_id: str, target: datetime) -> dict | None:
    """Return matching reservation if one exists for asset_id on target date."""
    label = target.strftime("%B %d, %Y")  # "June 01, 2026" — zero-padded, matches table
    for r in reservations:
        if f"/asset/{asset_id}" in r.get("asset_href", "") and label in r.get("start", ""):
            return r
    return None


def stage(page, asset_id: str, target: datetime, start_time: str, end_time: str) -> str:
    """
    Navigate to asset page, fill date/time picker, click APPLY.
    Returns the confirmed when_value string.
    Raises RuntimeError("booking_window_closed: ...") if date not yet bookable.
    Raises RuntimeError("auth_required") if redirected away from asset page.
    """
    target_day = str(target.day)
    target_month_idx = str(target.month - 1)
    target_year = str(target.year)
    target_str = target.strftime("%Y-%m-%d")
    url = ASSET_URL.format(asset_id=asset_id)

    print(f"Navigating to asset {asset_id}...", file=sys.stderr)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    if f"/asset/{asset_id}" not in page.url:
        if "microsoftonline" in page.url or "login.microsoft" in page.url:
            raise RuntimeError("auth_required")
        if page.url.rstrip("/") == "https://login.agilquest.com":
            raise RuntimeError("auth_required")
        raise RuntimeError(f"Unexpected URL after navigation: {page.url}")

    print("Opening date/time picker...", file=sys.stderr)
    page.wait_for_selector("#resv_form_when", timeout=20000)
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
            raise RuntimeError(f"booking_window_closed: {target_str} is outside the 7-day booking window")
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
        raise RuntimeError(f"End time '{end_time}' not found in picker")
    page.wait_for_timeout(300)

    print("Clicking APPLY...", file=sys.stderr)
    page.locator(".when-popup .save-button").click()
    page.wait_for_timeout(1000)

    error_el = page.locator(".popup .error-message.font-error")
    if error_el.count() > 0:
        raise RuntimeError(f"booking_window_closed: {error_el.first.text_content().strip()}")

    if page.locator(".when-popup").is_visible():
        raise RuntimeError(
            f"booking_window_closed: {target_str} not yet bookable "
            "(booking window opens at midnight exactly 7 days before)"
        )

    page.wait_for_timeout(500)
    when_value = page.locator("#resv_form_when").get_attribute("value") or ""
    print(f"Staged: {when_value}", file=sys.stderr)
    if target.strftime("%b").upper() not in when_value.upper():
        raise RuntimeError(
            f"booking_window_closed: {target_str} not yet bookable — "
            f"when input shows: '{when_value}'"
        )

    # Uncheck Private — checked by default; JS click bypasses viewport constraints.
    private_cb = page.locator("#res-private")
    if private_cb.is_checked():
        print("Unchecking Private...", file=sys.stderr)
        page.evaluate("document.querySelector('#res-private').click()")
        page.wait_for_timeout(300)

    return when_value


def submit_with_retries(
    page, asset_id: str, target_str: str, when_value: str,
    start_time: str, end_time: str,
) -> dict:
    """Click SUBMIT up to SUBMIT_RETRIES times. Returns on first definitive outcome."""
    target = datetime.strptime(target_str, "%Y-%m-%d")
    last_error = ""

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
                print("Verifying reservation wasn't silently created...", file=sys.stderr)
                time.sleep(RETRY_DELAY_S)
                reservations = get_reservations(page)
                existing = find_existing(reservations, asset_id, target)
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

        except Exception as e:
            last_error = str(e).splitlines()[0]
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
