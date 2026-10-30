@spec-3 @spec-5 @adr-0001
Feature: Read a report
  A reader moves through a report from structure to source lines.
  Other agents link to the same places by anchor.

  @step-1
  Scenario: A report opens without network access
    Given a report on a computer with no network connection
    When the reader opens the report
    Then all sections, diagrams, and the graph are shown

  @step-1
  Scenario: A link to a cited line opens that line
    Given the report cites line 42 of "src/app.ts"
    When the reader follows the citation
    Then the source view of "src/app.ts" opens at line 42

  @step-1
  Scenario: Every line of a source view can be linked
    Given the report cites "src/app.ts", which has 120 lines
    Then the source view of "src/app.ts" has a link target for each of the 120 lines

  @step-1
  Scenario: Every node and section of the report has its anchor
    Given the bundle has a node with the anchor "src/app.ts" and a section with the anchor "overview"
    Then the report has a place named "src/app.ts" and a place named "overview"

  @step-1
  Scenario: An anchor for a function stays the same when files are reordered
    Given the function "parseConfig" in "src/config.ts" has an anchor in a first report
    When a second report is made after the files are listed in a different order
    Then the anchor of "parseConfig" is the same in both reports

  @step-1
  Scenario: An agent finds the place of an anchor without opening the report
    Given the report has an anchor for the function "parseConfig" in "src/config.ts"
    Then the anchor index gives the report address, the file, and the line of "parseConfig"
