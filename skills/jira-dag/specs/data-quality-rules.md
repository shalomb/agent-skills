# Data-quality rules

Anchors: P7, P8, D7. Pure Python. Today these live in `attention()` in `scripts/po_view.py`; they become a rule set.

A rule has: `id`, `title`, `why`, `fix` (hint), `severity`, and a test that returns the epic keys it flags. Rules take the
issues and the topology config (for per-POD policy).

- **S-dq-1** *(P7)* Given the issues, when rules run, then each rule returns the epics it flags plus a per-epic note, and the existing nine checks (external blockers not ready, blocked by enablers not started, starts before blocker ends, priority vs WSJF, no owner, not sliced, no WSJF, no parent, no target dates) give the same results as today.
- **S-dq-2** *(P7)* Given the rule set, then every rule has an id, title, why and fix hint, and ids are unique and stable.
- **S-dq-3** *(P8)* Given an epic with no target dates, then it is flagged "no dates" and is never treated as ending today or never.
- **S-dq-4** *(P8)* Given an L2 epic whose L1 request has no need-by date, then it is flagged "L1 need-by unknown", not scored as low urgency.
- **S-dq-5** *(P7, D7)* Given a POD policy with a slice cap in days, when an epic has child issues over that cap, then it is flagged "split me" using that POD's cap; a POD with no policy uses a default.
- **S-dq-6** *(P7)* Given the rule set, then a helper returns, per epic, the list of failing rule ids (for badges and filters).
- **S-dq-7** *(P7)* Given the page, then the Needs-attention tab output is built from the rule set and is unchanged in content for the same data.
