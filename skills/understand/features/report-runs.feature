@spec-4
Feature: Keep the reports of earlier runs
  Each run is kept by commit and lens, so the user can compare reports
  and use an earlier report while a new run is in progress.

  @wip @step-3
  Scenario: Latest is the newest run of a lens
    Given runs of the full repository at commit "c1" and then at commit "c2"
    Then the latest report of the full repository is the one at commit "c2"

  @wip @step-3
  Scenario: A lens keeps its five newest runs
    Given five runs of the topic "auth"
    When the user makes a sixth report on "auth"
    Then the oldest report on "auth" is removed

  @wip @step-3
  Scenario: Runs of one lens do not remove runs of another lens
    Given five runs of the topic "auth" and one run of the full repository
    When the user makes a sixth report on "auth"
    Then the report of the full repository is still there

  @wip @step-3
  Scenario: Reports and todo cards of one repository share one name
    Given the repository has todo cards
    When a report of the repository is made
    Then the report directory and the todo card directory use the same repository name
