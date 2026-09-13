"""Unit tests for authentication and session reuse.

These are written TEST-FIRST against the *intended* API. Several of them fail
against the code as it stands today — that is deliberate and is the point:
each failing test pins one of the bugs catalogued in
features/auth_and_session.md. Implement to make them pass; do not weaken a
test to match current behaviour.

Fast and hermetic — no Chrome, no network. See conftest.py for the fakes and
test_auth_session_integration.py for the opt-in live checks.

Functions expected to exist in agilquest_reservations.lib.browser
(some do not yet — that is the work):

    current_url(page)                 -> str    authoritative location
    needs_interactive_login(page)     -> bool   login FORM present?
    wait_for_session(context, page, timeout) -> bool   AUTH_DATA appeared?
    establish_session(page, ...)      -> bool   full launcher flow
    clear_singleton_lock(profile_dir) -> None   remove stale lock symlinks
"""

import time
from pathlib import Path

import pytest

from conftest import (
    MS_LOGIN, SAMLSUCCESS, RESERVATIONS, LOGIN_SCREEN, LOGIN_BODY,
    FakeContext,
)


# --------------------------------------------------------------------------
# Rule: session state is judged by authoritative signals, never by URL shape
#
# Bug #1 (commit e887e70). `wait_until="commit"` returns before the SAML chain
# finishes, so page.url reports the intermediate Microsoft URL while the
# document has already moved to Agilquest. Branching on that substring is what
# made every cron job report a false auth failure.
# --------------------------------------------------------------------------

class TestAuthoritativeUrl:

    def test_reported_url_is_stale_after_a_commit_navigation(self, authed_context):
        """Characterisation: this is the trap, reproduced.

        Not a requirement — this documents the browser behaviour the
        production code must defend against. If this ever stops being true,
        the `commit` bug is gone at the source.
        """
        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="commit")

        assert "microsoftonline" in page.url          # reported: stale
        assert page.evaluate("location.href") == SAMLSUCCESS  # true: Agilquest

    def test_current_url_returns_the_true_location_not_the_stale_one(self, authed_context):
        from agilquest_reservations.lib.browser import current_url

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="commit")

        assert current_url(page) == SAMLSUCCESS
        assert "microsoftonline" not in current_url(page)

    def test_current_url_falls_back_when_evaluate_is_unavailable(self, authed_context):
        """A closed/crashed page must degrade, not explode."""
        from agilquest_reservations.lib.browser import current_url

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        def boom(expr):
            raise RuntimeError("Execution context was destroyed")
        page.evaluate = boom

        assert current_url(page) == SAMLSUCCESS  # falls back to page.url


class TestInteractiveLoginDetection:
    """"Do we need a human?" is answered by a login FORM, never by a URL."""

    def test_mid_redirect_page_does_not_require_interactive_login(self, authed_context):
        from agilquest_reservations.lib.browser import needs_interactive_login

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="commit")

        # page.url says microsoftonline; the user is nonetheless signed in.
        assert needs_interactive_login(page) is False

    def test_expired_credential_does_require_interactive_login(self, expired_context):
        from agilquest_reservations.lib.browser import needs_interactive_login

        page = expired_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert needs_interactive_login(page) is True

    def test_url_substring_alone_never_decides(self, authed_context):
        """Regression guard for the exact line that broke production:

            if "microsoftonline" in page.url: return False
        """
        from agilquest_reservations.lib.browser import needs_interactive_login

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="commit")

        assert "microsoftonline" in page.url          # the tempting signal...
        assert needs_interactive_login(page) is False  # ...must not be believed


# --------------------------------------------------------------------------
# Rule: the Agilquest session is only live once the token exchange completes
#
# Bug #3. The redirect chain parks at /samlsuccess?authToken=... and STOPS.
# The session does not exist yet; the SPA is still exchanging that token for
# AUTH_DATA/JSESSIONID. Navigating during that window silently discards it.
# --------------------------------------------------------------------------

