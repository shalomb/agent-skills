# Jira Epic Description Template

Use for PI-level epics that have corresponding GitHub issues and TargetProcess entities.

## Structure

```
*GitHub Epic:* https://github.com/ORG/REPO/issues/NNN
*TP Objective:* https://takedamain.tpondemand.com/entity/XXXXXXX
*TP Feature:* https://takedamain.tpondemand.com/entity/XXXXXXX
*Epic file:* https://github.com/ORG/control-tower/blob/main/program-increments/PI-X-XX/DAD-XXXX-*.md
*Carry-over from:* [PROJ-XXXX|https://...] (PI-X/XX)   ← omit if not a carry-over

----

h2. Problem Statement

Why this work exists. Focus on the problem, not the solution. Include quantified
impact where known (e.g. "$75K+ licensing exposure", "$604K/year addressable spend").

h2. Acceptance Criteria

* Testable, unambiguous outcome
* Written as "done when..." statements

h2. Sprint Breakdown

||Story/Task||Size||Sprint||Constraint||
|Task name|S/M/L|1|Constraint or —|

h2. Dependencies

||Type||Ref||Status||Notes||
|depends-on|[PROJ-XXX\|https://...]|unacknowledged|What we need from them|
|incoming|[PROJ-XXX\|https://...]|blocked|Who is waiting on us and why|

h2. Risks

||ID||Severity||Description||ROAM||Mitigation||
|R1|High|Description of risk|O/R/A/M|Mitigation action|

h2. Notes

Deferred decisions, constraints, carry-over context, architectural notes.
```

## Rules

- **Cross-system links always first** — before any section heading. This is how
  other teams navigate between Jira ↔ GitHub ↔ TargetProcess.
- **Dependencies table must include both directions** — outgoing (`depends-on`) AND
  incoming (`incoming` = another team/epic waiting on this one). Incoming deps are
  often forgotten and cause surprise blockers at PI review.
- **Sprint Breakdown replaces decomposition prose** — use a table, not bullet lists.
  Include the constraint column — it surfaces sequencing dependencies clearly.
- **ROAM column in Risks** — O=Own, R=Resolve, A=Accept, M=Mitigate.
- **Wiki markup not Markdown** — see `commands.md` Gotchas section for the full
  translation table.
