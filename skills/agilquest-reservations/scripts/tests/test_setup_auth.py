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
# Rule: setup_auth.py never assumes "no password form" means "automatic" —
# it always gives a human the same wait, whatever kind of interstitial
# Entra shows.
#
# main() used to branch three ways: is_on_agilquest() -> done;
# needs_interactive_login() -> wait for you; neither -> assume automatic
# and skip the wait entirely. That third branch was reached by ANY
# non-password interstitial — a "stay signed in?" prompt, an account
# picker, or a FIDO2/WebAuthn challenge (security key, Windows Hello,
# passkey) all fail needs_interactive_login()'s password-field check the
# same way a genuine mid-exchange pause does. Confirmed live: an MFA
# decision screen and a /fido/get WebAuthn prompt both closed the browser
# on someone mid-choice, because main() decided nothing needed waiting
# for. Fixed by removing the guess entirely — this script is always
# interactive (a human launched it and is at the keyboard), so anything
# short of already being on Agilquest gets the same 5-minute wait.
# --------------------------------------------------------------------------

class TestNeverAssumesAutomaticCompletion:

    def test_does_not_import_needs_interactive_login(self):
        """Regression guard for the three-way branch itself: if this name
        reappears in setup_auth's namespace, the old "maybe it's automatic"
        guess has likely come back too. FakePage/FakeContext model only
        a password-form-or-not distinction (see conftest.py), which is
        exactly the axis this bug lived on — a live FIDO/MFA/account-picker
        page is exercised by the opt-in integration suite
        (test_auth_session_integration.py), not reproducible here without
        a fixture that would just re-encode the same either/or assumption
        this fix removes."""
        import agilquest_reservations.setup_auth as setup_auth_module

        assert not hasattr(setup_auth_module, "needs_interactive_login"), (
            "setup_auth.py should not special-case password-form detection — "
            "any non-Agilquest page gets the same wait, no exceptions"
        )
