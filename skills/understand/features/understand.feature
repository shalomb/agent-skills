Feature: Understand a repository through a report
  A user wants a navigable report of a repository, or part of one,
  so that people and agents can learn its structure fast.

  Rule: The repository stays read-only

    Scenario: A full run does not change the repository
      Given a git repository with a clean working tree
      When the user runs "/understand"
      Then the working tree is still clean
      And the report is in the shadow directory for that repository

    Scenario: A pr run does not change the user's checkout
      Given the user is on branch "main"
      And pull request 123 has head commit "abc123"
      When the user runs "/understand pr 123"
      Then the user is still on branch "main"
      And no worktree for pull request 123 remains after the run

  Rule: Each run is kept by commit and lens

    Scenario: The latest link points to the newest run
      Given two runs of "/understand" at commits "c1" and "c2"
      Then "latest" for the full lens points to the run at "c2"

    Scenario: Only five runs are kept per lens
      Given five runs exist for the topic lens "auth"
      When the user runs "/understand auth" again
      Then five runs exist for the topic lens "auth"
      And the oldest run is gone

  Rule: The report server shows only serve roots

    Scenario Outline: Secrets are never served
      When the host requests "<path>" from the report server
      Then the response status is 404
      Examples:
        | path                      |
        | /src/../.ssh/id_ed25519   |
        | /src/shalomb/repo/.env    |
        | /.aws/credentials         |

    Scenario: A client outside the Parallels network is refused
      When a client at "100.99.83.10" requests "/r/"
      Then the response status is 403

  Rule: A topic report keeps the full map

    Scenario: Nodes outside the focus set are dimmed, not removed
      Given a repository where "billing/retry.py" mentions "retry"
      And "billing/retry.py" imports "billing/clock.py"
      When the user runs "/understand how billing retries work"
      Then "billing/retry.py" is a seed node
      And "billing/clock.py" is in the focus set
      And every other node is shown dimmed

  Rule: The glossary shows collisions

    Scenario: One term with two meanings in two contexts
      Given "Account" means "payer of invoices" in context "billing"
      And "Account" means "login principal" in context "identity"
      When a report is made
      Then the glossary lists "Account" under both contexts
      And the glossary flags "Account" as a collision

  Rule: Non-code directories get a docs profile

    Scenario: A docs-only directory that is not a git repository
      Given a directory with only Markdown files and no git repository
      When the user runs "/understand"
      Then the report shows a document map, a glossary, and a reading order
      And the report has no dependency graph section

  Rule: Every cited line has an anchor

    Scenario: A report link opens the exact source line
      Given the report cites "src/app.ts" line 42
      When the reader follows that link
      Then a source view for "src/app.ts" opens at the element with id "L42"
      And anchors.json maps the citation id to that URL
