---
name: iteration-planner
description: Orchestrate the transition between GitHub Project iterations (e.g., oneTakeda/293). Perform a "Sprint Stocktake" of open work and coordinate with the user to schedule the next 2-week iteration.
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

## Orchestration Flow

1.  **Phase 1: Knowledge Gathering & Retrospective**
    - Use GraphQL to fetch full iteration config (IDs, Dates).
    - Load the "Working Set" for the current iteration.
    - **Perform Retro**: Calculate Completion % and identify stalled items (Refer to `delivery-metrics.guide.md`).
2.  **Phase 2: Planning Sheet Generation**
    - Create `/tmp/meeting-notes/planning-sheet-YYYY-MM-DD.md`.
    - Include **Retrospective Summary** and **Capacity Warnings**.
    - Propose moves (e.g., `Todo` -> Next Iteration).
3.  **Phase 3: User Review & Edit**
    - Prompt user to edit the sheet and save.
4.  **Phase 4: Synthesis & Execution**
    - Parse edited sheet and execute `gh project item-edit` calls.

---
**Maintained by**: @shalomb | **Version**: 1.1 | **Last Updated**: 2026-03-14
