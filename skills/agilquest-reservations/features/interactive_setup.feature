Feature: Interactive SSO setup
  As a person running `aq setup-auth`
  I want the tool to tell me the truth about what it is doing
  So that I can trust its verdict at the one moment a human is actually present

  # setup_auth.py is the *source* of the durable Entra credential that
  # features/auth_and_session.feature's headless automation then reuses for
  # months. It shares the same protocol (same launcher, same redirect chain,
  # same client-side token exchange) and is vulnerable to the same class of
  # bug — a stale reported URL, a session declared live before the exchange
  # finishes — but the failure mode is worse here: a human is watching, and
  # a tool that lies to their face about "success" erodes the one channel
  # that catches what automation can't.

  Background:
    Given a person has launched `aq setup-auth`
    And a headed browser window is visible to them

  Rule: The tool never shows a reported location it knows to be stale

    # Same underlying bug as auth_and_session.feature's "Bug #1", but here
    # the audience is a human reading terminal output live, not a headless
    # branch. Printing the stale intermediate URL during the mid-redirect
    # window tells the person "still on Microsoft" while they are in fact
    # already signed in — actively misleading at the one moment their
    # judgment is supposed to be the safety net.

    Scenario: Diagnostic output reflects the true location, not the stale one
      Given the browser has completed the SAML exchange but its reported
        location is still mid-redirect
      When the tool prints the current URL for the person to read
      Then the printed URL is the true location
      And it does not print a Microsoft login URL for an already-authenticated session

  Rule: Success is only declared once the session is provably live

    # Same underlying bug as auth_and_session.feature's "Bug #3". Declaring
    # victory the moment the redirect chain parks at /samlsuccess — before
    # the SPA's token exchange has actually completed — can tell a person
    # their setup succeeded when the very next headless run will bounce to
    # a login screen.

    Scenario: The tool waits for the session exchange before declaring success
      Given the redirect chain has parked at the post-SAML URL
      And the token exchange has not yet completed
      When the tool checks whether setup succeeded
      Then it does not yet report success
      And it continues waiting rather than confirming prematurely

    Scenario: The tool confirms success only once the session is verified live
      Given the token exchange has completed
      When the tool checks whether setup succeeded
      Then it reports success
      And a subsequent headless run can reuse the session without interactive login

  Rule: The profile lock is cleared through one shared implementation

    # setup_auth.py grew its own clear_singleton_lock() before the shared
    # one existed in lib/browser.py. Two implementations of the same fix
    # drift: a change to one (e.g. a corrected PID-liveness check) silently
    # does not apply to the other.

    Scenario: Interactive setup clears a stale lock the same way headless runs do
      Given a previous run crashed and left the profile locked
      When the person runs `aq setup-auth`
      Then the lock is cleared by the same implementation the headless entry points use
      And the browser launches successfully

  Rule: A genuine login prompt and a mid-exchange page are never confused

    # The polling loop that waits for a human to finish typing must not
    # mistake "still authenticating" for "needs to type credentials", and
    # must not mistake a stale reported URL for a login prompt either.

    Scenario: The tool recognises a real login prompt by the form it renders
      Given Entra is presenting a genuine login form
      When the tool decides whether to prompt the person to sign in
      Then it prompts them to complete Entra SSO

    Scenario: The tool does not prompt for login during an automatic mid-exchange pause
      Given the session is authenticating automatically with no form presented
      When the tool decides whether to prompt the person to sign in
      Then it does not prompt them
      And it proceeds to wait for the exchange to complete
