"""Browser launch and auth-state helpers shared across all entry points."""

import os
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, BrowserContext
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

# Every headless session must start via this URL to establish a fresh
# Agilquest session through MS SSO. The Agilquest session lasts ~10 minutes,
# but the MS tokens in user_data_dir persist across days.
APP_LAUNCHER = (
    "https://launcher.myapps.microsoft.com/api/signin/"
    "cb15e862-80aa-4d9c-95af-4748246cecd7"
    "?tenantId=57fdf63b-7e22-45a3-83dc-d37003163aae"
)
AGILQUEST_HOME = "https://login.agilquest.com"


def get_state_dir() -> Path:
    xdg = os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")
    d = Path(xdg) / "agent-skills" / "agilquest-reservations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_chrome_path() -> str:
    if env := os.getenv("CHROME_PATH"):
        return env
    return (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if sys.platform == "darwin"
        else "/usr/bin/google-chrome"
    )


def _persistent_context(p, headless: bool, extra_args: list[str] | None = None) -> BrowserContext:
    args = ["--disable-gpu", "--no-sandbox"] + (extra_args or [])
    return p.chromium.launch_persistent_context(
        user_data_dir=str(get_state_dir() / "user_data"),
        headless=headless,
        executable_path=get_chrome_path(),
        args=args,
    )


def launch_headless(p) -> BrowserContext:
    """Launch headless using the persistent user_data_dir (MS tokens survive here).
    Always go through APP_LAUNCHER to establish a fresh Agilquest session.
    """
    return _persistent_context(p, headless=True)


def launch_headed(p) -> BrowserContext:
    """Launch headed for interactive SSO. --use-mock-keychain keeps cookies
    in a format the headless persistent context can also read."""
    return _persistent_context(
        p, headless=False,
        extra_args=["--use-mock-keychain", "--password-store=basic"],
    )


def is_on_agilquest(page) -> bool:
    """True if the current page is on Agilquest (not an MS login redirect)."""
    return (
        "login.agilquest.com" in page.url
        and "microsoftonline" not in page.url
        and "login.microsoft" not in page.url
        and "samlsuccess" not in page.url
    )


def establish_session(page, retries: int = 2, delay: int = 5) -> bool:
    """Go through APP_LAUNCHER to get a fresh Agilquest session.

    The launcher does a SAML exchange that lands on /samlsuccess?authToken=...
    and stays there while the SPA sets session cookies client-side. The URL
    never redirects further, so we wait for a DOM element that proves the app
    has fully loaded and the session is live.

    Returns True if session established. Returns False if MS SSO requires
    interactive login (MS tokens expired — run setup_auth.py).
    Retries on network errors.
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=30000)
            last_exc = None
            break
        except Exception as e:
            last_exc = e
            print(
                f"Launcher attempt {attempt}/{retries} failed: {str(e).splitlines()[0]}",
                file=sys.stderr,
            )
            if attempt < retries:
                time.sleep(delay)

    if last_exc:
        raise RuntimeError(
            f"Launcher unreachable after {retries} attempts: {str(last_exc).splitlines()[0]}"
        )

    if "microsoftonline" in page.url or "login.microsoft" in page.url:
        print(f"Launcher landed on MS login: {page.url[:80]}", file=sys.stderr)
        return False  # MS SSO needs interactive login

    # Wait for the SPA to finish its client-side token exchange.
    # The nav menu only renders once the session cookie is set.
    try:
        page.wait_for_selector("nav, .navbar, [class*='nav']", timeout=15000)
    except Exception:
        pass  # fall through — is_on_agilquest will catch failures

    print(f"Launcher session ready: {page.url[:80]}", file=sys.stderr)
    return "login.agilquest.com" in page.url


# Keep verify_auth as an alias so callers don't need updating yet
def verify_auth(page, retries: int = 3, delay: int = 10) -> bool:
    return establish_session(page, retries=retries, delay=delay)