class TestSessionExchange:

    def test_session_is_not_live_when_the_redirect_chain_settles(self, authed_context):
        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert page.url == SAMLSUCCESS  # arrived...
        names = {c["name"] for c in authed_context.cookies()}
        assert "AUTH_DATA" not in names  # ...but not yet authenticated

    def test_wait_for_session_blocks_until_auth_data_appears(self, authed_context):
        from agilquest_reservations.lib.browser import wait_for_session

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert wait_for_session(authed_context, page, timeout=10) is True

        names = {c["name"] for c in authed_context.cookies()}
        assert "AUTH_DATA" in names
        assert "JSESSIONID" in names

    def test_navigating_before_the_exchange_destroys_the_session(self, authed_context):
        """The A/B that was reproduced 3/3 in production: 0 rows vs 4."""
        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        page.goto(RESERVATIONS, wait_until="domcontentloaded")  # too early

        assert page.url == LOGIN_SCREEN
        assert "LOG IN" in page.inner_text("body")
        assert page.query_selector_all("table tbody tr") == []

    def test_navigating_after_the_exchange_preserves_the_session(self, authed_context):
        from agilquest_reservations.lib.browser import wait_for_session

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")
        wait_for_session(authed_context, page, timeout=10)

        page.goto(RESERVATIONS, wait_until="domcontentloaded")

        assert page.url == RESERVATIONS
        assert page.query_selector_all("table tbody tr") != []

    def test_a_stalled_exchange_is_reported_not_swallowed(self):
        """The current wait is `except: pass`, so a stall looks like success.

        It is load-bearing: its failure must be visible to the caller.
        """
        from agilquest_reservations.lib.browser import wait_for_session

        ctx = FakeContext(entra_valid=True, exchange_delay_polls=10**6)
        page = ctx.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert wait_for_session(ctx, page, timeout=2) is False

    def test_establish_session_waits_for_the_exchange_before_returning_true(self, authed_context):
        """establish_session() must not return True on arrival alone."""
        from agilquest_reservations.lib.browser import establish_session

        page = authed_context.new_page()
        assert establish_session(page, context=authed_context) is True

        names = {c["name"] for c in authed_context.cookies()}
        assert "AUTH_DATA" in names, (
            "establish_session returned True before the session existed"
        )

    def test_establish_session_is_false_when_a_human_is_required(self, expired_context):
        from agilquest_reservations.lib.browser import establish_session

        page = expired_context.new_page()
        assert establish_session(page, context=expired_context) is False

    def test_a_stale_cookie_from_a_previous_run_is_not_mistaken_for_this_runs_exchange(
        self, stale_cookie_context
    ):
        """Bug #6, found in production the first night this ran unattended.

        launch_persistent_context() keeps session-scoped cookies alive
        across separate process launches — AUTH_DATA can already be sitting
        in the profile before this run has navigated at all. Observed live:
        `ctx.cookies()` returned AUTH_DATA immediately after
        launch_headless(), zero navigation done. wait_for_session() must not
        treat that leftover as proof THIS run's exchange completed.
        """
        from agilquest_reservations.lib.browser import wait_for_session

        page = stale_cookie_context.new_page()
        # Precondition, mirroring the live repro exactly: the stale cookie
        # already exists before any navigation.
        assert any(c["name"] == "AUTH_DATA" for c in stale_cookie_context.cookies())

        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded", timeout=30000)
        # The launcher never actually redirected this run.
        assert "launcher.myapps.microsoft.com" in page.evaluate("location.href")

        assert wait_for_session(stale_cookie_context, page, timeout=2) is False, (
            "a leftover cookie from a previous run was mistaken for proof "
            "that this run's session exchange completed"
        )

    def test_establish_session_fails_when_the_launcher_never_lands_despite_a_stale_cookie(
        self, stale_cookie_context, capsys
    ):
        """End-to-end version of the same bug through establish_session().

        The live log showed the exact contradiction this pins: "Launcher
        session ready" printed immediately followed by "Session invalid".
        The return value alone (False) isn't sufficient proof of a fix —
        get there via the honest branch (wait_for_session failing) rather
        than falling through to a stale-cookie false "ready" that
        is_on_agilquest() then has to catch after the fact.
        """
        from agilquest_reservations.lib.browser import establish_session

        page = stale_cookie_context.new_page()
        assert establish_session(page, context=stale_cookie_context) is False

        err = capsys.readouterr().err
        assert "session ready" not in err.lower(), (
            "reported the session as ready based on a stale leftover "
            "cookie, then had to be caught by a second check — this is "
            "the exact contradictory log seen in production"
        )


# --------------------------------------------------------------------------
# Rule: a durable Entra credential survives long periods
#
# The core assumption. Proven against a 104-day-old profile.
# --------------------------------------------------------------------------

class TestDurableCredential:

    def test_a_months_old_credential_still_authenticates_unattended(self):
        from agilquest_reservations.lib.browser import establish_session

        # Credential issued 104 days ago, ~90-day life remaining from issue.
        ctx = FakeContext(entra_valid=True,
                          entra_expires=time.time() + 90 * 86400)
        page = ctx.new_page()

        assert establish_session(page, context=ctx) is True
        assert page.query_selector("input[name='loginfmt']") is None

    def test_the_durable_credential_is_the_entra_persistent_cookie(self, authed_context):
        cookies = {c["name"]: c for c in authed_context.cookies()}

        assert "ESTSAUTHPERSISTENT" in cookies
        assert cookies["ESTSAUTHPERSISTENT"]["expires"] > time.time() + 30 * 86400

    def test_agilquest_cookies_are_ephemeral_and_prove_nothing_long_term(self, authed_context):
        """AUTH_DATA/JSESSIONID are session-scoped (expires == -1).

        Their absence in a cold profile is normal, not a sign of broken auth.
        """
        from agilquest_reservations.lib.browser import wait_for_session

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")
        wait_for_session(authed_context, page, timeout=10)

        ephemeral = [c for c in authed_context.cookies()
                     if c["name"] in ("AUTH_DATA", "JSESSIONID")]
        assert ephemeral and all(c["expires"] == -1 for c in ephemeral)


