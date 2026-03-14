# Guide: Delivery Metrics & Retrospective Insights

This document provides the logic for calculating sprint performance and identifying carryover risks during the iteration transition.

---

## 1. Velocity & Completion Analysis
Used to evaluate the health of the completed iteration and forecast capacity for the next.

### Calculation Logic:
- **Completion %**: `(Count(Done) / Total Items) * 100`
- **Carryover %**: `(Count(Non-Done) / Total Items) * 100`
- **Velocity (Size-Based)**: `Sum(Size of Done items)` (e.g., Total 'M' points delivered).

### Retrospective Prompting:
If Completion % is < 50%, the agent MUST add a **"Velocity Alert"** to the planning sheet:
> **⚠️ Velocity Alert**: The team completed only X% of work in the last iteration. Consider reducing the load for the next sprint or identifying systemic blockers.

---

## 2. Carryover Root-Cause Analysis (RCA)
For all items being moved to the next iteration, the agent should categorize the reason for carryover based on issue history:

- **STALLED**: Blocked for > 48h by external dependency (e.g., IAM/RITM).
- **UNDERESTIMATED**: Large volume of technical discussion/comments without status change.
- **DE-PRIORITIZED**: No activity or comments during the entire iteration.

---

## 3. Capacity Forecasting (Iteration Target)
Before confirming the "Move to Next Iteration" action, the agent should perform a capacity check:

- **Command**: `gh project item-list <number> --owner <org> --format json | jq '.items[] | select(.iteration.title == "Upcoming Iteration") | .size'`
- **Validation**: If `Proposed Carryover + Existing Items > Team Average Velocity`, the agent warns:
> **📉 Capacity Warning**: Iteration X already has Y 'M' points. Moving these Z items will exceed historical velocity. Recommend prioritizing high-value carryover only.
