# Plan overlay

Anchors: P1, P5, D3, D4, D10. Pure Python, no Jira calls. A plan is a list of operations applied to a snapshot of issues.
Nothing here writes to Jira.

Slice fields (D10): id, epic, title, kind (enabler|deliverable), mode (manual|scripted|self-service|automated), days,
value_share (0..1), unblocks (keys), releasable (bool), learn (text), debt ({creates, repaid_by}).

Operations: `add_slice`, `defer_epic`, `set_dates` (epic start/end), `add_link` / `remove_link` (blocks).

- **S-plan-1** *(P1)* Given a snapshot and a plan, when I apply it, then I get a new set of issues and the snapshot is unchanged.
- **S-plan-2** *(D3, D10)* Given `add_slice`, then the slice appears as an issue under its epic with a temporary id, its fields, and `blocks` edges for `unblocks`.
- **S-plan-3** *(P5, D7)* Given a slice whose days exceed the POD cap, then validation reports "split me" for that slice; at or under the cap it passes.
- **S-plan-4** *(P5)* Given a slice with `mode: manual` and a `debt`, then validation requires a `repaid_by` slice that exists in the plan, else it reports unrepaid debt.
- **S-plan-5** *(D10)* Given the slices of one epic, then value shares must total at most 1.0, else validation reports it.
- **S-plan-6** *(P5)* Given an epic with slices, then the plan reports "time to first releasable slice" in days along the dependency order.
- **S-plan-7** *(D4)* Given two plans on the same snapshot, then a diff lists slices added, removed or changed, and links or dates moved.
- **S-plan-8** *(D4)* Given a plan and a refreshed snapshot where an epic the plan touches is now closed or gone, then applying reports a conflict naming it and still applies the rest.
- **S-plan-9** *(D4)* Given a plan, then it round-trips to and from a plain YAML or JSON file with stable ordering (so a git diff is readable).
- **S-plan-10** *(P1)* Given an applied plan, then no function in the module performs network access or imports a Jira client.
