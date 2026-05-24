#!/usr/bin/env python3
"""One-time setup to establish Agilquest Entra SSO session."""

import sys
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
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

    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform == "linux":
        return "/usr/bin/google-chrome"
    else:
        return "chrome"


def clear_singleton_lock(user_data_dir: Path):
    """Remove stale Chrome SingletonLock so setup_auth can open the profile."""
    lock = user_data_dir / "SingletonLock"
    if lock.is_symlink() or lock.exists():
        import subprocess
        target = lock.resolve() if lock.is_symlink() else None
        pid = None
        if target:
            try:
                pid = int(str(target).rsplit("-", 1)[-1])
            except ValueError:
                pass
        if pid and subprocess.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0:
            print(f"Killing Chrome process {pid} holding SingletonLock...", file=sys.stderr)
            subprocess.run(["kill", str(pid)], capture_output=True)
            import time; time.sleep(2)
        lock.unlink(missing_ok=True)
        print("SingletonLock cleared.", file=sys.stderr)


def setup_auth():
    """Establish browser session by logging in via Microsoft app launcher then Agilquest."""
    user_data_dir = get_user_data_dir()
    chrome_path = get_chrome_path()

    print(f"Setting up Agilquest authentication...")
    print(f"Chrome path: {chrome_path}")
    print(f"Session storage: {user_data_dir}")
    print()

    clear_singleton_lock(user_data_dir)

    with sync_playwright() as p:
        # Launch in headed mode so user can log in
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,  # Show browser for manual login
            executable_path=chrome_path,
            args=["--disable-gpu"]
        )

        try:
            page = browser.new_page()

            # Step 1: Login via Microsoft app launcher
            print("Step 1: Authenticating via Microsoft app launcher...")
            app_launcher_url = "https://launcher.myapps.microsoft.com/api/signin/cb15e862-80aa-4d9c-95af-4748246cecd7?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"

            try:
                page.goto(app_launcher_url, wait_until="load", timeout=30000)
            except Exception as e:
                print(f"Note: {e}", file=sys.stderr)

            # Wait for page to actually have content (not just blank/loading)
            page.wait_for_load_state("networkidle", timeout=30000)

            current_url = page.url
            print(f"✓ Loaded page at: {current_url}")

            # Check if we got redirected to Agilquest (already logged in via cached session)
            if "login.agilquest.com" in current_url:
                print("✓ Already authenticated! Cached session is valid.")
            else:
                print("✓ Browser opened. Please complete Entra SSO login.")
                print("✓ After login, you'll be redirected to Agilquest.")
                print("✓ Waiting for redirect...\n")

                # Wait for redirect to Agilquest after app launcher auth
                page.wait_for_url("**/login.agilquest.com/**", timeout=300000)
                print("✓ Redirected to Agilquest!")

            # Step 2: Navigate to asset page to confirm access
            print("\nStep 2: Navigating to Agilquest asset page...")
            page.goto("https://login.agilquest.com/asset/343", wait_until="load", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # Verify we're actually on the asset page (not a login page)
            if "asset" in page.url.lower() or "agilquest" in page.url.lower():
                print("✓ Authentication successful! Session saved.")
                print(f"✓ You can now run: uv run src/get_reservations.py\n")
            else:
                raise RuntimeError(f"Failed to reach asset page. Current URL: {page.url}")

        except Exception as e:
            print(f"✗ Setup failed: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    setup_auth()
