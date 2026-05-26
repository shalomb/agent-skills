#!/usr/bin/env python3
"""
One-time interactive SSO setup for Agilquest.

Opens a headed Chrome window via Microsoft app launcher. After successful
login, saves auth state to auth.json for use by all headless scripts.

Usage:
  uv run src/setup_auth.py
"""

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from lib.browser import (
    APP_LAUNCHER, AGILQUEST_HOME, get_state_dir, get_auth_state_path,
    get_chrome_path, save_auth,
)


def clear_singleton_lock():
    lock = get_state_dir() / "user_data" / "SingletonLock"
    if lock.is_symlink() or lock.exists():
        import subprocess, time
        pid = None
        if lock.is_symlink():
            try:
                pid = int(str(lock.resolve()).rsplit("-", 1)[-1])
            except ValueError:
                pass
        if pid and subprocess.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0:
            print(f"Killing Chrome process {pid} holding SingletonLock...", file=sys.stderr)
            subprocess.run(["kill", str(pid)], capture_output=True)
            time.sleep(2)
        lock.unlink(missing_ok=True)
        print("SingletonLock cleared.", file=sys.stderr)


def main():
    chrome_path = get_chrome_path()
    state_dir = get_state_dir()

    print(f"Chrome:  {chrome_path}")
    print(f"Storage: {state_dir}")
    print()

    clear_singleton_lock()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(state_dir / "user_data"),
            headless=False,
            executable_path=chrome_path,
            # Mock keychain so cookies are readable by headless Playwright Chrome
            args=["--disable-gpu", "--use-mock-keychain", "--password-store=basic"],
        )
        try:
            page = browser.new_page()

            print("Step 1: Authenticating via Microsoft app launcher...")
            try:
                page.goto(APP_LAUNCHER, wait_until="load", timeout=30000)
            except Exception as e:
                print(f"Note: {e}", file=sys.stderr)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "login.agilquest.com" in page.url:
                print("✓ Already authenticated — cached session is valid.")
            else:
                print("✓ Browser opened. Please complete Entra SSO login.")
                print("  Waiting for redirect to Agilquest...")
                page.wait_for_url("**/login.agilquest.com/**", timeout=300000)
                print("✓ Redirected to Agilquest.")

            print("\nStep 2: Navigating to Agilquest home to confirm access...")
            page.goto(f"{AGILQUEST_HOME}/home", wait_until="load", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            if "agilquest.com" not in page.url:
                raise RuntimeError(f"Failed to reach Agilquest. URL: {page.url}")

            save_auth(browser)
            print("✓ Authentication successful — auth.json saved.")
            print("✓ Headless scripts (book_reservation.py etc.) are ready to run.")

        except Exception as e:
            print(f"✗ Setup failed: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
