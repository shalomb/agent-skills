# 0001. Agents write a bundle; one fixed renderer makes the report

- Status: Accepted
- Date: 2026-10-30
- Context: /understand design session, node `render.model` ([decision tree](../explanation/understand/decision-tree.md))

| Y-statement | |
| :-- | :-- |
| In the context of | generating interactive HTML reports of repositories with LLM delegates |
| facing | the need for clickable graphs, a consistent look, and testable output |
| we decided for | a bundle (`graph.json`, `anchors.json`, Markdown sections, glossary) rendered by one fixed, tested renderer |
| and neglected | Markdown with Mermaid only; agents writing raw HTML |
| to achieve | structured data for interactivity, one design system, low token cost, unit-testable rendering |
| accepting that | the bundle schema is a contract that we must version and keep stable |
| because | prose cannot drive a filterable graph, and per-run HTML from an agent cannot be tested or kept consistent |
| revisit when | the bundle schema needs a breaking change more than once a quarter |

## Decision drivers

- DRV-01 Interactive graph (filter, search, click to source).
- DRV-02 Same look across all reports and the index page.
- DRV-03 Rendering is deterministic and unit-tested.
- DRV-04 Low token cost per run.

## Options

| Option | DRV-01 | DRV-02 | DRV-03 | DRV-04 |
| :-- | :-: | :-: | :-: | :-: |
| **Bundle + fixed renderer** | yes | yes | yes | yes |
| Markdown + Mermaid (build.py) | no | yes | yes | yes |
| Agent writes HTML | yes | no | no | no |

## Consequences

- The bundle schema lives in the skill and is validated before render.
- Agents never write HTML. A render failure is a bundle bug or a renderer bug, never "the agent drew it wrong".
