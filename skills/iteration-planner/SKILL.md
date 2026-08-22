---
name: iteration-planner
description: >
  Orchestrate the transition between GitHub Project iterations (e.g., ORG/PROJECT_NUMBER). Perform a "Sprint Stocktake" of open work and coordinate with the user to schedule the next 2-week iteration. Triggers on: 'sprint planning', 'iteration', 'sprint stocktake', 'plan the next sprint'.
---

# Iteration Planner Skill

Automate the transition between sprint iterations by performing a structured stocktake of open work and facilitating a "Bias for Action" planning session.

## Purpose

Manage the lifecycle of GitHub Project iterations:
- **Sprint Stocktake**: Identify non-completed items (Todo, In Progress, Blocked).
- **Roadmap Discovery**: Identify empty or upcoming iterations via GraphQL.
- **Interactive Planning**: Present a Markdown-based "Planning Sheet" for user review.
- **Bulk Updates**: Automatically transition items to the next iteration or backlog.

## Capabilities

1. **Iteration Discovery**: Fetch full roadmap (Completed, Current, Upcoming).
2. **Carryover Analysis**: Group non-completed items by Status, Priority, and Size.
3. **Retrospective Insights**: Calculate completion rates and identify carryover root causes (Stalled, Underestimated, De-prioritized).
4. **Capacity Forecasting**: Warn if carryover work exceeds historical team velocity.
5. **Planning Sheet Generation**: Create an interactive Markdown sheet in the temp directory.
6. **Rescheduling**: Execute bulk updates confirmed by the user.

## Technical Guides

For command references, GraphQL mutations, and delivery metrics, refer to:
- `references/planning-commands.guide.md`: Core commands for discovery and updates.
- `references/iteration-crud.guide.md`: Instructions for creating/deleting iterations.
- `references/delivery-metrics.guide.md`: Logic for Retro analysis and capacity forecasting.
- `references/roadmap-view-troubleshooting.guide.md`: Why an "Epic" issue doesn't show up in a Roadmap-layout view (hint: it almost always needs a real sub-issue), plus the Project/Start date/Target date hygiene checklist for epics.

## Orchestration Flow

1.  **Phase 1: Knowledge Gathering & Retrospective**
    - Use GraphQL to fetch full iteration config (IDs, Dates) — including `completedIterations`.
    - Always use `--limit 200` on `gh project item-list` to avoid silent truncation.
    - Load the "Working Set" for the current iteration.
    - **Perform Retro**: Calculate Completion % and identify stalled items (Refer to `delivery-metrics.guide.md`).
2.  **Phase 2: Planning Sheet Generation**
    - Create `/tmp/meeting-notes/planning-sheet-YYYY-MM-DD.md`.
    - Include **Retrospective Summary** and **Capacity Warnings**.
    - Propose moves (e.g., `Todo` -> Next Iteration).
3.  **Phase 3: User Review & Edit**
    - Prompt user to edit the sheet and save.
4.  **Phase 4: Synthesis & Execution**
    - Before any `updateProjectV2Field` mutation: snapshot all item→iteration assignments.
    - Include ALL past iterations in the mutation payload (see `iteration-crud.guide.md`).
    - After mutation: re-fetch new iteration IDs, then re-assign all items.
    - Verify with `gh project item-list --limit 200` that assignments are correct.

---
**Maintained by**: contributors | **Version**: 1.3 | **Last Updated**: 2026-07-08

## Changelog
- **1.3 (2026-07-08)**: Added `roadmap-view-troubleshooting.guide.md` — empirically confirmed that
  Roadmap-layout "Epics" views require the epic issue to have at least one real GitHub sub-issue
  (via `addSubIssue`, not a text reference) to render; `issueType`, `Parent issue`, dates, and the
  saved view filter were all ruled out as gating factors. Also codified the best practice of always
  setting the correct Project membership plus `Start date`/`Target date` on epics, even though those
  dates don't gate visibility — they matter for timeline accuracy regardless.
- **1.2 (2026-04-21)**: Added lessons from live session — `--limit 200` requirement for stocktake,
  `completedIterations` must be preserved to keep `@current` views working, ID regeneration
  side-effect on every mutation, GraphQL item assignment pattern. See `iteration-crud.guide.md`.
