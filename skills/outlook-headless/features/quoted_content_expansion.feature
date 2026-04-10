Feature: Quoted and Forwarded Content Expansion
  As an agent
  I want to expand and parse quoted/forwarded email chains within a single message
  So that I can extract each individual forwarded message as a separate structured record

  Background:
    Given the parser is initialized

  Scenario: Expanding a single forwarded message with standard headers
    Given a message body contains one forwarded block with headers:
      | From    | Neuber, Anton <anton.neuber@vendor.com>             |
      | Sent    | Monday, October 27, 2025 2:10 PM                   |
      | To      | Dattenny, Stéphane <stephane.dattenny@takeda.com>  |
      | Subject | Re: LIP AWS Migration - Infrastructure Requirements |
    When I parse the forwarded chain
    Then I should get 1 sub-message
    And the sub-message sender should contain "Neuber, Anton"
    And the sub-message timestamp should contain "October 27, 2025"

  Scenario: Parsing a deeply nested forwarded chain (10+ messages)
    Given a message body contains a forwarded chain of 10 messages
    And each message has From, Sent/Date, To, and Subject headers
    When I parse the forwarded chain
    Then I should get 10 sub-messages
    And the sub-messages should be ordered from most recent to oldest
    And each sub-message should have a non-empty body

  Scenario: Handling mixed header formats in forwarded content
    Given a forwarded chain contains headers in different formats:
      | format   | example                                |
      | Sent:    | Sent: Thursday, March 5, 2026 11:13 PM |
      | Date:    | Date: Wednesday, 8 April 2026 at 13:47 |
      | Envoyé : | Envoyé : mardi 21 octobre 2025 16:45   |
    When I parse the forwarded chain
    Then each sub-message should have a parsed timestamp
    And the parser should handle multilingual header labels (De, Envoyé, Objet, À)

  Scenario: Clicking intra-message expansion controls before extraction
    Given Outlook has collapsed quoted content within a message body
    And the message body contains a "..." or ellipsis toggle button
    When the client expands intra-message content
    Then the hidden forwarded content should become visible in the DOM
    And the full forwarded chain should be available for parsing

  Scenario: Forwarded chain with divRplyFwdMsg markers
    Given a message body contains HTML with divRplyFwdMsg elements
    And some markers use the "x_divRplyFwdMsg" variant
    When I parse the forwarded chain
    Then each divRplyFwdMsg boundary should start a new sub-message
    And headers within each block should be correctly extracted
    And body content between markers should be captured

  Scenario: Regex fallback when no divRplyFwdMsg markers exist
    Given a message body contains forwarded headers as plain text
    And the headers follow "From:/Sent:/To:/Subject:" pattern without HTML markers
    When I parse the forwarded chain
    Then the regex fallback strategy should split on header blocks
    And each sub-message should have sender, timestamp, and body extracted

  Scenario: Graceful handling of partial or missing headers
    Given a forwarded block is missing the Subject line
    When I parse the forwarded chain
    Then the sub-message should still be created
    And the subject should be null or empty
    And the sender and body should still be extracted

  Scenario: No forwarded content returns empty list
    Given a message body contains only plain text with no forwarded headers
    When I parse the forwarded chain
    Then I should get 0 sub-messages
    And the original message should be returned unchanged