# --------------------------------------------------------------------------
# Rule: failure to authenticate is never reported as an absence of data
#
# Bug #4. get_reservations() wraps everything in `except: pass` and returns [].
# A lost session then looks identical to "you have no bookings", so
# ensure_reservation.py tries to rebook and the real fault stays hidden.
# --------------------------------------------------------------------------

class TestAuthFailureIsNotEmptyData:

    def test_login_screen_raises_rather_than_returning_empty(self, authed_context):
        from agilquest_reservations.lib.agilquest import get_reservations

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")
        page.goto(RESERVATIONS, wait_until="domcontentloaded")  # session lost

        assert "LOG IN" in page.inner_text("body")  # precondition

        with pytest.raises(Exception) as exc:
            get_reservations(page)
        assert "auth" in str(exc.value).lower() or "login" in str(exc.value).lower()

    def test_genuinely_empty_is_distinguishable_from_failure(self, authed_context, monkeypatch):
        """A valid session with no bookings returns [] and does NOT raise."""
        from agilquest_reservations.lib import agilquest
        from agilquest_reservations.lib.browser import wait_for_session

        monkeypatch.setattr(agilquest, "save_reservations", lambda *_: None)

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")
        wait_for_session(authed_context, page, timeout=10)
        page.goto(RESERVATIONS, wait_until="domcontentloaded")

        monkeypatch.setattr(page, "query_selector_all", lambda sel: [])

        assert agilquest.get_reservations(page) == []

    def test_the_login_screen_is_detected_by_its_body_text(self):
        """Documents the marker used to spot a bounced request."""
        assert "LOG IN" in LOGIN_BODY
        assert "Upcoming Reservations" not in LOGIN_BODY


# --------------------------------------------------------------------------
# Rule: the browser profile has exactly one owner at a time
#
# Bug #2. clear_singleton_lock() lives only in setup_auth.py, so the four cron
# entry points never self-heal. Surfaces as "Page.goto: Timeout" — which
# points at the network and sends diagnosis to entirely the wrong layer.
# --------------------------------------------------------------------------

class TestProfileLock:

    def _make_stale_lock(self, profile_dir: Path, pid: int = 999999):
        lock = profile_dir / "SingletonLock"
        lock.symlink_to(f"HOST-{pid}")  # dangling by design
        (profile_dir / "SingletonCookie").symlink_to("1234567890")
        (profile_dir / "SingletonSocket").symlink_to("/tmp/nonexistent.sock")
        return lock

    def test_stale_lock_from_a_dead_process_is_cleared(self, profile_dir):
        from agilquest_reservations.lib.browser import clear_singleton_lock

        lock = self._make_stale_lock(profile_dir)
        assert lock.is_symlink()

        clear_singleton_lock(profile_dir)

        assert not lock.is_symlink()
        assert not (profile_dir / "SingletonCookie").is_symlink()
        assert not (profile_dir / "SingletonSocket").is_symlink()

    def test_clearing_is_idempotent_on_a_clean_profile(self, profile_dir):
        from agilquest_reservations.lib.browser import clear_singleton_lock

        clear_singleton_lock(profile_dir)   # must not raise
        clear_singleton_lock(profile_dir)

    def test_every_headless_launch_clears_the_lock_first(self, profile_dir, monkeypatch):
        """The regression that matters: self-healing must not be
        setup_auth-only. All four cron entry points go through here."""
        from agilquest_reservations.lib import browser

        self._make_stale_lock(profile_dir)
        monkeypatch.setattr(browser, "get_state_dir", lambda: profile_dir.parent)

        cleared = []
        monkeypatch.setattr(browser, "clear_singleton_lock",
                            lambda d=None: cleared.append(d or profile_dir))

        class FakeChromium:
            def launch_persistent_context(self, **kw):
                return FakeContext()

        class FakeP:
            chromium = FakeChromium()

        browser.launch_headless(FakeP())

        assert cleared, "launch_headless() did not clear the stale lock"


