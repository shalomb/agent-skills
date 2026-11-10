# Filters and view state (Topologies first)

Anchors: P6, P8, P9, D6, D8, D9. Phase 1 scope: Topologies tab only. Applying to every tab and folding Dependencies in come later.

State (D9): one object `{filters, pins, depth}`; hover is transient and not stored. The URL hash is that state written down.
Filters: `labels` (set of selected labels), `components` (set), `status` (set), `rel` (set of: incoming, external, blocking),
`dates` ({from,to,undated}). Pure logic lives in a DOM-free JS module (`scripts/viewstate.js`, embedded into the page by Python)
and is tested with `node --test` (no browser). The browser only renders what the logic returns.

Pure logic (node tests, no DOM):
- **S-flt-1** *(D6)* Given labels grouped by prefix, when I select two labels in the same group, then an epic matches if it has either; when I also select a label in another group, then it must match both groups (OR within a group, AND between).
- **S-flt-2** *(D6)* Given components selected, then an epic matches if it has any selected component; given none selected, components do not filter.
- **S-flt-3** *(D6)* Given relationship toggles, then `incoming` matches epics that wait on another POD or outside the ART, `external` matches epics with a link leaving the ART, `blocking` matches epics that block another POD; several toggles are OR'd with each other and AND'd with labels.
- **S-flt-4** *(D6, P8)* Given a date range, then an epic matches if its target start to end overlaps it; an epic with no dates matches only when `undated` is on (default on). Unknown is never treated as a date.
- **S-flt-5** *(D6, P6)* Given a filter and a pinned epic, then the pinned epic and its neighbours are shown even when the filter would hide them (pins override).
- **S-flt-6** *(P6)* Given filtered-in epics, then their linked neighbours that fail the filter are returned as `ghost`, so no link vanishes silently; epics unrelated to any match are `hidden`.
- **S-flt-7** *(D9)* Given a state, then `toHash` and `fromHash` round-trip it exactly (including empty state, commas and `%2C` in values), and unknown hash keys are ignored.
- **S-flt-8** *(P6)* Given no filters and no pins, then every epic is `shown` and nothing is ghosted.
- **S-flt-9** *(D6)* Given the data, then a facet function returns label groups (prefix title, values, counts) and a components list that is empty when no epic has components.

Browser (a few scenarios, synthetic data, headless Chrome):
- **S-ui-1** *(P9)* Given the page, then the filter controls are in a drawer opened by a single "Filters (n)" button; with the drawer closed the diagram starts higher on the page than before (the filter bar no longer sits above it).
- **S-ui-2** *(D6, P6)* Given an applied filter, then non-matching epics are removed from Topologies and the layout closes up, ghosts are drawn faded, and a chip row shows each active filter with a ✕ and "n of m shown".
- **S-ui-3** *(D9)* Given a filter, then reloading the URL restores the same view; clearing all chips returns the unfiltered layout exactly (as S-pin-8).
- **S-ui-4** *(D6)* Given components are empty, then the Components control is present but disabled with a hint, not hidden.
- **S-ui-5** *(P6)* Given a filter and a pin, then unpinning returns to the filtered view, not the unfiltered one.
