---
name: daily-standup
description: >
  Turn a Teams meeting transcript or minutes into a plan for the day — map
  discussion to GitHub issues, record decisions, detect stalls, update issues,
  and set reminders. Use after a standup or team call when you have a transcript
  to act on. For reporting your own recent activity with no meeting involved,
  use `daily-status` instead. Triggers on: 'daily standup', 'standup',
  'process the standup', 'meeting transcript', 'what came out of the call'.
---

# Daily Standup Skill

Automate the bridge between synchronized engineering discussions and asynchronous project tracking.

## Scope

Transcript in, plan and updates out. Related skills:

- `meeting-notes` — general transcript → minutes extraction. This skill calls it.
- `daily-status` — your own activity from git/gh/Jira, no transcript.
- `iteration-planner` — sprint boundaries, not the daily cycle.

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

## Phase 0: Locate the transcript

Look for a Teams transcript among the newest files in `~/Downloads`:

```bash
find ~/Downloads -maxdepth 1 -type f \
  \( -iname '*.vtt' -o -iname '*.srt' -o -iname '*transcript*' -o -iname '*recap*' \) \
  -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -5
```

Decide as follows:

- **A recent transcript is found** (within ~24h): state the filename and its
  timestamp, and confirm it is the right meeting before proceeding.
- **Nothing matches, or the newest match is stale**: do not guess and do not
  scan the wider filesystem. Ask the user for the transcript location, and say
  what you looked for. Accept a path, a paste of the transcript text, or a
  Teams chat name to pull via the `teams-headless` skill (`--recap`).

Never proceed on an unconfirmed file. Acting on the wrong meeting means writing
wrong decisions into real issues.

## Orchestration Flow

1.  **Phase 1: Knowledge Gathering**
    - Identify Project, Iteration, and Working Set.
    - Load the transcript confirmed in Phase 0.
2.  **Phase 2: Deep Analysis**
    - Call `meeting-notes` skill to parse transcript.
    - Fetch issue history for all matches to detect stalls.
    - Perform **Reality Checks** (Refer to `intervention-logic.md`).
3.  **Phase 3: Proposal Generation**
    - Apply the **Bias for Action** template to each update.
    - Generate **Lead Briefing** with priority escalations.
    - Assemble the day's plan (see Outputs below).
4.  **Phase 4: User Validation & Execution**
    - Display Plan and Briefing; execute confirmed updates via `gh`.

## Outputs

Produce all four, in this order:

1.  **The day's plan** — what the user should do today, ordered by priority,
    derived from actions assigned to them plus anything the Reality Check
    flagged as a gap.
2.  **Decisions** — material decisions reached in the meeting, each with the
    issue or PR it belongs to. Post as issue comments using the
    `status-update.template.md` format.
3.  **Issue updates** — status moves, comments, new issues for unowned action
    items. Proposed first, executed only after confirmation.
4.  **Reminders** — time-bound commitments made in the meeting ("I'll check
    with Priya by Thursday"). Write to the user's usual capture point: append
    to the Obsidian vault via `obsidian-notetaker`, or `~/projects/dailies/`
    if the vault is unavailable. Ask once which, then keep to it.

## Execution Safety

Issue comments and status changes are visible to your team and are hard to
retract. Therefore:

- Show every proposed write — target, action, exact body — before executing.
- Batch the confirmation: one list, one approval, then execute.
- Never invent an action item, owner, or decision that is not in the transcript.
  If attribution is ambiguous, mark it `[owner unclear]` and ask.
- A **Reality Gap** is reported, never silently corrected.

---
**Maintained by**: contributors | **Version**: 1.2 | **Last Updated**: 2026-03-14
