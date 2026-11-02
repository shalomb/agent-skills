# 0005. Hybrid discovery with hard token ceiling and dual navigation

- Status: Accepted
- Date: 2026-11-02
- Context: /understand design session, nodes `discovery.cost-and-quality`, `links.github-navigation` ([decision tree](../explanation/understand/decision-tree.md))

| Y-statement | |
| :-- | :-- |
| In the context of | generating rich architectural reports without runaway token costs or brittle links |
| facing | the high token burn of swarm delegates and the fragility of online-only GitHub links |
| we decided for | hybrid discovery (static pre-scan at 0 tokens + max 2-3 delegates capped at 8k tokens) with dual navigation (local source primary, remote git secondary) |
| and neglected | pure static extraction without LLM insight; full unconstrained LLM delegate swarms; remote-only links |
| to achieve | predictable sub-minute execution, bounded token cost, guaranteed offline readability, and seamless jump to GitHub |
| accepting that | LLM synthesis is scoped to central hubs and complex boundaries rather than every file |
| because | 80% of codebase topology is extracted deterministically for free, while 20% deep semantic intent is captured within a strict 8k token ceiling |
| revisit when | local zero-cost LLM models make unconstrained token consumption free |

## Decision drivers

- DRV-01 Bounded discovery cost: guaranteed token ceiling (<= 8,000 tokens) and latency ceiling (< 45s).
- DRV-02 Offline resilience: reports and source views remain 100% functional without an active internet connection.
- DRV-03 Developer workflow integration: seamless jump from report citations directly to GitHub/GitLab commit blobs.
- DRV-04 Partial-failure salvage: a timed-out or failed delegate gracefully falls back to deterministic static topology.

## Options

| Option | DRV-01 | DRV-02 | DRV-03 | DRV-04 |
| :-- | :-: | :-: | :-: | :-: |
| **Hybrid discovery + dual navigation** | yes | yes | yes | yes |
| Pure deterministic static analysis | yes | yes | no | yes |
| Full LLM delegate swarm | no | yes | yes | no |
| Remote-only links | yes | no | yes | yes |

## Consequences

- Pre-scan leverages `codemap --deps` and AST analysis at zero token cost.
- High-level delegates are capped at 8,000 tokens total and 30s timeout per worker.
- Source view links (`src/<path>.html#L<line>`) remain the primary offline anchor.
- Git remotes are deterministically parsed to emit commit-pinned GitHub/GitLab badges.
