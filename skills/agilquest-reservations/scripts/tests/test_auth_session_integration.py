"""Live integration checks for the auth/session protocol.

These launch real headless Chrome against the real persistent profile and
talk to Microsoft and Agilquest. They are OPT-IN — skipped unless:

    AQ_LIVE_TESTS=1 uv run pytest tests/ -v

Read-only: they authenticate and read reservations. Nothing here books,
cancels or checks in. Keep it that way — a test suite must never mutate a
real reservation.

They need the profile to hold a valid ESTSAUTHPERSISTENT cookie. If it has
expired these fail with a clear message telling you to run `aq setup-auth`;
that is a genuine result, not a flaky test.

Purpose: the unit tests encode what we believe the protocol does. These
verify that belief still matches reality — Entra and Agilquest can change
their redirect behaviour under us at any time.
"""

import os
import sys
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytestmark = pytest.mark.skipif(
    os.getenv("AQ_LIVE_TESTS") != "1",
    reason="live browser tests — set AQ_LIVE_TESTS=1 to run",
)

MAX_ESTABLISH_SECONDS = 45


@pytest.fixture
def live_context():
    """A real headless persistent context against the real profile."""
    from playwright.sync_api import sync_playwright
    from agilquest_reservations.lib.browser import launch_headless

    with sync_playwright() as p:
        ctx = launch_headless(p)
        try:
            yield ctx
        finally:
            ctx.close()


def _true_url(page):
    try:
        return page.evaluate("location.href")
    except Exception:
        return page.url


class TestLiveCredential:

    def test_profile_holds_an_unexpired_entra_credential(self, live_context):
        """The one thing a human must periodically renew.

        Failure here means: run `aq setup-auth`. It is not a code bug.
        """
        cookies = {c["name"]: c for c in live_context.cookies()}
        cred = cookies.get("ESTSAUTHPERSISTENT")

        assert cred is not None, (
            "no ESTSAUTHPERSISTENT in the profile — run `aq setup-auth`"
        )
        remaining = (cred["expires"] - time.time()) / 86400
        assert remaining > 0, (
            f"Entra credential expired {-remaining:.0f} days ago — "
            "run `aq setup-auth`"
        )
        if remaining < 14:
            pytest.skip(
                f"credential valid but expires in {remaining:.0f} days — "
                "schedule an `aq setup-auth` soon"
            )

    def test_unattended_session_establishes_without_a_login_form(self, live_context):
        """The core assumption, against the live services."""
        from agilquest_reservations.lib.browser import APP_LAUNCHER

        page = live_context.new_page()
        start = time.time()
        page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=60000)
        elapsed = time.time() - start

        assert elapsed < MAX_ESTABLISH_SECONDS
        assert page.query_selector(
            "input[name='loginfmt'], #i0116, input[type='password']"
        ) is None, "Entra demanded interactive login — run `aq setup-auth`"
        assert "login.agilquest.com" in _true_url(page)


class TestLiveSessionExchange:

    def test_domcontentloaded_reports_the_real_url(self, live_context):
        """Guards the fix for bug #1.

        `domcontentloaded` was replaced by `commit` to dodge a hang that was
        in fact the profile-lock bug. It does not hang: measured 7.0-7.7s.
        """
        from agilquest_reservations.lib.browser import APP_LAUNCHER

        page = live_context.new_page()
        page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=60000)

        assert "samlsuccess" in page.url or "login.agilquest.com" in page.url, (
            f"expected an Agilquest URL, got {page.url[:120]}"
        )

    def test_auth_data_cookie_appears_after_the_exchange(self, live_context):
        """AUTH_DATA is the positive signal the session is live."""
        from agilquest_reservations.lib.browser import APP_LAUNCHER

        page = live_context.new_page()
        page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=60000)

        deadline = time.time() + 30
        while time.time() < deadline:
            if any(c["name"] == "AUTH_DATA" for c in live_context.cookies()):
                break
            time.sleep(1)

        names = {c["name"] for c in live_context.cookies()}
        assert "AUTH_DATA" in names, (
            "token exchange never completed — AUTH_DATA absent after 30s"
        )

    def test_authenticated_read_returns_real_data(self, live_context):
        """End-to-end proof, and the A/B that pins bug #3.

        Read-only: reads the reservations table, changes nothing.
        """
        from agilquest_reservations.lib.browser import APP_LAUNCHER
        from agilquest_reservations.lib.agilquest import RESERVATIONS_URL

        page = live_context.new_page()
        page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=60000)

        deadline = time.time() + 30
        while time.time() < deadline:
            if any(c["name"] == "AUTH_DATA" for c in live_context.cookies()):
                break
            time.sleep(1)

        page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("table tbody tr", timeout=15000)

        body = page.inner_text("body")
        assert "LOG IN" not in body, (
            "bounced to the login screen — the session was discarded before "
            "the read (bug #3: navigated before AUTH_DATA appeared)"
        )
        assert page.query_selector_all("table tbody tr"), (
            "no reservation rows; session may have been lost"
        )

    @pytest.mark.xfail(
        reason="bug #3: navigating before AUTH_DATA discards the session; "
               "remove this xfail once establish_session() waits properly",
        strict=False,
    )
    def test_navigating_immediately_loses_the_session(self, live_context):
        """Characterises the race against the live app.

        Reproduced 3/3 in production: 0 reservations vs 4. Expected to fail
        (i.e. the session IS lost) until the wait is implemented.
        """
        from agilquest_reservations.lib.browser import APP_LAUNCHER
        from agilquest_reservations.lib.agilquest import RESERVATIONS_URL

        page = live_context.new_page()
        page.goto(APP_LAUNCHER, wait_until="domcontentloaded", timeout=60000)
        page.goto(RESERVATIONS_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        assert "LOG IN" not in page.inner_text("body")


class TestLiveProfileLock:

    def test_a_stale_lock_does_not_prevent_launching(self, tmp_path):
        """Bug #2, end to end: a poisoned profile must self-heal.

        Uses a throwaway profile, never the real one.
        """
        from playwright.sync_api import sync_playwright
        from agilquest_reservations.lib import browser

        profile = tmp_path / "user_data"
        profile.mkdir()
        (profile / "SingletonLock").symlink_to("HOST-999999")

        original = browser.get_state_dir
        browser.get_state_dir = lambda: tmp_path
        try:
            with sync_playwright() as p:
                ctx = browser.launch_headless(p)
                try:
                    assert ctx is not None
                finally:
                    ctx.close()
        finally:
            browser.get_state_dir = original
