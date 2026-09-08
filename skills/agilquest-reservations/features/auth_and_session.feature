Feature: Authenticate once, reuse the session headlessly
  As an unattended cron job
  I want to reuse a credential established by a one-off interactive login
  So that reservations can be booked and checked into with no human present

  # The domain has TWO sessions with very different lifetimes. Nearly every
  # bug in this area comes from treating them as one:
  #
  #   Durable Entra credential   ~90 days   renewed by a human, quarterly
  #   Agilquest session          ~10 min    minted fresh on every single run
  #
  # See features/auth_and_session.md for the protocol and the bug catalogue.

  Background:
    Given a browser profile that was interactively authenticated at some point in the past
    And no human is available to interact with the browser

  Rule: A durable Entra credential survives long periods without re-authentication

    # This is THE assumption the whole automation rests on. If this rule ever
    # genuinely fails, the design needs revisiting. Verified against a profile
    # 104 days old, so treat "the credential expired" as a last resort
    # diagnosis, not a first guess.

    Scenario: A months-old credential still authenticates without a human
      Given the profile was last interactively authenticated 104 days ago
      When the automation establishes a session
      Then the session is established successfully
      And no interactive login is requested

    Scenario: The durable credential is the Entra persistent cookie
      When the automation inspects the profile's stored credentials
      Then a persistent Entra credential is present
      And it remains valid for roughly 90 days from the interactive login

    Scenario: A stale storage-state file does not indicate credential health
      # auth.json is a leftover from a superseded auth model (commit 51c4379).
      # Nothing reads it. Its age has misled diagnosis before.
      Given a stale storage-state file exists from a superseded auth model
      When the automation establishes a session
      Then the session is established successfully
      And the stale storage-state file is not consulted

  Rule: The Agilquest session is only live once the token exchange completes

    # The redirect chain parks at /samlsuccess?authToken=... and the URL then
    # STOPS MOVING. The session does not exist yet at that moment — the SPA is
    # still exchanging that token. This pause is the single most misread part
    # of the protocol.

    Scenario: The session is not usable at the moment the redirect chain settles
      When the automation reaches the point where the redirect chain stops moving
      Then the Agilquest session is not yet usable

    Scenario: The session becomes usable once the exchange completes
      When the automation waits for the token exchange to complete
      Then the Agilquest session is usable
      And an authenticated read returns the account's real reservations

    Scenario: Navigating away mid-exchange silently discards the session
      # Bug #3. Observed A/B, 3/3 trials: 0 reservations vs 4, same profile.
      # The failure is silent — an empty result, never an error.
      When the automation navigates to another page before the exchange completes
      Then the session is lost
      And the application presents a login screen instead of the reservations

    Scenario: Waiting for the exchange is mandatory, not cosmetic
      # The current wait is a DOM-selector guess wrapped in `except: pass`, so
      # its failure is invisible. It is load-bearing and must fail loudly.
      Given the token exchange does not complete within the expected time
      When the automation establishes a session
      Then the failure is reported explicitly
      And the automation does not proceed as though authenticated

    Scenario: A cookie from a previous run is never mistaken for this run's exchange
      # Bug #6, found in production the first night this ran unattended.
      # Chrome's persistent profile keeps session-scoped cookies (AUTH_DATA,
      # expires=-1) alive across separate process launches — they are not
      # cleared just because the previous script exited. A stale AUTH_DATA
      # left over from an earlier, unrelated run was already present the
      # moment the profile was opened, before this run had navigated at
      # all. Meanwhile the launcher genuinely never redirected this run (3
      # real 30s timeouts, then a 0.1s "success" that was really just
      # landing back on the launcher page). The stale cookie satisfied a
      # presence check and produced a false "session ready", followed
      # immediately by is_on_agilquest() correctly reporting the page was
      # never on Agilquest at all — an internally contradictory result.
      Given the profile already holds a session cookie left over from a previous run
      And this run's navigation never actually reaches the Agilquest application
      When the automation waits for the token exchange to complete
      Then it does not report the session as usable
      And the failure is attributed to the launcher never landing, not to authentication

  Rule: Session state is judged by authoritative signals, never by URL shape

    # Bug #1, the primary regression (commit e887e70). Navigating with a
    # "commit" wait returns before the redirect chain finishes, leaving the
    # reported URL stale while the real document has moved on.

    Scenario: A stale reported location must not be mistaken for a login prompt
      Given the browser has authenticated but its reported location is still mid-redirect
      When the automation determines whether interactive login is required
      Then it concludes that no interactive login is required

    Scenario: A genuine login prompt is recognised by the presence of a login form
      Given the durable Entra credential has expired
      When the automation determines whether interactive login is required
      Then it concludes that interactive login is required
      And it advises the operator to run the interactive setup

    Scenario: An authenticated page is never misreported as unauthenticated
      Given the browser has authenticated but its reported location is still mid-redirect
      When the automation inspects the page's true location
      Then the true location is within the Agilquest application

  Rule: Failure to authenticate is never reported as an absence of data

    # Bug #4. get_reservations() swallows every exception and returns [],
    # so a lost session looks exactly like "you have no bookings" — which
    # makes ensure_reservation.py try to rebook, masking the real fault.

    Scenario: A lost session is reported as an error, not as zero reservations
      Given the session was lost before the reservations were read
      When the automation reads the reservations
      Then an authentication error is reported
      And the result is not an empty list of reservations

    Scenario: Genuinely having no reservations is distinguishable from failing to read them
      Given the session is valid
      And the account has no active reservations
      When the automation reads the reservations
      Then an empty list of reservations is returned
      And no authentication error is reported

  Rule: The browser profile has exactly one owner at a time

    # Chrome permits one process per user_data_dir. Violations surface as
    # "Page.goto: Timeout" — which implicates the network and sends people
    # to the wrong layer entirely.

    Scenario: A crashed run does not permanently poison the profile
      # Bug #2. The lock-clearing helper exists but only in setup_auth.py,
      # so the four cron entry points never self-heal.
      Given a previous run crashed and left the profile locked
      When the automation establishes a session
      Then the stale lock is cleared automatically
      And the session is established successfully

    Scenario: Interactive re-authentication does not contend with the polling run
      Given the automation has requested interactive re-authentication
      When it polls for the session to become valid
      Then it does not hold the profile open between polls

    Scenario: Re-authentication is launched from the correct working directory
      # Currently correct, and pinned so it stays that way: the path
      # arithmetic looks off at a glance and has already been mistaken for a
      # defect once during review.
      When the automation launches interactive re-authentication
      Then the command runs from the directory containing the project manifest

  Rule: Diagnosis distinguishes the layer that actually failed

    # Bugs #1, #2 and #3 all surfaced as the identical message:
    #   "Page.goto: Timeout 30000ms exceeded"
    # None were network faults. That ambiguity is why earlier fixes added DNS
    # seeding, caffeinate and prewarm jobs against causes that were not there.

    Scenario Outline: Each failure layer is reported distinguishably
      Given the automation cannot establish a session because <cause>
      When an operator inspects the reported failure
      Then the report identifies <layer> as the failing layer
      And the report does not attribute the failure to the network

      Examples:
        | cause                                        | layer                |
        | another process holds the browser profile    | profile lock         |
        | the durable Entra credential has expired     | interactive login    |
        | the token exchange did not complete          | session exchange     |

    Scenario: A genuine network fault is still reported as a network fault
      Given the launcher is genuinely unreachable
      When an operator inspects the reported failure
      Then the report identifies the network as the failing layer
