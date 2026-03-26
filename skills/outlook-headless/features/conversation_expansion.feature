Feature: Conversation Thread Expansion
  As an agent
  I want to expand collapsed email conversations in Outlook
  So that I can extract all messages in a thread, not just the most recent one

  Scenario: Expanding a multi-message thread with a "X messages" button
    Given an Outlook conversation contains 9 messages
    And the reading pane shows a "9 messages" expansion button
    When I search for and select the "Simca Online Server" thread
    Then I should click the "9 messages" button
    And the reading pane should show all 9 message containers

  Scenario: Expanding a thread with individual collapsed messages
    Given an Outlook conversation has 3 messages from different senders
    And 2 of the messages are collapsed in the reading pane
    When I extract the full thread content
    Then I should identify all 3 message headers
    And each header should be associated with its correct message body

  Scenario: Handling "Show more messages" button
    Given an Outlook conversation has hidden messages
    And a "Show more messages" button is visible at the bottom of the reading pane
    When I extract the full thread content
    Then I should click "Show more messages"
    And all messages should be loaded before extraction
