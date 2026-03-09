Feature: Harness IDP Workspace Provisioning
  As a Cloud Engineer
  I want to provision workspaces via Harness IDP
  So that I can automate infrastructure and configuration setup

  Background:
    Given the Harness integration is configured
    And a valid APMS ID "92416"
    And a target environment "dev"

  @integration @harness @workspace
  Scenario: Successfully provisioning a new workspace
    Given the Harness Scaffolder API is available
    When I provision the workspace for APMS "92416" in "dev"
    Then a task should be created in Harness
    And the system should monitor the task until it completes successfully
    And the user should see the task URL

  @integration @harness @error-handling
  Scenario: Provisioning fails when required credentials are missing
    Given the Harness API key is not set
    When I attempt to provision the workspace
    Then it should fail with a "HARNESS_API_KEY not found" error
    And no task should be submitted to Harness

  @integration @harness @error-handling
  Scenario: Handling Harness task failure
    Given a Harness task is created
    But the task execution fails in Harness with error "Repository already exists"
    When the system monitors the task
    Then it should report the failure to the user
    And the error message should be displayed

  @integration @harness @fail-fast
  Scenario: Provisioning fails fast when credentials are missing
    Given the Harness API key is not set
    When I attempt to provision the workspace
    Then the provisioning should fail immediately
    And an error message regarding missing credentials should be displayed

  @integration @harness @idempotency
  Scenario: Generic template execution with custom parameters
    Given the Harness Scaffolder API is available
    When I execute a template "MyTemplateV3" with parameters:
      | param1 | value1 |
      | param2 | value2 |
    Then a task should be created with the provided parameters
    And the system should monitor the task until it completes successfully

  @integration @harness @error-handling
  Scenario: Task polling timeout handling
    Given a long-running task in Harness
    And the task is configured with a 5 second timeout
    When I poll the task
    Then a TimeoutError should be raised
    And the task ID should be displayed for manual inspection
