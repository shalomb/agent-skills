---
name: daily-standup
description: Orchestrate GitHub Project updates (e.g., oneTakeda/293) using meeting transcripts (VTT). Map discussion points, decisions, and blockers from the meeting-notes skill directly to active WIP items on the project board.
---

# Daily Standup Skill

Automate the bridge between synchronous engineering discussions and asynchronous project tracking. This skill processes meeting transcripts to "close the loop" on technical decisions, status changes, and blockers directly in GitHub Projects.

## Purpose

Convert the output of engineering meetings (standups, design reviews, retrospectives) into structured updates for active GitHub Project items:
- **Status Updates**: Automatically move cards (e.g., "In Progress" -> "Done") based on verbal confirmation.
- **Technical Feedback**: Post "Material Decision Rationale" as comments on specific GitHub Issues.
- **Blocker Escalation**: Flag project items as "Blocked" when new dependencies are identified in the transcript.
- **Proactive Intervention**: Identify stagnant items and validate that proposed resolution options are sufficient.

## Capabilities

1. **Project Context Retrieval**: Pull all items, statuses, and linked issue summaries from a GitHub Project (e.g., `oneTakeda/293`).
2. **Transcript Mapping (Semantic Join)**: Use the `meeting-notes` skill to parse the VTT, then map segments of discussion to specific Project Items.
3. **Automated Status Proposals**: Identify phrases like "We've finished X" or "X is ready for PR" to suggest status changes using the **Bias for Action** template.
4. **Stall Detection & Option Validation**: Analyze issue history to detect stagnation (2+ days) and verify that today's proposed options haven't already failed in the past.
5. **Issue Commenting**: Summarize technical deep-dives into a "Meeting Summary" comment, preserving the "Why" behind code changes.
6. **Blocker Detection**: Link mentions of "waiting for X" or "RITM ticket Y" to specific project cards as blockers.

## Input

**Required**:
- VTT (WebVTT) transcript file path or content. Supports **Smart File Discovery**:
  - Accepts glob patterns (e.g., `~/Downloads/DAD*vtt`).
  - **Recency Filtering**: Automatically selects the most recent file matching the pattern that was modified within the last 24 hours.
  - **Command Guide**:
    ```bash
    # Find the most recent VTT file modified in the last 24 hours
    (cd /home/unop/Downloads && find . -maxdepth 1 -name "DAD*vtt" -mmin -1440 -printf "%T@ %p\n" | sort -n | tail -1 | cut -f2- -d" ")
    ```
- GitHub Project Number (e.g., 293) and Owner (e.g., oneTakeda). Supports **Auto-Discovery**:
  - If launched within a repository, the skill automatically identifies linked GitHub Projects (via GraphQL).
  - Infers the default project if only one is linked (e.g., `oneTakeda/293`).

**Optional**:
- Filter (e.g., "Only update items in Iteration 4").
- Custom status mapping.

## Output

**Primary**: A "Plan of Updates" and "Lead Briefing" presented for user confirmation:
- List of status changes (Old -> New).
- List of proposed action-oriented comments.
- **Lead Briefing**: High-impact interventions required (Stalled items, Reality gaps).

**Secondary**: Execution of confirmed changes via `gh project` and `gh issue`.

## Project Attribution & Context Logic

### 1. Repository-Based Attribution (Primary)
```bash
gh api graphql -f query='
  query($owner:String!, $name:String!) {
    repository(owner: $owner, name: $name) {
      projectsV2(first: 5) {
        nodes {
          number, title, url
        }
      }
    }
  }
' -f owner="<org>" -f name="<repo>"
```

### 2. Current Iteration Inference (The "Working Set")
The skill narrows the focus to the **Current Iteration** (Iteration 4) based on today's date:
```bash
gh project item-list <number> --owner <org> --format json | jq '.items[] | select(.iteration.title == "Iteration X") | {id, title, status, assignees, issue_number: .content.number, repo: .content.repository}'
```

## The "Bias for Action" Status Standard

To avoid "Blocker Fatigue," all status updates must follow the fixed structure in `references/status-update.template.md`.

### 1. Stall Detection (The "2-Day Rule")
The skill flags items as **"Stalled"** if they have been `Blocked` or `Impeded` for **2+ consecutive days** without new options being explored.
- **Check History**: `gh issue view <number> --json comments,updatedAt`

### 2. Option Validation
The skill cross-references today's "Options Explored" against the **Issue History** to prevent "Cyclic Resolution Errors" (proposing something that already failed).

## Orchestration Flow

1.  **Phase 1: Knowledge Gathering & Project Attribution**
    - Step A: Check Repository-linked projects.
    - Step B: Infer Current Iteration and load the "Working Set."
2.  **Phase 2: Transcript Discovery & Analysis**
    - Step A: Find the most recent VTT (Robust `find` command).
    - Step B: Call `meeting-notes` skill to parse the VTT.
3.  **Phase 3: Cross-Referencing & Deep History Pull**
    - Map (Topic) -> (Project Item).
    - For Impeded/Blocked matches: Pull last 5 issue comments for history analysis.
4.  **Phase 4: Option Validation & Stall Analysis**
    - Compare today's options against history; check for 2-day stagnation.
5.  **Phase 5: Proposal Generation (Bias for Action)**
    - Generate updates using the mandatory template.
    - Include **[INTERVENTION RECOMMENDED]** for stalled items.
6.  **Phase 6: User Validation & Execution**
    - Display "Update Plan" and "Lead Briefing" then execute confirmed changes.

## System Integration
- `meeting-notes`: For VTT parsing.
- `github-cli`: For Project/Issue management.

---
**Maintained by**: @shalomb | **Version**: 1.1 | **Last Updated**: 2026-03-14
