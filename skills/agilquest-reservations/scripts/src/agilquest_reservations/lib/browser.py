"""Browser launch and auth-state helpers shared across all entry points."""

import os
import subprocess
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
    """Reverted back to defaulting to the real, installed system Chrome —
    see features/auth_and_session.md, "Chrome/Playwright version drift"
    (bug #5) and its reversal note.

    Bug #5 found that a system Chrome auto-updating ahead of what the
    installed playwright package's CDP client supports produces a launcher
    hang that looks exactly like a network fault, and switched the default
    to Playwright's own bundled Chromium to remove that drift vector.

    That default was itself reverted after a SEPARATE, worse problem
    surfaced on this machine: Microsoft Defender for Endpoint's real-time
    protection (a `[managed]`, centrally-controlled policy — not something
    disable-able locally) actively scans freshly-downloaded, unsigned
    binaries under `~/Library/Caches/ms-playwright/` (confirmed live in
    `microsoft_defender.log`: repeated `ExecuteLuaScript() failed` /
    `SIGNATURE_TYPE_MACHOHSTR_EXT` entries against the exact
    chrome-headless-shell/Chrome-for-Testing binaries). This does not
    register as a formal threat detection (`mdatp threat list` shows none,
    an explicit `mdatp scan custom` finds 0/327 threats, the file is never
    quarantined) but intermittently races Chrome's own startup — observed
    live killing `setup_auth.py`'s headed browser ~10s after launch,
    mid-interactive-MFA, on two separate real attempts, while a bare
    launch-and-wait test survived a full 20s moments later. Real Chrome is
    already signed and trusted, so it does not hit this race at all.

    Net effect: the version-drift risk bug #5 fixed is real but rarer in
    practice than this EDR race turned out to be, on this machine. Set
    CHROME_PATH to override with a different executable if needed.
    """
    if env := os.getenv("CHROME_PATH"):
        return env
    return (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if sys.platform == "darwin"
        else "/usr/bin/google-chrome"
    )


def clear_singleton_lock(profile_dir: Path) -> None:
    """Remove stale Chrome ProcessSingleton symlinks from a profile dir.

    A crashed or orphaned Chrome leaves SingletonLock/SingletonCookie/
    SingletonSocket behind. Any later launch against the same profile then
    fails with "Failed to create a ProcessSingleton for your profile
    directory" — which looks nothing like a lock problem and gets
    misdiagnosed as a network timeout (see features/auth_and_session.md,
    bug #2).

    If the lock's PID is still alive, kill it first — otherwise we'd be
    clearing a lock a live Chrome still holds, and the next launch would
    just recreate the same conflict.

    Safe to call on every launch: a clean profile has nothing to remove.
    """
    lock = profile_dir / "SingletonLock"
    if lock.is_symlink():
        pid = None
        try:
            pid = int(str(lock.readlink()).rsplit("-", 1)[-1])
        except (OSError, ValueError):
            pass
        if pid is not None:
            try:
                os.kill(pid, 0)  # raises if the process is gone
                os.kill(pid, 15)
                time.sleep(2)
            except (OSError, ProcessLookupError, PermissionError):
                pass
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        p = profile_dir / name
        if p.is_symlink() or p.exists():
            p.unlink(missing_ok=True)


def _persistent_context(p, headless: bool, extra_args: list[str] | None = None) -> BrowserContext:
    profile_dir = get_state_dir() / "user_data"
    profile_dir.mkdir(parents=True, exist_ok=True)
    clear_singleton_lock(profile_dir)
    args = ["--disable-gpu", "--no-sandbox"] + (extra_args or [])
    # executable_path=None (the default — see get_chrome_path()) makes
    # Playwright launch its own bundled, version-matched Chromium rather
    # than a system Chrome that can silently drift out of CDP compatibility.
    return p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
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


def current_url(page) -> str:
    """The page's authoritative location.

    page.url can go stale mid-redirect: a "commit" navigation returns as
    soon as the first response byte arrives, well before a client-side/SAML
    redirect chain finishes, so page.url can keep reporting an intermediate
    URL (e.g. login.microsoftonline.com) after the document has already
    moved on to login.agilquest.com. location.href always reflects the
    document's real, current location.

    Falls back to page.url if evaluate() fails (e.g. a closed/crashed page)
    rather than raising — callers need a best-effort string, not an
    exception, when deciding what to log or how to react.

    See features/auth_and_session.md, bug #1 — this was the primary
    regression: code branching on `page.url` reported healthy, fully
    authenticated sessions as auth failures.
    """
    try:
        return page.evaluate("location.href")
    except Exception:
        return page.url


