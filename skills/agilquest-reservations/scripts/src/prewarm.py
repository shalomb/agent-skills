#!/usr/bin/env python3
"""
Browser pre-warm: open Chrome, hit app launcher and asset page, then close.

Runs at 23:51 — seeds OS DNS cache and Chrome's disk cache so the 23:55
warmup and 23:57 booking script find everything ready. No browser lock is
held after this exits.
"""

import sys
import os
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

APP_LAUNCHER = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"
ASSET_URL = "https://login.agilquest.com/asset/343"


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


def prewarm():
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

            # Navigate through app launcher — seeds DNS, session cookies, CDN cache
            print("Pre-warming via app launcher...", file=sys.stderr)
            # Use "commit" — fires on first byte received, doesn't wait for the
            # full Microsoft auth redirect chain (which takes >30s to complete)
            for attempt in range(1, 6):
                try:
                    page.goto(APP_LAUNCHER, wait_until="commit", timeout=30000)
                    print(f"App launcher commit on attempt {attempt}: {page.url}", file=sys.stderr)
                    # Let auth redirects run for a few seconds to warm the session
                    page.wait_for_timeout(5000)
                    print(f"After 5s: {page.url}", file=sys.stderr)
                    break
                except Exception as e:
                    if attempt == 5:
                        raise
                    print(f"Attempt {attempt} failed ({e}), retrying in 20s...", file=sys.stderr)
                    time.sleep(20)

            # Pre-load the asset page to warm CDN/DNS cache
            print("Pre-loading asset page...", file=sys.stderr)
            try:
                page.goto(ASSET_URL, wait_until="commit", timeout=30000)
                page.wait_for_timeout(3000)
                print(f"Asset page reached: {page.url}", file=sys.stderr)
            except Exception as e:
                print(f"Asset page warning (non-fatal): {e}", file=sys.stderr)

        finally:
            browser.close()
            print("Browser closed — DNS and session cache warm.", file=sys.stderr)


if __name__ == "__main__":
    prewarm()
