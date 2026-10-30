@spec-1 @spec-2
Feature: Focus a report with a lens
  A lens selects what a report is about: a topic, a pull request, or a diff.
  The report highlights the focus set and keeps the full map for orientation.

  @wip @step-5
  Scenario: A pull request report does not change the user's branch
    Given the user is on branch "main"
    When the user makes a report of pull request 123
    Then the user is still on branch "main"

  @wip @step-5
  Scenario: A pull request report shows the code as it is at the head of the pull request
    Given pull request 123 changes "src/app.ts" on its branch
    When the user makes a report of pull request 123
    Then the source view of "src/app.ts" shows the file as it is at the head of pull request 123

  @wip @step-5
  Scenario: A pull request report leaves no extra worktree
    Given a report of pull request 123 has finished
    Then the repository has no worktree for pull request 123

  @wip @step-5
  Scenario: A failed pull request report leaves no extra worktree
    Given a report of pull request 123 stops during discovery
    Then the repository has no worktree for pull request 123

  @wip @step-5
  Scenario: A diff report includes uncommitted work
    Given "src/new.ts" has an uncommitted change
    When the user makes a report of the diff against "main"
    Then "src/new.ts" is in the focus set

  @wip @step-5
  Scenario: A diff report excludes changes made only on the base branch
    Given "src/other.ts" changed on "main" after the current branch split from it
    And "src/other.ts" did not change on the current branch
    When the user makes a report of the diff against "main"
    Then "src/other.ts" is not in the focus set

  @wip @step-5
  Scenario: A topic finds code that uses a different word
    Given "billing/backoff.py" schedules failed payments again
    And no file in the repository contains the word "retry"
    When the user makes a report on "how billing retries work"
    Then "billing/backoff.py" is a seed node

  @wip @step-5
  Scenario: A direct neighbour of a seed node is in the focus set
    Given "billing/retry.py" uses "billing/clock.py"
    When the user makes a report on "retry" and "billing/retry.py" is a seed node
    Then "billing/clock.py" is in the focus set

  @wip @step-5
  Scenario: Nodes outside the focus set stay on the map
    Given a topic report where "auth/login.py" is not in the focus set
    Then the report shows "auth/login.py" dimmed
