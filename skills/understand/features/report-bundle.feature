@spec-3 @adr-0001
Feature: Turn a bundle into a report
  The renderer is the only program that writes report pages.
  It refuses a bundle that it cannot trust, and it still shows diagrams
  on a computer that cannot draw them ahead of time.

  @wip @step-1
  Scenario: A broken bundle gives no report
    Given a bundle where a graph node has no path
    When the renderer runs
    Then no report is made

  @wip @step-1
  Scenario: A broken bundle names the faulty node
    Given a bundle where a graph node has no path
    When the renderer runs
    Then the run says which node has no path

  @wip @step-1
  Scenario: A diagram is shown when it cannot be drawn ahead of time
    Given diagrams cannot be drawn ahead of time on this computer
    When the renderer runs
    Then the report shows each diagram

  @wip @step-1
  Scenario: The run records that diagrams were drawn in the page
    Given diagrams cannot be drawn ahead of time on this computer
    When the renderer runs
    Then the run log says that diagrams were drawn in the page

  @wip @step-1
  Scenario: The glossary is the last section
    When a report is made
    Then the glossary is the last section of the report
