#!/usr/bin/env python3
"""
Browser pre-warm: seed OS DNS cache and warm Chrome's network stack.

Runs at 23:51 — 4 minutes before warmup.py, 6 before book_reservation.py.
Strategy: open Chrome headless, do a lightweight TLS connect to each domain
we'll need, then close. This populates the OS DNS cache and Chrome's disk
cache so subsequent scripts connect immediately.

We also warm Chrome's DNS resolver against the MS app launcher URL using
wait_until="commit" so book_reservation.py finds a warm connection at 23:57.
"""

import sys
import os
import time
import ssl
import socket
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

DOMAINS = [
    "launcher.myapps.microsoft.com",
    "login.microsoftonline.com",
    "login.agilquest.com",
    "auth.agilquest.com",
]
ASSET_URL = "https://login.agilquest.com/asset/343"
APP_LAUNCHER = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"


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


def seed_dns(domains: list[str]):
    """Make TLS connections to seed OS DNS cache for all target domains."""
    ctx = ssl.create_default_context()
    for domain in domains:
        for attempt in range(1, 4):
            try:
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=domain):
                        print(f"  DNS/TLS seeded: {domain}", file=sys.stderr)
                        break
            except Exception as e:
                if attempt == 3:
                    print(f"  Warning: could not seed {domain}: {e}", file=sys.stderr)
                else:
                    time.sleep(3)


def warm_chrome(user_data_dir: Path, chrome_path: str):
    """Open Chrome, navigate to the asset page, then close."""
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            executable_path=chrome_path,
            args=["--disable-gpu", "--no-sandbox"],
        )
        try:
            page = browser.new_page()
            # Give Chrome's NetworkService time to initialise
            print("Waiting for Chrome network service...", file=sys.stderr)
            time.sleep(8)

            # Warm Chrome's internal DNS resolver for both the MS launcher and
            # the asset page — OS DNS seed alone doesn't warm Chrome's resolver.
            for label, url in [("launcher", APP_LAUNCHER), ("asset page", ASSET_URL)]:
                print(f"Loading {label} to warm Chrome cache...", file=sys.stderr)
                for attempt in range(1, 4):
                    try:
                        page.goto(url, wait_until="commit", timeout=20000)
                        print(f"  {label} commit on attempt {attempt}: {page.url}", file=sys.stderr)
                        page.wait_for_timeout(2000)
                        break
                    except Exception as e:
                        if attempt == 3:
                            print(f"  Chrome warm warning (non-fatal): {e}", file=sys.stderr)
                        else:
                            print(f"  Attempt {attempt} failed, retrying...", file=sys.stderr)
                            time.sleep(5)
        finally:
            browser.close()
            print("Chrome closed — cache warm.", file=sys.stderr)


def prewarm():
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()

    print("Step 1: Seeding OS DNS cache via TLS connects...", file=sys.stderr)
    seed_dns(DOMAINS)

    print("Step 2: Warming Chrome network stack...", file=sys.stderr)
    warm_chrome(user_data_dir, chrome_path)

    print("Pre-warm complete.", file=sys.stderr)


if __name__ == "__main__":
    prewarm()
