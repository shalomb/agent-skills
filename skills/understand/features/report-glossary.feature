@spec-3 @spec-5
Feature: Learn the terms of a repository from its report
  The glossary is the last section of every report.
  It shows each term in its context and flags terms with more than one meaning.

  @wip @step-6
  Scenario: Contexts come from the repository glossary map
    Given the repository has a glossary map with the contexts "billing" and "identity"
    When a report is made
    Then the glossary groups its terms under "billing" and "identity"

  @wip @step-6
  Scenario: Contexts are found when the repository has no glossary map
    Given the repository has no glossary map
    And the areas "src/billing" and "src/identity" use different terms
    When a report is made
    Then the glossary groups its terms under a context for each of the two areas

  @wip @step-6
  Scenario: A term with two meanings is flagged as a collision
    Given "Account" means "payer of invoices" in the context "billing"
    And "Account" means "login principal" in the context "identity"
    When a report is made
    Then the glossary flags "Account" as a collision with a link to each meaning

  @wip @step-6
  Scenario: The report offers a glossary draft for the repository
    Given the repository has no glossary
    When a report is made
    Then the report offers a glossary draft that the user can apply

  @wip @step-6
  Scenario: A report never writes the glossary draft to the repository
    Given the repository has no glossary
    When a report is made
    Then the repository has no new or changed glossary file
