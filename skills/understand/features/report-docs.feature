@spec-2
Feature: Report on a directory of documents
  A directory of documents has no code to map.
  Its report shows how to read the documents.

  @wip @step-4
  Scenario: A directory of documents gets a reading order
    Given a directory that contains only Markdown documents
    When the user makes a report of the full directory
    Then the report gives a reading order of the documents

  @wip @step-4
  Scenario: A directory of documents gets a document map
    Given a directory that contains only Markdown documents that link to each other
    When the user makes a report of the full directory
    Then the report shows which document links to which
