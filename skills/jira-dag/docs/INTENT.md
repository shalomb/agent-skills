# jira-dag: intent

A read-only page that helps a PO or lead talk through a platform ART's backlog with stakeholders: what depends on what,
what to slice next, and what a plan change would do. This file holds the principles and decisions the code and the
BDD specs (`specs/`) are anchored to. Scenarios cite them by id (`@P6`, `@D3`). Change an id's meaning only on purpose.

## Context
- **L1** = INTREQ epics: product requests, the interface where product teams register interest in being enabled.
- **L2** = PLTDSO, PLTDPE, PLTAPE epics: platform capabilities. **Value is released from L2.**
- Products (stream-aligned teams) sit *on* the platform; PODs are *in* the platform. No product data yet.
- Enablement is incremental: a product may first be enabled by a manual step so it can start and give feedback.

## Principles
| id | Principle |
|---|---|
| P1 | **Read-only on Jira.** The page never writes. Changes are drafted in a plan; a separate guarded step applies them after approval. |
| P2 | **A conversation tool.** Output is a snapshot for discussion, not a validated record. It says when it was fetched. |
| P3 | **Config, not code.** PODs, interface, products and policies come from one config blob. Anything not in it is external. |
| P4 | **Epic level first.** Capacity and team views come later. Do not design for them yet beyond leaving room. |
| P5 | **Slices are releasable.** A slice ships value or learning on its own. Its length is capped (days, per POD policy); over the cap means split. A manual first rung is fine if the debt is recorded and a later slice repays it. |
| P6 | **Show only what matters.** Relationships appear on demand (hover, pin, filter). Hidden things leave no gaps; neighbours of what you chose stay as ghosts so no link vanishes silently. |
| P7 | **Data quality is a rule set.** Each check has an id, reason, test and fix hint, and is reused by badges, lists, filters and slicing. |
| P8 | **Unknown is not zero.** Missing dates, scores or L1 need-by dates are findings, never silently scored low. |
| P9 | **Screen space belongs to the diagram.** Controls sit in a drawer or a slim row, not above the picture. |
| P10 | **Behaviour first.** Behaviour is a scenario before it is code. Logic is pure and tested without a browser; the browser is checked with a few scenarios on synthetic data. |

## Decisions
| id | Decision | Why |
|---|---|---|
| D1 | L2 epics are ranked with WSJF; L1 is still being shaped and is not scored by this tool yet. | L2 is where value is released and investment is decided. |
| D2 | Slice WSJF is relative and light: compare slices of one epic, no deep method. Refine later. | Not worth over-engineering; a rough ordering is enough. |
| D3 | Slices live in the plan, not in Jira. | Jira holds WSJF fields only on Epic (checked for PLTDSO). |
| D4 | A plan is an overlay of operations on a Jira snapshot. Versions are git branches rendered from worktrees, in a private location (`~/.local/share/po-plans/<PROJECT>/`). | Compare scenarios side by side, replay on a fresh fetch, apply later. |
| D5 | One browser renderer fed by a JSON model. Dependencies folds into Topologies. The story view is retired (done). | One layout, one set of behaviours. |
| D6 | Filters apply to every tab: multi-select labels grouped by prefix (OR within a group, AND between), components (on, empty until used), a date-range slider with an Undated toggle, and relationship toggles (incoming, external, blocking others). Pinned epics override filters. | A PO scopes to a horizon without losing cross-POD links. |
| D7 | Slice size is in working days, cap per POD in config (continuous-delivery appetite varies by POD). | Days make the cap testable; PODs differ. |
| D8 | Pin allows several epics; depth is Direct by default, Full chain optional. | Compare similar epics; keep the view small. |
| D9 | One state object (filters, pins, depth, hover) drives rendering; the URL hash is that state. | Ends scattered handlers and stale-state bugs. |
| D10 | Slice fields: id, epic, title, kind (enabler or deliverable), mode (manual, scripted, self-service, automated), days, value share, unblocks, releasable, learn, debt. | Captures the enablement ladder and its debt. |

## Open questions
- Names the PODs use for the ladder rungs; which PODs are most continuous-delivery minded (seeds per-POD caps).
- How L1 need-by dates and value will be recorded once L1 is shaped.
- 1-in-1-out rule: what counts as a unit when capacity is not modelled.
- Whether any shared page still needs the standalone `epics.svg` and `jira_dag.py` / `jira_timeline.py` tools.

## Order of work
1. Characterise current client behaviour as scenarios (`specs/topology-pin-hover.md`).
2. Data-quality rule set (`specs/data-quality-rules.md`) and plan overlay model (`specs/plan-overlay.md`): pure Python, independent.
3. Then, building on 1: JSON model and browser renderer, state model, filter drawer, Dependencies folded in.
4. Then: slicing in the plan, guarded apply to Jira.
