"""Browser launch and auth-state helpers shared across all entry points."""

import os
import sys
import json
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, BrowserContext
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

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


def get_auth_state_path() -> Path:
    return get_state_dir() / "auth.json"


def get_chrome_path() -> str:
    if env := os.getenv("CHROME_PATH"):
        return env
    return (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if sys.platform == "darwin"
        else "/usr/bin/google-chrome"
    )


def launch_headless(p) -> BrowserContext:
    """Launch a headless browser context, loading saved auth state if present.

    Uses launch() + new_context() (not persistent context) so storage_state
    can be passed directly — persistent context doesn't support that parameter.
    """
    auth_path = get_auth_state_path()
    browser = p.chromium.launch(
        headless=True,
        executable_path=get_chrome_path(),
        args=["--disable-gpu", "--no-sandbox"],
    )
    kwargs = {}
    if auth_path.exists():
        kwargs["storage_state"] = str(auth_path)
    return browser.new_context(**kwargs)


def launch_headed(p) -> BrowserContext:
    """Launch a headed browser for interactive SSO, using mock keychain so
    cookies are stored in a format readable by the headless context."""
    return p.chromium.launch_persistent_context(
        user_data_dir=str(get_state_dir() / "user_data"),
        headless=False,
        executable_path=get_chrome_path(),
        args=["--disable-gpu", "--use-mock-keychain", "--password-store=basic"],
    )


def save_auth(context: BrowserContext):
    """Persist cookies/storage to auth.json for headless reuse."""
    path = get_auth_state_path()
    context.storage_state(path=str(path))
    print(f"Auth state saved → {path}", file=sys.stderr)


def is_authenticated(page) -> bool:
    """True if the current page is on Agilquest (not an MS login redirect)."""
    return (
        "login.agilquest.com" in page.url
        and "microsoftonline" not in page.url
        and "login.microsoft" not in page.url
    )


def verify_auth(page, retries: int = 3, delay: int = 10) -> bool:
    """
    Navigate to the Agilquest reservations page and confirm the session is
    valid. Returns True if authenticated, False if redirected to MS login.
    Retries on network errors (timeout / DNS).
    """
    from .agilquest import RESERVATIONS_URL
    import time

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
            last_exc = None
            break
        except Exception as e:
            last_exc = e
            print(
                f"Auth check attempt {attempt}/{retries} failed: {str(e).splitlines()[0]}",
                file=sys.stderr,
            )
            if attempt < retries:
                time.sleep(delay)

    if last_exc:
        raise RuntimeError(
            f"Agilquest unreachable after {retries} attempts: {str(last_exc).splitlines()[0]}"
        )

    return is_authenticated(page)
