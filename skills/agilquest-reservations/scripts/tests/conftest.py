"""Test fixtures and browser fakes for the auth/session suite.

The fakes here model the *protocol*, not Playwright's API surface. In
particular FakePage deliberately reproduces the one behaviour that broke
production: `page.url` can lag behind the document's real location during a
client-side redirect chain, while `location.href` cannot.

Nothing in this file touches the network or launches Chrome. The integration
tests that do are in test_auth_session_integration.py and are opt-in.
"""

import sys
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


APP_LAUNCHER_HOST = "launcher.myapps.microsoft.com"
MS_LOGIN = "https://login.microsoftonline.com/57fdf63b/oauth2/authorize?client_id=2793995e"
SAMLSUCCESS = "https://login.agilquest.com/samlsuccess?authToken=deadbeefcafe"
RESERVATIONS = "https://login.agilquest.com/myreservations/active?viewMode=table"
LOGIN_SCREEN = "https://login.agilquest.com/"

# Body text Agilquest renders when it bounces an unauthenticated request.
# Matching on this is how we tell "session lost" from "no bookings".
LOGIN_BODY = (
    "LOG IN\nForgot Password?\nLOVE WHERE YOU WORK ™\n"
    "Choose, Use, Share, Enjoy!\nCopyright © 2026 Tango. All rights reserved."
)

AUTHED_BODY = (
    "Analytics | Help | Shalom Israel Bhooshi | SEARCH BY LIST | "
    "Upcoming Reservations | SK-BRA-06.01.W1024"
)


class FakeCookieJar:
    """Models the two cookie layers the protocol depends on."""

    def __init__(self):
        self._cookies = []

    def set_entra_persistent(self, expires: float):
        self._cookies.append({
            "name": "ESTSAUTHPERSISTENT",
            "value": "AQABAAAAAA...",
            "domain": ".login.microsoftonline.com",
            "expires": expires,
        })

    def set_agilquest_session(self):
        """Set by the SPA only AFTER the token exchange completes."""
        self._cookies.append({
            "name": "AUTH_DATA",
            "value": '{"owner":false}',
            "domain": "login.agilquest.com",
            "expires": -1,
        })
        self._cookies.append({
            "name": "JSESSIONID",
            "value": "EAEA2CE2ACCFF8B64C",
            "domain": "auth.agilquest.com",
            "expires": -1,
        })

    def clear_agilquest_session(self):
        self._cookies = [
            c for c in self._cookies
            if c["name"] not in ("AUTH_DATA", "JSESSIONID")
        ]

    def all(self):
        return list(self._cookies)


class FakePage:
    """A page that reproduces the real redirect/exchange timing.

    Key modelled behaviours:
      * `url` is the *reported* location and may be stale (the `commit` bug).
      * `evaluate("location.href")` always returns the true location.
      * the Agilquest session only exists after `complete_exchange()`.
    """

    def __init__(self, context, *, entra_valid=True, exchange_delay_polls=2,
                 stuck_at_launcher=False):
        self.context = context
        self.entra_valid = entra_valid
        self._reported_url = "about:blank"
        self._true_url = "about:blank"
        self._exchange_delay_polls = exchange_delay_polls
        self._polls_since_landing = 0
        self._exchange_done = False
        self._has_login_form = False
        self.closed = False
        # Models a launcher that never actually lands anywhere this run —
        # observed live: 3 real 30s Page.goto timeouts, and even the
        # "successful" 4th goto() returned in 0.1s while the page was still
        # sitting on the launcher URL, never having reached samlsuccess.
        self.stuck_at_launcher = stuck_at_launcher

    # -- navigation -------------------------------------------------------

    def goto(self, url, wait_until="load", timeout=30000):
        if APP_LAUNCHER_HOST in url:
            if self.stuck_at_launcher:
                # The launcher genuinely never redirects this run — the
                # real midnight failure. Any stale AUTH_DATA already in the
                # cookie jar (from an earlier run) must NOT be mistaken for
                # proof this navigation succeeded.
                self._reported_url = url
                self._true_url = url
                return
            if not self.entra_valid:
                # Entra genuinely wants a human: a real login form renders.
                self._reported_url = MS_LOGIN
                self._true_url = MS_LOGIN
                self._has_login_form = True
                return
            self._true_url = SAMLSUCCESS
            self._polls_since_landing = 0
            self._exchange_done = False
            self._has_login_form = False
            # THE BUG: with wait_until="commit" the navigation returns before
            # the redirect chain finishes, so the reported URL is the stale
            # intermediate MS URL while the document is already on Agilquest.
            self._reported_url = MS_LOGIN if wait_until == "commit" else SAMLSUCCESS
            return

        # Any other navigation. If the exchange has not completed, the app
        # discards the token and bounces to the login screen.
        if not self._exchange_done:
            self.context.cookies_jar.clear_agilquest_session()
            self._reported_url = LOGIN_SCREEN
            self._true_url = LOGIN_SCREEN
            return
        self._reported_url = url
        self._true_url = url

    def complete_exchange(self):
        """Simulate the SPA finishing its token->session exchange."""
        self._exchange_done = True
        self.context.cookies_jar.set_agilquest_session()

    # -- inspection -------------------------------------------------------

    @property
    def url(self):
        return self._reported_url

    def evaluate(self, expr):
        if "location.href" in expr:
            # Polling location.href is also what advances the exchange clock,
            # mirroring real elapsed time during a settle loop.
            self._tick()
            return self._true_url
        if "document.domain" in expr:
            return self._true_url.split("/")[2] if "//" in self._true_url else ""
        raise NotImplementedError(expr)

    def _tick(self):
        if self._true_url == SAMLSUCCESS and not self._exchange_done:
            self._polls_since_landing += 1
            if self._polls_since_landing >= self._exchange_delay_polls:
                self.complete_exchange()

    def query_selector(self, sel):
        if any(t in sel for t in ("loginfmt", "i0116", "password")):
            return object() if self._has_login_form else None
        return None

    def query_selector_all(self, sel):
        if "tbody tr" in sel and self._true_url.startswith(RESERVATIONS[:40]):
            return [object()] if self._exchange_done else []
        return []

    def inner_text(self, sel):
        if self._true_url == LOGIN_SCREEN:
            return LOGIN_BODY
        return AUTHED_BODY if self._exchange_done else ""

    def wait_for_selector(self, sel, timeout=None):
        raise TimeoutError(f"no element matching {sel}")

    def close(self):
        self.closed = True


