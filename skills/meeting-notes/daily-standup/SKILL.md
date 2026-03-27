---
name: daily-standup
description: Orchestrate GitHub Project updates using meeting transcripts. Map discussion points to WIP items, detect stalls, and generate action-oriented status updates.
---

# Daily Standup Skill

Automate the bridge between synchronized engineering discussions and asynchronous project tracking.

## Purpose

- **Status Updates**: Move cards and post technical rationale to GitHub issues.
- **Bias for Action**: Enforce an options-based resolution format for blockers.
- **Proactive Intervention**: Detect stalled items and flag "Reality Gaps" between claims and system state.

## Capabilities

1. **Context Discovery**: Auto-infer Project and current Iteration.
2. **Semantic Mapping**: Link transcript discussion points to specific GitHub issues.
3. **Stall Detection**: Flag items blocked for 2+ days without progress.
4. **Lead Briefing**: Prioritize critical path unblocking for the Engineering Lead.

## Technical Guides

- `references/status-update.template.md`: Mandatory action-oriented comment format.
- `references/intervention-logic.md`: Rules for stall detection and reality checking.

## Orchestration Flow

1.  **Phase 1: Knowledge Gathering**
    - Identify Project, Iteration, and Working Set.
    - Discover the most recent VTT file in `~/Downloads`.
2.  **Phase 2: Deep Analysis**
    - Call `meeting-notes` skill to parse transcript.
    - Fetch issue history for all matches to detect stalls.
    - Perform **Reality Checks** (Refer to `intervention-logic.md`).
3.  **Phase 3: Proposal Generation**
    - Apply the **Bias for Action** template to each update.
    - Generate **Lead Briefing** with priority escalations.
4.  **Phase 4: User Validation & Execution**
    - Display Plan and Briefing; execute confirmed updates via `gh`.

---
**Maintained by**: contributors | **Version**: 1.2 | **Last Updated**: 2026-03-14
