@spec-1 @spec-6
Feature: Report Catalog Dashboard and Seamless Navigation
  The user accesses the report server root to search and filter past runs,
  and follows links to local source views or remote GitHub blobs.

  @step-7
  Scenario: Root URL presents the client-side catalog dashboard
    Given the report server is running
    When the user navigates to "/r/understand/"
    Then the page loads the catalog dashboard
    And the dashboard lists recent runs across repositories

  @step-7
  Scenario: Directory URL without file name automatically serves report.html
    Given a report run has completed for "service-now" under lens "full"
    When the user requests the directory URL "/r/understand/service-now/full/latest/"
    Then nginx serves "report.html" with status 200

  @step-7
  Scenario: Source file citations provide dual links when remote exists
    Given a repository has git remote origin "git@github.com:example-org/my-repo.git"
    And a report run finishes on commit "a1b2c3d"
    When the user inspects a source citation for "src/app.py" at line 42
    Then the citation has an offline link to "src/src/app.py.html#L42"
    And the citation has a remote link to "https://github.com/example-org/my-repo/blob/a1b2c3d/src/app.py#L42"

  @step-7
  Scenario: Remote links degrade gracefully when no git remote is configured
    Given a repository has no git remote origin
    When a report run finishes
    Then source citations contain local offline links
    And no remote repository links are shown

  @step-7
  Scenario: Hybrid discovery enforces token and latency ceilings
    Given a large repository with multiple central hubs
    When the hybrid discovery process runs
    Then the total LLM token usage does not exceed 8000 tokens
    And any individual delegate execution times out after 30 seconds
    And timed-out delegates fall back to static analysis without aborting the run
