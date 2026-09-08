"""Unit tests for the interactive SSO setup script.

Written TEST-FIRST against the intended API, mirroring
test_auth_session.py. setup_auth.py currently has its own duplicate
clear_singleton_lock(), prints the raw (possibly stale) page.url straight
to the terminal, and declares success from a DOM selector wait rather than
waiting for the AUTH_DATA cookie — the same class of bug already fixed in
lib/browser.py's establish_session(), just not yet applied here. See
features/interactive_setup.feature for the behavioural spec.

Fast and hermetic — no Chrome, no network, no Terminal windows.
"""

import sys
import time
from pathlib import Path

import pytest

from conftest import MS_LOGIN, SAMLSUCCESS, FakeContext


# --------------------------------------------------------------------------
# Rule: the tool never shows a reported location it knows to be stale
# --------------------------------------------------------------------------

class TestDiagnosticOutputUsesTrueLocation:

    def test_prints_the_true_location_not_the_stale_reported_one(self, authed_context, capsys):
        from agilquest_reservations.setup_auth import print_current_url

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="commit")  # lands with a stale reported page.url

        print_current_url(page, label="Current URL")

        out = capsys.readouterr().out
        assert SAMLSUCCESS in out
        assert "microsoftonline" not in out, (
            "printed the stale intermediate MS URL to the person watching, "
            "even though they are already signed in"
        )


# --------------------------------------------------------------------------
# Rule: success is only declared once the session is provably live
# --------------------------------------------------------------------------

class TestSuccessRequiresLiveSession:

    def test_does_not_confirm_before_the_exchange_completes(self):
        from agilquest_reservations.setup_auth import wait_for_authenticated_session

        ctx = FakeContext(entra_valid=True, exchange_delay_polls=10**6)  # never completes
        page = ctx.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert wait_for_authenticated_session(page, ctx, timeout=2) is False

    def test_confirms_once_the_exchange_has_completed(self, authed_context):
        from agilquest_reservations.setup_auth import wait_for_authenticated_session

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert wait_for_authenticated_session(page, authed_context, timeout=10) is True

        names = {c["name"] for c in authed_context.cookies()}
        assert "AUTH_DATA" in names, (
            "reported success before the session actually existed"
        )


# --------------------------------------------------------------------------
# Rule: the profile lock is cleared through one shared implementation
# --------------------------------------------------------------------------

class TestSharedLockClearing:

    def test_setup_auth_has_no_local_clear_singleton_lock(self):
        """Regression guard: a second implementation of the same fix drifts.

        setup_auth.py must import lib.browser.clear_singleton_lock rather
        than defining its own.
        """
        import agilquest_reservations.setup_auth as setup_auth_module

        own_lock_fn = setup_auth_module.__dict__.get("clear_singleton_lock")
        if own_lock_fn is None:
            pytest.fail("clear_singleton_lock is not available at all")

        from agilquest_reservations.lib.browser import clear_singleton_lock as shared_fn
        assert own_lock_fn is shared_fn, (
            "setup_auth.py defines its own clear_singleton_lock() instead of "
            "reusing lib.browser.clear_singleton_lock — the two will drift"
        )

    def test_shared_clear_singleton_lock_accepts_a_profile_dir(self, profile_dir):
        """setup_auth.py's old local version took no arguments and hardcoded
        get_state_dir() / "user_data" internally — the shared one must be
        usable the same way this module needs it: given an explicit dir."""
        from agilquest_reservations.lib.browser import clear_singleton_lock

        lock = profile_dir / "SingletonLock"
        lock.symlink_to("HOST-999999")

        clear_singleton_lock(profile_dir)

        assert not lock.is_symlink()


# --------------------------------------------------------------------------
# Rule: a genuine login prompt and a mid-exchange page are never confused
# --------------------------------------------------------------------------

class TestLoginPromptDetection:

    def test_prompts_when_entra_shows_a_real_login_form(self, expired_context):
        from agilquest_reservations.setup_auth import needs_interactive_login

        page = expired_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="domcontentloaded")

        assert needs_interactive_login(page) is True

    def test_does_not_prompt_during_an_automatic_mid_exchange_pause(self, authed_context):
        from agilquest_reservations.setup_auth import needs_interactive_login

        page = authed_context.new_page()
        page.goto("https://launcher.myapps.microsoft.com/api/signin/x",
                  wait_until="commit")  # stale reported URL, no real form

        assert needs_interactive_login(page) is False

    def test_setup_auth_reuses_the_shared_login_detector(self):
        """Must not reimplement the URL-substring check that caused bug #1."""
        import agilquest_reservations.setup_auth as setup_auth_module
        from agilquest_reservations.lib.browser import needs_interactive_login as shared_fn

        assert setup_auth_module.needs_interactive_login is shared_fn