class TestChromeVersionDrift:
    """Bug #5 (features/auth_and_session.md): a system Chrome that
    auto-updates ahead of what the installed playwright package's CDP
    client supports produces a hang that looks exactly like a network
    fault. Fix: launch Playwright's own bundled, version-matched
    Chromium by default; only use a system install if CHROME_PATH is
    explicitly set."""

    def test_no_override_means_use_playwrights_bundled_chromium(self, monkeypatch):
        from agilquest_reservations.lib.browser import get_chrome_path

        monkeypatch.delenv("CHROME_PATH", raising=False)
        assert get_chrome_path() is None

    def test_explicit_override_is_still_honoured(self, monkeypatch):
        from agilquest_reservations.lib.browser import get_chrome_path

        monkeypatch.setenv("CHROME_PATH", "/opt/custom/chrome")
        assert get_chrome_path() == "/opt/custom/chrome"

    def test_persistent_context_passes_none_through_by_default(self, monkeypatch, profile_dir):
        """The regression that matters: nothing downstream must
        hardcode a system Chrome path — executable_path=None has to
        reach launch_persistent_context() so Playwright picks its own
        bundled build."""
        from agilquest_reservations.lib import browser

        monkeypatch.delenv("CHROME_PATH", raising=False)
        monkeypatch.setattr(browser, "get_state_dir", lambda: profile_dir.parent)

        captured = {}

        class FakeChromium:
            def launch_persistent_context(self, **kw):
                captured.update(kw)
                return FakeContext()

        class FakeP:
            chromium = FakeChromium()

        browser.launch_headless(FakeP())

        assert captured.get("executable_path") is None


class TestReauthLaunch:
    """Guards the path arithmetic in trigger_reauth_and_wait().

    This currently PASSES — the four `.parent`s are correct, resolving to
    scripts/ (the dir holding pyproject.toml). It is pinned because the
    expression looks wrong at a glance and was already misreported as a bug
    once; a well-meaning "fix" to three would break re-auth silently.
    """

    def test_reauth_runs_from_the_directory_holding_the_manifest(self, monkeypatch):
        from agilquest_reservations.lib import browser

        captured = {}

        class FakePopen:
            def __init__(self, argv, *a, **kw):
                captured["argv"] = argv

        monkeypatch.setattr(browser.subprocess, "Popen", FakePopen)
        monkeypatch.setattr(browser.time, "sleep", lambda _: None)
        monkeypatch.setattr(browser, "_persistent_context",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("locked")))

        browser.trigger_reauth_and_wait(object(), timeout=0)

        cd_target = None
        for part in " ".join(captured["argv"]).split():
            if part.endswith("/scripts") or part.endswith("agilquest-reservations"):
                cd_target = part
        assert cd_target and cd_target.endswith("/scripts"), (
            f"re-auth would cd to {cd_target!r}; expected the scripts/ dir "
            "containing pyproject.toml"
        )

    def test_reauth_does_not_hold_the_profile_between_polls(self, monkeypatch):
        """Chrome allows one owner of user_data_dir. If the poller keeps a
        context open, the setup_auth window it just spawned cannot start."""
        from agilquest_reservations.lib import browser

        opened, closed = [], []

        class TrackingContext(FakeContext):
            def __init__(self):
                super().__init__(entra_valid=False)
                opened.append(self)

            def close(self):
                closed.append(self)
                super().close()

        monkeypatch.setattr(browser.subprocess, "Popen",
                            lambda *a, **k: None)
        monkeypatch.setattr(browser.time, "sleep", lambda _: None)
        monkeypatch.setattr(browser, "_persistent_context",
                            lambda *a, **k: TrackingContext())

        browser.trigger_reauth_and_wait(object(), timeout=1, poll_interval=1)

        assert len(closed) == len(opened), (
            "a polling context was left open, blocking interactive setup_auth"
        )


# --------------------------------------------------------------------------
# Rule: diagnosis distinguishes the layer that actually failed
#
# Bugs #1, #2 and #3 all surfaced as "Page.goto: Timeout 30000ms exceeded".
# None were network faults. That ambiguity is why earlier fixes added DNS
# seeding, caffeinate and prewarm jobs against causes that were not there.
# --------------------------------------------------------------------------

class TestFailureAttribution:

    @pytest.mark.parametrize("layer", [
        "profile_lock",
        "interactive_login",
        "session_exchange",
        "network",
    ])
    def test_each_layer_has_a_distinct_diagnosis(self, layer):
        from agilquest_reservations.lib.browser import diagnose

        report = diagnose(layer_override=layer)

        assert report["layer"] == layer
        if layer != "network":
            assert "network" not in report["message"].lower(), (
                f"{layer} failure blamed on the network — the exact "
                "misattribution that cost weeks of debugging"
            )

    def test_a_real_network_fault_is_still_called_a_network_fault(self):
        from agilquest_reservations.lib.browser import diagnose

        assert diagnose(layer_override="network")["layer"] == "network"