def needs_interactive_login(page) -> bool:
    """True only if Entra is actually presenting a login form.

    Deliberately does NOT look at page.url. A page mid-SAML-redirect can
    sit at a login.microsoftonline.com URL for a moment while already
    holding a valid session — matching on that URL substring is exactly
    the bug that made every cron job report false auth failures (bug #1).
    The only reliable signal that a human is genuinely required is the
    presence of the credential input itself.

    A still-navigating page (the SAML chain keeps moving client-side
    after domcontentloaded fires) tears down its execution context out
    from under a racing query_selector() call — Playwright raises
    "Execution context was destroyed, most likely because of a
    navigation" rather than returning null. That is not evidence of a
    login form; it is evidence the page hasn't settled yet, which is
    exactly what current_url() already tolerates the same way for the
    same reason (bug #1's fix). Surfaced live once Chrome/Playwright
    version drift (bug #5) stopped hiding it behind a 30s stall.
    """
    try:
        return page.query_selector(
            "input[name='loginfmt'], #i0116, input[type='password']"
        ) is not None
    except Exception:
        return False


def is_on_agilquest(page) -> bool:
    """True if the current page is on Agilquest (not an MS login redirect).

    Deliberately does NOT exclude /samlsuccess — that page IS a live,
    authenticated Agilquest page once the token exchange has completed
    (confirmed by inspecting its rendered body: "Upcoming Reservations",
    the signed-in user's name). Excluding it was based on the pre-exchange
    assumption that it's just a transient hop; treat wait_for_session()
    as the gate for "is the exchange done", not this URL check.
    """
    url = current_url(page)
    return (
        "login.agilquest.com" in url
        and "microsoftonline" not in url
        and "login.microsoft" not in url
    )


