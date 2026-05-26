#!/usr/bin/env python3
"""List active Agilquest reservations.

Usage:
  uv run src/get_reservations.py
"""

import sys
import json

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from lib.browser import launch_headless, verify_auth
from lib.agilquest import get_reservations


def main():
    with sync_playwright() as p:
        browser = launch_headless(p)
        try:
            page = browser.new_page()
            print("Checking auth...", file=sys.stderr)
            if not verify_auth(page):
                print("Session invalid — run: uv run src/setup_auth.py", file=sys.stderr)
                sys.exit(1)
            reservations = get_reservations(page)
            print(json.dumps(reservations, indent=2))
        finally:
            browser.close()


if __name__ == "__main__":
    main()