class FakeContext:
    """Stands in for a Playwright persistent BrowserContext."""

    def __init__(self, *, entra_valid=True, exchange_delay_polls=2,
                 entra_expires=None, stuck_at_launcher=False):
        self.cookies_jar = FakeCookieJar()
        if entra_valid:
            self.cookies_jar.set_entra_persistent(
                entra_expires if entra_expires is not None
                else time.time() + 90 * 86400
            )
        self._entra_valid = entra_valid
        self._exchange_delay_polls = exchange_delay_polls
        self._stuck_at_launcher = stuck_at_launcher
        self.pages = []
        self.closed = False

    def new_page(self):
        p = FakePage(
            self,
            entra_valid=self._entra_valid,
            exchange_delay_polls=self._exchange_delay_polls,
            stuck_at_launcher=self._stuck_at_launcher,
        )
        self.pages.append(p)
        return p

    def cookies(self):
        return self.cookies_jar.all()

    def clear_cookies(self, *, name=None, domain=None, path=None):
        """Mirrors Playwright's BrowserContext.clear_cookies(name=...)."""
        if name == "AUTH_DATA" or name == "JSESSIONID":
            # Test only exercises the single-name calls establish_session
            # makes; a real name filter would need proper matching if this
            # fake ever needs more.
            self.cookies_jar._cookies = [
                c for c in self.cookies_jar._cookies if c["name"] != name
            ]

    def close(self):
        self.closed = True


@pytest.fixture
def authed_context():
    """Profile with a healthy, long-lived Entra credential."""
    return FakeContext(entra_valid=True)


@pytest.fixture
def expired_context():
    """Profile whose Entra credential has expired — needs a human."""
    return FakeContext(entra_valid=False)


@pytest.fixture
def stale_cookie_context():
    """A persistent profile that already holds AUTH_DATA/JSESSIONID from a
    PREVIOUS run, before this run's navigation happens at all.

    Chrome's launch_persistent_context() keeps session-scoped cookies
    (expires=-1) alive across separate process launches — they are not an
    artifact of the current navigation. Observed live: `ctx.cookies()`
    returned AUTH_DATA immediately after launch_headless(), with zero
    navigation having occurred yet.

    This is what made wait_for_session()'s "does AUTH_DATA exist" check a
    false positive in production: a genuinely stuck/slow launcher (this
    run's goto() never reaching samlsuccess) still reported success because
    a stale cookie from an earlier run satisfied the check.
    """
    ctx = FakeContext(entra_valid=True, stuck_at_launcher=True)
    ctx.cookies_jar.set_agilquest_session()  # present BEFORE any navigation
    return ctx


@pytest.fixture
def profile_dir(tmp_path):
    """A throwaway Chrome user_data_dir."""
    d = tmp_path / "user_data"
    d.mkdir()
    return d
