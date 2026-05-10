#!/usr/bin/env python3
"""
Pre-booking warmup: verify Entra SSO auth and pre-load the asset page.

Run at 23:59 before the 00:00 booking attempt. Exits 0 if session is healthy,
non-zero if auth has lapsed (so cron/monitoring can alert you to re-run
setup_auth.py interactively before midnight).
"""

import sys
import json
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

APP_LAUNCHER = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"
ASSET_URL = "https://login.agilquest.com/asset/343"
RESERVATIONS_URL = "https://login.agilquest.com/myreservations/active?viewMode=table"


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


def warmup() -> dict:
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            executable_path=chrome_path,
            args=["--disable-gpu", "--no-sandbox"],
        )
        try:
            page = browser.new_page()

            # Step 1: app launcher — must always go through this first
            print("Warming up via app launcher...", file=sys.stderr)
            page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "microsoftonline" in page.url or "login.microsoft" in page.url:
                return {
                    "status": "auth_required",
                    "message": (
                        "Entra SSO session has lapsed. "
                        "Run: uv run src/setup_auth.py"
                    ),
                    "url": page.url,
                }

            # Step 2: pre-load the asset page so it's warm in the browser cache
            print("Pre-loading asset page...", file=sys.stderr)
            page.goto(ASSET_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "/asset/" not in page.url:
                return {
                    "status": "auth_required",
                    "message": f"Redirected away from asset page to: {page.url}",
                    "url": page.url,
                }

            # Step 3: verify reservations page is also reachable
            print("Verifying reservations page...", file=sys.stderr)
            page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "myreservations" not in page.url:
                return {
                    "status": "auth_required",
                    "message": f"Redirected away from reservations page to: {page.url}",
                    "url": page.url,
                }

            return {
                "status": "ok",
                "message": "Session healthy — ready for 00:00 booking",
            }

        finally:
            browser.close()


def main():
    result = warmup()
    print(json.dumps(result, indent=2))
    if result["status"] != "ok":
        print(
            f"\nACTION REQUIRED: {result['message']}\n"
            f"Run interactively: cd {Path(__file__).parent.parent} && uv run src/setup_auth.py",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
