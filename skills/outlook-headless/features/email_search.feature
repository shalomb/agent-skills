Feature: Outlook Email Search and Extraction
  As an agent
  I want to search and extract emails from Outlook Web
  So that I can analyze their content and metadata

  Scenario: Basic search by query
    Given I am authenticated with Outlook Web
    When I search for "GMSGQ EHS"
    Then I should receive a list of matching emails
    And each email should contain a subject, sender, and body

  Scenario: Advanced search with filters
    Given I am authenticated with Outlook Web
    When I search for emails:
      | sender | boss@example.com |
      | after  | 2024-01-01       |
      | unread | true             |
    Then the search query should be "from:boss@example.com received:>2024-01-01 isread:no"

  Scenario: Extracting email from Deleted Items
    Given I am authenticated with Outlook Web
    When I navigate to the "Deleted Items" folder
    And I list the last 10 headers
    Then I should see a list of deleted emails with accurate timestamps and senders

  Scenario: Robust body extraction with imagery
    Given an email contains HTML tables and embedded images
    When I extract the email body
    Then the body should be converted to clean Markdown
    And the image metadata should include src, alt, width, and height
    And I should be able to optionally download the images locally
