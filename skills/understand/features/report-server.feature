@spec-6 @adr-0002 @adr-0003
Feature: Show reports to the devices of the owner
  The report server shows reports and cited source to the host Mac and to
  tailnet devices, and to no other device. It never shows secrets.

  @step-2
  Scenario Outline: A device on a permitted network gets the report index
    Given <device>
    When the device asks for the report index
    Then the device gets the report index

    Examples:
      | device                                    |
      | the host Mac on the Parallels network     |
      | a laptop on the tailnet with an old-style address |
      | a phone on the tailnet with a new-style address   |

  @step-2
  Scenario Outline: A device just outside a permitted network is denied
    Given <device>
    When the device asks for the report index
    Then no report is served to the device

    Examples:
      | device                                              |
      | a device in the next network after the Parallels network |
      | a device in the first address after the tailnet range    |
      | a device on a home network                               |

  @step-2
  Scenario: The report server is not reachable on other interfaces of the VM
    Given a device that reaches the VM on an interface that is not the Parallels network or the tailnet
    When the device asks for the report index
    Then no report is served to the device

  @wip @step-2
  Scenario: The host Mac still gets reports when tailscale is down
    Given tailscale is down
    When the host Mac asks for the report index
    Then the host Mac gets the report index

  @step-2
  Scenario Outline: A hidden file in a serve root is not found
    When a permitted device asks for "<path>"
    Then the device is told that the file is not found

    Examples:
      | path                        |
      | /src/shalomb/repo/.env      |
      | /src/shalomb/repo/.git/config |
      | /r/.hidden/report.html      |

  @step-2
  Scenario: A file outside the serve roots is not found
    When a permitted device asks for "/.ssh/id_ed25519"
    Then the device is told that the file is not found

  @step-2
  Scenario: A link that leaves a serve root is not followed
    Given "~/projects/demo/keys" links to "~/.aws"
    When a permitted device asks for "/src/demo/keys/credentials"
    Then the device is told that the file is not found

  @step-2
  Scenario: The report server starts without administrator rights
    Given the user has no administrator rights
    When the user starts the report server
    Then the report server accepts requests