def wait_for_session(context, page, timeout: int = 30, poll_interval: float = 1.0) -> bool:
    """Block until the Agilquest session is actually live.

    The launcher's redirect chain parks at /samlsuccess?authToken=... and
    the URL stops moving there — but the session does NOT exist yet at that
    moment. The SPA still has to exchange that token client-side for real
    session cookies (AUTH_DATA on login.agilquest.com, JSESSIONID on
    auth.agilquest.com). Only once AUTH_DATA appears is it safe to navigate
    elsewhere; navigating earlier silently discards the token and the next
    page load bounces to a bare LOG IN screen (bug #3).

    This replaces a DOM-selector wait that was wrapped in `except: pass` —
    a stall there was invisible to the caller, which is exactly backwards
    for something load-bearing. Returns False (not an exception) on
    timeout so establish_session() can turn it into a clean "needs
    interactive login" style result; callers that need the failure to be
    loud should check the return value.

    Cookie presence alone is NOT sufficient: launch_persistent_context()
    keeps session-scoped cookies (expires=-1) alive across separate
    process launches, so AUTH_DATA from a PREVIOUS run can already be
    sitting in the profile before this run has navigated at all (observed
    live — present immediately after launch, before any goto()). A
    launcher that genuinely never redirects this run would then have a
    stale cookie mistaken for proof of a fresh exchange (bug #6). We
    therefore also require the page to actually be on the Agilquest
    domain right now — establish_session() additionally clears these
    cookies before navigating so a fresh AUTH_DATA can only mean this
    run's exchange; this check is the independent second line of defence
    for any caller that skips that step.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        url = current_url(page)
        has_auth_data = any(c["name"] == "AUTH_DATA" for c in context.cookies())
        if has_auth_data and "login.agilquest.com" in url:
            return True
        time.sleep(poll_interval)
    return False


def establish_session(page, context=None, retries: int = 4, delay: int = 8) -> bool:
    """Go through APP_LAUNCHER to get a fresh Agilquest session.

    The launcher does a SAML exchange that lands on /samlsuccess?authToken=...
    and stays there while the SPA sets session cookies client-side. The URL
    never redirects further, so completion is judged by wait_for_session()
    polling for the AUTH_DATA cookie — a positive signal — not by guessing
    from DOM state or URL shape.

    Uses wait_until="domcontentloaded". An earlier "commit" wait was tried
    to dodge an observed >30s hang, but "commit" is what caused bug #1 (see
    current_url() and needs_interactive_login() docstrings) and the hang it
    was chasing was actually a stale profile lock (bug #2), not a slow
    page. domcontentloaded measures at 7-8s against the real launcher and
    correctly reflects the settled URL.

    `context` is needed to check cookies via wait_for_session(); pass the
    BrowserContext the page belongs to. If omitted, session-exchange
    completion cannot be verified and this falls back to a short grace
    sleep — callers should pass it whenever a context is available.

    Returns True if session established. Returns False if MS SSO requires
    interactive login (Entra's persistent credential expired — run
    `aq setup-auth`). Retries navigation on network errors.
    """
    if context is not None:
        # launch_persistent_context() keeps session-scoped cookies
        # (expires=-1) alive across separate process launches — AUTH_DATA
        # from a PREVIOUS run can already be sitting in the profile before
        # this run has navigated at all (observed live: present immediately
        # after launch, zero navigation done). wait_for_session() below
        # would then treat that leftover as proof this run's exchange
        # completed, even if the launcher never redirects this time — the
        # "Launcher session ready" / "Session invalid" contradiction seen
        # in the first night of production cron logs (bug #6). Clearing the
        # Agilquest session cookies first guarantees any AUTH_DATA we see
        # afterward was actually minted by this run.
        context.clear_cookies(name="AUTH_DATA")
        context.clear_cookies(name="JSESSIONID")

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

    if needs_interactive_login(page):
        print(f"Launcher landed on MS login: {current_url(page)[:80]}", file=sys.stderr)
        return False  # Entra credential expired — needs a human

    if context is not None:
        if not wait_for_session(context, page, timeout=30):
            print("Timed out waiting for the Agilquest session to become live "
                  "(AUTH_DATA cookie never appeared)", file=sys.stderr)
            return False
    else:
        # No context to poll cookies on — best effort only.
        time.sleep(3)

    print(f"Launcher session ready: {current_url(page)[:80]}", file=sys.stderr)
    return is_on_agilquest(page)


# Keep verify_auth as an alias so callers don't need updating yet
def verify_auth(page, context=None, retries: int = 4, delay: int = 8) -> bool:
    return establish_session(page, context=context, retries=retries, delay=delay)


def trigger_reauth_and_wait(p, timeout: int = 300, poll_interval: int = 10) -> bool:
    """Launch setup_auth.py in a Terminal window, then poll headlessly
    through APP_LAUNCHER until the session comes up or timeout elapses.

    Must poll via establish_session()/APP_LAUNCHER, not a raw goto to an
    Agilquest URL — a fresh headless context has no live Agilquest session
    cookie (that cookie is ~10-minute-lived and set by the launcher's SAML
    exchange), so a direct goto can never observe a freshly-completed SSO.

    `p` is an active sync_playwright() context — the caller's own context
    must already be closed (Chrome allows only one owner of the profile
    dir at a time), so this opens and closes its own persistent context
    for each poll.

    Returns True if the session came up within timeout, else False.
    """
    scripts_dir = Path(__file__).parent.parent.parent.parent
    print("\nSession invalid — opening Terminal to run setup_auth.py...", file=sys.stderr)
    subprocess.Popen([
        "/usr/bin/osascript", "-e",
        f'tell application "Terminal" to do script "cd {scripts_dir} && uv run src/agilquest_reservations/setup_auth.py"',
    ])
    print(f"Waiting up to {timeout // 60} minutes for SSO to complete...", file=sys.stderr)

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(poll_interval)
        try:
            context = _persistent_context(p, headless=True)
            try:
                page = context.new_page()
                if establish_session(page, context=context, retries=1):
                    print("Session restored.", file=sys.stderr)
                    return True
            finally:
                context.close()
        except Exception:
            pass  # profile locked by setup_auth — keep polling

    print(f"Re-auth timed out after {timeout // 60} minutes.", file=sys.stderr)
    return False


# Every layer below has, at one point, surfaced as the identical
# "Page.goto: Timeout 30000ms exceeded" — which reads as a network problem
# and sent past debugging down that path for weeks while the real causes
# (a stale profile lock, a stale page.url, a not-yet-live session) went
# unaddressed. diagnose() exists so callers report which layer actually
# failed instead of letting every failure look like connectivity.
_LAYER_MESSAGES = {
    "profile_lock": "Another Chrome process holds the browser profile "
                    "(stale SingletonLock). Should self-heal on next launch.",
    "interactive_login": "Entra's persistent credential has expired. "
                          "Run `aq setup-auth` to re-authenticate.",
    "session_exchange": "The launcher reached samlsuccess but the SPA's "
                         "token exchange did not complete (AUTH_DATA cookie "
                         "never appeared). Connectivity is fine; the SPA "
                         "itself did not finish.",
    "network": "The launcher was genuinely unreachable — DNS, TLS, or "
               "connectivity failure.",
}


def diagnose(page=None, context=None, profile_dir: Path | None = None,
             layer_override: str | None = None) -> dict:
    """Classify why establishing a session failed, by layer rather than by
    the generic timeout message every layer happens to produce.

    `layer_override` lets callers who already know the failing layer (e.g.
    a caught exception type) report it directly without re-probing state.
    Real (non-overridden) classification is intentionally conservative:
    prefer "network" only when nothing else explains the failure, since
    that is the misdiagnosis this function exists to stop.
    """
    layer = layer_override
    if layer is None:
        if profile_dir is not None and (profile_dir / "SingletonLock").is_symlink():
            layer = "profile_lock"
        elif page is not None and needs_interactive_login(page):
            layer = "interactive_login"
        elif page is not None and context is not None and not wait_for_session(
            context, page, timeout=1, poll_interval=0.2
        ):
            layer = "session_exchange"
        else:
            layer = "network"

    return {"layer": layer, "message": _LAYER_MESSAGES[layer]}
