# 0003. The report server also accepts clients from the tailnet

- Status: Accepted
- Date: 2026-10-30
- Amends: [0002](0002-report-server-allow-list.md) (network rule only; the serve-root allow list is unchanged)
- Context: /understand design session, node `delivery.networks` ([decision tree](../explanation/understand/decision-tree.md))

| Y-statement | |
| :-- | :-- |
| In the context of | reading reports from devices other than the host Mac |
| facing | ADR 0002 limits clients to the Parallels network (`10.211.55.0/24`) |
| we decided for | accepting clients from the Parallels network and from the tailnet (`100.64.0.0/10`, `fd7a:115c:a1e0::/48`); all other clients are denied |
| and neglected | Parallels network only; `tailscale serve` in front of the server |
| to achieve | reports readable from any device that the owner signs in to the tailnet |
| accepting that | every tailnet device can read the serve roots, including source under `~/projects` |
| because | the owner wants access from more than one device, and the tailnet is already an authenticated, private network |
| revisit when | the tailnet gains devices or users that must not read source code |

## Rules

These replace the first rule of ADR 0002. The other rules of ADR 0002 stay in force.

- The server MUST accept clients from `10.211.55.0/24`, `100.64.0.0/10`, and `fd7a:115c:a1e0::/48`.
- The server MUST deny all other clients.
- The server MUST NOT accept clients on any other interface of the VM.
- The server MUST keep serving the Parallels network when tailscale is down.
- The end message MUST give the report URL for each network.

## Consequences

- Tailnet ACLs become part of the security boundary for source code.
- ADR 0002 rule 1 is superseded. Its serve-root rules (dot segments, symlinks, run as user) apply to both networks.
