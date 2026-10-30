@spec-1
Feature: Start a report run
  The user starts a run from pi to get a report of the current directory.
  A run reads the directory and never changes it.

  @wip @step-3
  Scenario: A run leaves uncommitted work as it was
    Given a repository with an uncommitted change to "src/app.ts"
    When the user makes a report of the full repository
    Then the working tree has the same uncommitted change to "src/app.ts"

  @wip @step-3
  Scenario Outline: A short command makes the same lens as its subcommand
    When the user starts a run with "<short command>"
    Then the lens is the same as for "<subcommand>"

    Examples:
      | short command         | subcommand             |
      | /understand-pr 123    | /understand pr 123     |
      | /understand-diff main | /understand diff main  |

  @wip @step-3
  Scenario: A directory without git gets a report of its full content
    Given a directory that is not a git repository
    When the user makes a report of the full directory
    Then the report shows the files and folders of the directory

  @wip @step-3
  Scenario: A directory without git gets a topic report
    Given a directory that is not a git repository
    When the user makes a report on "onboarding"
    Then the report is about "onboarding" and shows no git history section

  @wip @step-3
  Scenario: A directory without git cannot get a pull request report
    Given a directory that is not a git repository
    When the user asks for a report of pull request 1
    Then the user is told that a pull request report needs a git repository

  @wip @step-3
  Scenario Outline: The user sees which phase a run is in
    Given a run is in the phase "<phase>"
    Then the status line shows the phase "<phase>"

    Examples:
      | phase    |
      | plan     |
      | discover |
      | converge |
      | render   |

  @wip @step-3
  Scenario Outline: The user can pick a lens from the command
    When the user types "/understand " and asks for completion
    Then the choices include "<lens>"

    Examples:
      | lens |
      | pr   |
      | diff |

  @wip @step-3 @adr-0003
  Scenario: The end message gives a report address for each network
    When a run finishes
    Then the end message gives one report address for the Parallels network and one for the tailnet

  @wip @step-3
  Scenario: The end message is short
    When a run finishes
    Then the summary in the end message has 5 lines or less
