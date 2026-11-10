---
name: jira-dag
description: 'One interactive Jira portfolio page for a project (dependency DAG, timeline, needs-attention list), built from live issue links and served on the local network. A local replica of the Jira Plans dependencies view, for PO and lead conversations. Read-only. Triggers on: ''dependency graph'', ''dependency DAG'', ''critical path'', ''blocks graph'', ''jira plans dependencies'', ''portfolio view'', ''po dashboard''.'
---

# Jira portfolio page

Read-only. One page, `index.html`, with six tabs, built from live Jira data. Credentials come from `~/.netrc` for the Jira host; nothing is printed.

```bash
S=~/.pi/agent/skills/jira-dag/scripts
python3 $S/po_view.py --url "$JIRA_URL" --project <PROJECT> --outdir ~/.cache/jira/<PROJECT>/dag         # the page
# options: --relates (dashed Relates links), --all (also epics with no links)
```

Outputs in `--outdir`: `index.html` (open this), `epics.svg` and `timeline.svg` (standalone, Jira links, no popups), `epics.mmd` (source). `epics.html` and `timeline.html` redirect to the tabs. `jira_dag.py` and `jira_timeline.py` still run alone for one view.

## Tabs
- **Pressure** (default tab, flow view for Kanban-style work). Built from the whole open blocking graph, all issue types, not only epics. (1) *What blocks the most*: open issues ranked by how many others sit behind them (transitive within the project plus direct dependants in other projects), with owner, status and days in state, earliest need-by date downstream, and flags: no owner, due soon or overdue, idle (early status for 14+ days), stalled (in progress 21+ days). (2) *Work in flight by team*: in-flight and queue counts per team, with an editable limit per team (kept in the browser) that flags a team over its limit. (3) *Chase list*: flagged blockers grouped by owner (unowned first), then other projects' items that hold up ours, with Copy as Markdown. In-flight counts only cover what exists in Jira at that level. Downstream counts do not follow links past one hop into other projects.
- **Briefing.** Pick another project (a consumer that waits on us, or a provider we wait on) and get a one-page brief for that team: *what you can rely on from us* (their items that our outcomes block: needed-by date, our forecast, confidence, fit: on time / late by N wk / unknown) and *what we need from you* (their items that block ours, with the date we need them by). Copy as Markdown or print to PDF. Deep link: `#tab=brief&for=<PROJECT>`. Their dates are whatever Jira records; an unacknowledged dependency is only a claim.
- **Roadmap.** For stakeholders: outcomes grouped by initiative on a month axis, one bar each, coloured by confidence, with a dashed ghost bar where the forecast is later than the plan, a purple diamond for a commitment date, and the initiative due date as a dashed line. "Stakeholder view" hides keys and people. Click a row for a what-if drawer. Confidence is derived, never stored: **Committed** (owner, dates, initiative, a Due date set, and Ready or Implementing, with no flags), **At risk** (flagged, waits on something not started or undated, forecast later than plan, or passes its commitment or the initiative due date), **Likely** (planned and owned, no flags, no commitment date), **Not yet planned** (no owner, dates or initiative). The forecast is a forward pass over blockers: an epic cannot start before its blockers end and keeps its planned duration. This is a simple model, not a prediction.
- **Dependencies.** Epics plus one hop of linked issues. Mermaid DAG, `mmdc` needed (`npx puppeteer browsers install chrome-headless-shell`).
- **Timeline.** Bars from Target start to Target end, grouped by parent initiative, due-date markers, a today line, rose arrows where a blocker ends after the blocked epic starts. Planned dates, not forecasts. Epics without dates are listed, not drawn.
- **Topologies.** Team Topologies view of the ART, driven by a config blob (`--topology FILE`, default `~/.config/jira-dag/topology.{yaml,json}`; no config means no tab). The config maps PODs, an interface project and products to Jira projects; anything not listed is external. Bands: *On the platform* (products, placeholder until data exists) · *interface* (product requests, spans all PODs) · *In the platform* (a lane per POD, dotted borders, waits-on-another-POD epics on the left of each lane) · *External* (outgoing, under the ART; external incoming sits in a left gutter). Only epics on a cross-boundary link are drawn; same-POD links are counted per lane. Config shape: `art`, `pods:[{id,projects}]`, `interface:{name,projects}`, `products:[{id,projects}]`. Epics of every configured POD are fetched in one extra query. Direction is Jira "blocks".
- **Needs attention.** Epics grouped by what a PO would act on: external blockers not ready, blocked by enablers not started, starts before blocker ends, priority vs WSJF mismatch, no owner, not sliced, no WSJF, no parent, no dates. Each row opens the card.

## Using the page
- Click a box or a row: card with status, priority, WSJF, assignee, team, children, target dates, warnings, blocked-by and blocks (external ones flagged) and a link to Jira. ⌘/ctrl-click on a box opens Jira directly.
- Hover a box: traces its upstream and downstream chain.
- **Consumer / Provider / Label** dropdowns narrow every tab. Consumer = an external project with issues that wait on one of our epics. Provider = an external project whose issues block ours. Label = an epic label (for example the PI or area labels). Choices carry counts and the project's Jira name.
- Filter box (`/` focuses it) and status buttons dim non-matching epics; "external only" keeps epics that cross a project boundary.
- The address bar carries the state: `#tab=timeline&k=KEY` opens that tab with that card. Copy it into a message and the reader lands on the same view.
- Zoom with − / fit / +.

## Reading it
- **Orange** = crosses a project boundary: a ring on epics that depend on, or block, another Jira project (`◀ EXTERNAL IN`, `EXTERNAL OUT ▶`, both); a dashed orange box for the other project's issue; orange edges. It wins over every other colour.
- **★ and thick pink edges** = critical path (longest blocking chain in view). Dotted grey box = not an epic of this view, such as a task that blocks an epic.
- Status colours: green implementing, yellow analyzing, blue-grey backlog, grey funnel.
- `blocks N` counts only what the picture shows (one hop of neighbours), so it understates the full downstream count.
- Closed issues (Done, Discarded, Closed, Cancelled, Resolved) are dropped. A blank WSJF is treated as missing.
- Warnings are questions for the PO, not errors. An early start can be a deliberate thin first slice.

## What-if and synthetic data
- The drawer lets you slip an epic's end, set or clear a commitment date, toggle owner and impediment, all in the browser (kept in localStorage). The forecast and counts recompute at once. A bar lists the local changes; Export gives a Markdown table and JSON of **proposed** Jira edits. The page never writes to Jira and holds no credentials.
- `po_view.py --synthetic --outdir <dir>` builds the page from built-in fake data (generic names, dates relative to today) and makes no Jira call at all. Use it to try the page and to demo it.
- Assumptions to confirm with the RTE before trusting the Roadmap on real data: Due date as the commitment marker (it is already used as a needed-by date on some tasks), and the confidence rules above.

Never write Jira content into a repository. Keep outputs under `~/.cache/jira/<PROJECT>/dag/`. The page is a snapshot, not a validated record.
