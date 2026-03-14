# Guide: Daily Standup Interventions

This document provides the logic for proactive stall detection, reality checking, and stakeholder intervention during the daily standup.

---

## 1. Stall Detection Rules (The "2-Day Rule")
The agent monitors issues for lack of progress using the following logic:

- **Trigger**: Item has been in `Blocked` or `In progress` for **2+ consecutive days** with no changes to the "Options Explored" or "Proposed Path."
- **Analysis**: Check issue comments via `gh issue view`. If the same root cause is repeated without resolution, flag as **STALLED**.
- **Reporting**: Include a `[STALLED]` tag in the Lead Briefing.

---

## 2. Reality Check Patterns
Cross-reference verbal claims in the transcript against the actual system state:

- **Claim**: "The PR is merged." → **Check**: Verify PR state via `gh pr view`.
- **Claim**: "The TST deployment is done." → **Check**: Verify last TFC run or GitHub Action status.
- **Claim**: "I opened an issue." → **Check**: Verify issue existence in the repository.

If a discrepancy is found, the agent MUST flag it as a **"Reality Gap."**

---

## 3. Stakeholder Interventions
Proposed actions for the Engineering Lead to unblock the team:

- **Escalation**: Draft an email/Slack to the owner of a blocking RITM or dependency.
- **Review Push**: Alert the Lead to pending PRs that are blocking offshore team progress.
- **Policy Alignment**: Flag when a technical decision made in the meeting contradicts existing repository patterns or GxP requirements.
