#!/usr/bin/env python3
"""
One-time interactive SSO setup for Agilquest.

Opens a headed Chrome window and navigates through the Microsoft app
launcher. After successful SSO, MS tokens are saved in the persistent
Chrome profile (user_data_dir) and reused by all headless scripts.

Run this again whenever the headless scripts report MS SSO requires
interactive login.

Usage:
  aq setup-auth
  uv run src/agilquest_reservations/setup_auth.py
"""

import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from agilquest_reservations.lib.browser import (
    APP_LAUNCHER, get_state_dir, launch_headed,
    is_on_agilquest, current_url, needs_interactive_login, wait_for_session,
    clear_singleton_lock,
)


def print_current_url(page, label: str = "Current URL") -> None:
    """Print the page's true location, never the stale reported one.

    page.url can lag behind a client-side/SAML redirect for a few seconds
    (see current_url()'s docstring in lib/browser.py). Printing it directly
    to a person watching this run misleads them at the one moment their
    judgment is the safety net — they'd read "still on Microsoft" while
    already signed in. Always route through current_url() instead.
    """
    print(f"  {label}: {current_url(page)[:100]}", flush=True)


def wait_for_authenticated_session(page, context, timeout: int = 30) -> bool:
    """True once the Agilquest session is provably live, not merely once
    the redirect chain has parked at /samlsuccess.

    Thin wrapper over lib.browser.wait_for_session so setup_auth reports
    success on the same evidence (the AUTH_DATA cookie) that headless runs
    require — otherwise this script could declare victory on a page that
    the very next cron run would find already-expired/discarded.
    """
    return wait_for_session(context, page, timeout=timeout)


def main():
    state_dir = get_state_dir()

    print(f"Storage: {state_dir}", flush=True)
    print(flush=True)

    clear_singleton_lock(state_dir / "user_data")

    with sync_playwright() as p:
        browser = launch_headed(p)
        # browser.version is only known once launched — print it (rather
        # than a pre-launch executable path) since Chrome/CDP version drift
        # is the diagnostic that actually matters now Playwright launches
        # its own bundled Chromium by default (see get_chrome_path()).
        print(f"Chrome:  {browser.browser.version if browser.browser else 'unknown'}", flush=True)
        try:
            # launch_persistent_context() already opens one tab (Chrome
            # always starts a window with a tab) — calling new_page() would
            # create a second, separate tab that this script then navigates
            # and polls while you're looking at the first one, which never
            # moves off about:blank. Reuse the context's existing tab
            # instead so there's only ever one tab to watch.
            page = browser.pages[0] if browser.pages else browser.new_page()
            print(f"(tabs open: {len(browser.pages)})", flush=True)

            print("Step 1: Authenticating via Microsoft app launcher...", flush=True)
            try:
                # domcontentloaded, not "commit" — "commit" returns before
                # the SAML redirect chain finishes, leaving page.url (and
                # anything printed from it) stale. domcontentloaded measures
                # 7-8s against the real launcher; the hang that "commit" was
                # introduced to dodge was a stale profile lock, not a slow
                # page (see lib/browser.establish_session's docstring).
                page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"Note: {e}", file=sys.stderr, flush=True)

            if is_on_agilquest(page):
                print("✓ MS SSO completed automatically — session valid.", flush=True)
            elif not needs_interactive_login(page):
                # Landed somewhere that isn't yet Agilquest and isn't a real
                # login form either — the automatic mid-exchange pause.
                # Nothing to prompt for; fall through to the same wait used
                # below to confirm the exchange completes.
                print("✓ MS SSO completing automatically...", flush=True)
            else:
                print("✓ Browser opened. Please complete Entra SSO login.", flush=True)
                print_current_url(page)
                print("  Waiting up to 5 minutes for you to finish...", flush=True)
                # Don't use page.wait_for_url() here — Entra's login page
                # does its own client-side redirects while loading (ADFS
                # relay pages, "pick an account" bounces, etc.), any one of
                # which can transiently match a URL-shape predicate before
                # you've typed anything. Poll is_on_agilquest() instead and
                # require it to hold steady, so a momentary mid-flow bounce
                # can't be mistaken for a completed login.
                deadline = time.time() + 300
                confirmed = False
                last_url = current_url(page)
                while time.time() < deadline:
                    time.sleep(3)
                    try:
                        url_now = current_url(page)
                    except Exception as e:
                        print(f"  (poll error: {e})", flush=True)
                        continue
                    if url_now != last_url:
                        print(f"  URL changed: {url_now[:100]}", flush=True)
                        last_url = url_now
                    if is_on_agilquest(page):
                        time.sleep(2)  # let any further redirect settle
                        if is_on_agilquest(page):
                            confirmed = True
                            break
                if not confirmed:
                    raise RuntimeError(f"Timed out waiting for SSO. URL: {current_url(page)}")
                print("✓ Redirected to Agilquest.", flush=True)

            print("\nStep 2: Confirming the session is actually live...", flush=True)
            if not wait_for_authenticated_session(page, browser, timeout=30):
                raise RuntimeError(
                    "Redirected to Agilquest, but the session never became "
                    f"live (AUTH_DATA cookie never appeared). URL: {current_url(page)}"
                )
            if not is_on_agilquest(page):
                raise RuntimeError(f"Lost Agilquest session before confirming. URL: {current_url(page)}")

            print("✓ MS tokens saved in persistent Chrome profile.", flush=True)
            print("✓ Headless scripts are ready — they will go through the launcher each run.", flush=True)

        except Exception as e:
            print(f"✗ Setup failed: {e}", file=sys.stderr, flush=True)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
