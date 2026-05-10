#!/usr/bin/env python3
"""Retrieve active reservations from Agilquest portal."""

import json
import sys
import argparse
from pathlib import Path
import os

try:
    from playwright.sync_api import sync_playwright, BrowserContext
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)


def get_user_data_dir() -> Path:
    """Get XDG-compliant user data directory for browser session."""
    xdg_state = os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")
    user_data = Path(xdg_state) / "agent-skills" / "agilquest-reservations" / "user_data"
    user_data.mkdir(parents=True, exist_ok=True)
    return user_data


def get_chrome_path() -> str:
    """Get Chrome executable path from env or system defaults."""
    env_path = os.getenv("CHROME_PATH")
    if env_path:
        return env_path

    # Platform-specific defaults
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform == "linux":
        return "/usr/bin/google-chrome"
    else:
        return "chrome"  # Windows will find it in PATH


def extract_reservations_table(page) -> list[dict]:
    """Extract reservation data from the table on myreservations/active page."""
    reservations = []

    try:
        page.wait_for_selector("table tbody tr", timeout=10000)
    except Exception as e:
        print(f"Warning: Table not found - {e}", file=sys.stderr)
        return reservations

    rows = page.query_selector_all("table tbody tr")
    for row in rows:
        try:
            def cell_text(cls):
                el = row.query_selector(f"td.{cls}")
                return el.text_content().strip() if el else ""

            name = cell_text("resv-name-cell")
            # Extract reservation ID from the link in resv-name-cell
            resv_link = row.query_selector("td.resv-name-cell a")
            resv_id = ""
            if resv_link:
                href = resv_link.get_attribute("href") or ""
                parts_href = [p for p in href.split("/") if p.isdigit()]
                resv_id = parts_href[0] if parts_href else ""
            asset = cell_text("asset-name-cell")
            location = cell_text("location-name-cell")
            date_time_raw = cell_text("start-end-cell")
            status = cell_text("status-cell")
            owner = cell_text("user-name-cell")

            if not asset:
                continue

            # start-end-cell has two <span> elements (start and end datetime)
            se_cell = row.query_selector("td.start-end-cell")
            spans = se_cell.query_selector_all("span") if se_cell else []
            start_dt = spans[0].text_content().strip() if len(spans) > 0 else date_time_raw
            end_dt = spans[1].text_content().strip() if len(spans) > 1 else ""

            reservations.append({
                "id": resv_id,
                "name": name,
                "asset": asset,
                "location": location,
                "start": start_dt,
                "end": end_dt,
                "status": status,
                "owner": owner,
            })
        except Exception as e:
            print(f"Warning: Failed to parse row - {e}", file=sys.stderr)

    return reservations


def get_reservations(asset_id: str = None) -> list[dict]:
    """Fetch active reservations from Agilquest."""
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()

    with sync_playwright() as p:
        # Launch with persistent user data (reuses cached Entra session)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            executable_path=chrome_path,
            args=["--disable-gpu", "--no-sandbox"]
        )

        try:
            page = browser.new_page()

            # CRITICAL: Always go through Microsoft app launcher first for auth
            app_launcher_url = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"
            print(f"Authenticating via app launcher...", file=sys.stderr)
            page.goto(app_launcher_url, wait_until="load", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # Navigate to Agilquest
            if asset_id:
                url = f"https://login.agilquest.com/asset/{asset_id}"
            else:
                url = "https://login.agilquest.com/myreservations/active?viewMode=table"

            print(f"Fetching {url}...", file=sys.stderr)
            page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # Check if logged in
            if "login" in page.url.lower() and "agilquest" not in page.url.lower():
                raise RuntimeError("Not logged in - run setup_auth.py first")

            # Extract reservations
            reservations = extract_reservations_table(page)

            return reservations

        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch active reservations from Agilquest"
    )
    parser.add_argument(
        "--asset-id",
        help="Specific workspace asset ID (e.g., 343)"
    )

    args = parser.parse_args()

    try:
        reservations = get_reservations(asset_id=args.asset_id)
        print(json.dumps(reservations, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
