# 0002. The report server exposes an allow list, not $HOME

- Status: Accepted, amended by [0003](0003-report-server-tailnet-access.md) (network rule)
- Date: 2026-10-30
- Context: /understand design session, node `delivery.serve-root` ([decision tree](../explanation/understand/decision-tree.md))

| Y-statement | |
| :-- | :-- |
| In the context of | serving reports from the VM to the host Mac over the Parallels network |
| facing | the wish to link to any file under $HOME, which holds live secrets |
| we decided for | an allow list of serve roots: `/r/` = shadow root, `/src/` = `~/projects`; dotfiles and dot dirs blocked; everything else 404 |
| and neglected | all of $HOME with a dotfile deny list; shadow root only |
| to achieve | working source links without exposing keys or tokens |
| accepting that | a new serve root needs a deliberate config change |
| because | $HOME holds `~/.ssh/id_ed25519`, `~/.aws/credentials`, `~/.vault-token`, `~/.netrc`, `~/.pi/agent/auth.json` and OAuth tokens; one missed deny rule leaks a secret to the network |
| revisit when | reports need files outside `~/projects` often |

## Rules

- ~~The server MUST listen only on the Parallels address and MUST deny clients outside `10.211.55.0/24`.~~ Superseded by [ADR 0003](0003-report-server-tailnet-access.md).
- The server MUST return 404 for any path segment that starts with `.`.
- The server MUST NOT follow symlinks that leave a serve root.
- The server MUST run as the user, not as root.
