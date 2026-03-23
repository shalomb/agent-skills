Feature: Teams Chat Search and Extraction
  As an agent
  I want to search and extract messages from Teams Web V2
  So that I can analyze conversations and meeting recaps

  Scenario: Basic chat extraction by name
    Given I am authenticated with Teams Web V2
    When I search for chat with "Suhasini"
    Then I should be switched to that chat
    And I should receive the last 10 messages with author and body

  Scenario: Meeting recap and transcript extraction
    Given I am authenticated with Teams Web V2
    When I search for "Call to Discuss AMI Creation"
    And I click "View recap"
    And I switch to the "Transcript" tab
    Then I should receive the full meeting transcript segments as Markdown

  Scenario: Image metadata extraction from chat
    Given a chat message contains an embedded image
    When I extract the message metadata
    Then I should receive the image src and alt text
    And I should be able to optionally download the image
