"""Data-quality rule set for the Needs-attention tab (pure Python, no Jira calls). See specs/data-quality-rules.md.

A Rule has a stable `id`, `title`, `why`, `fix` (hint), `severity` ('warn' | 'info') and `test(I, ctx) -> (keys, notes)`.
I is the issues dict used by po_view (see jira_common.ISSUE_FIELDS). ctx is a dict:
  conflicts: [(blocker, blocked)] timeline conflicts (from jira_timeline.build), default []
  topology:  topology config dict or None; cfg["policy"][pod_id]["slice_cap_days"] is the slice cap for that POD
  policy:    optional per-POD overrides in the same shape as cfg["policy"]
Unknown is not zero: a missing value is a finding or is skipped, never defaulted to a low score or a date.
"""
from dataclasses import dataclass
from typing import Callable
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topology
from jira_common import EARLY

DEFAULT_SLICE_CAP_DAYS = 10


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    why: str
    fix: str
    severity: str
    test: Callable
    always_listed: bool = True  # the section appears even when nothing is flagged


def _epics(I):
    return {k: v for k, v in I.items() if v["core"]}


def _ws(v):
    return float(v["ws"]) if v["ws"] not in (None, "") else -1


def _blank(x):
    return x is None or (isinstance(x, str) and not x.strip())


def _external_blockers_not_ready(I, ctx):
    epics = _epics(I)
    ks = [k for k, v in epics.items() if v["warn"] and any("external blocker" in w for w in v["warn"])]
    return ks, {k: next((w for w in v["warn"] if "external blocker" in w), "") for k, v in epics.items()}


def _early_enablers(I, v):
    return [r for r in v["blockedBy"] if not r["ext"] and r["k"] in I and not I[r["k"]]["core"] and r["st"] in EARLY]


def _blocked_by_enablers(I, ctx):
    epics = _epics(I)
    return ([k for k, v in epics.items() if _early_enablers(I, v)],
            {k: "waiting on " + ", ".join(r["k"] + " [" + r["st"] + "]" for r in _early_enablers(I, v))[:110] for k, v in epics.items() if _early_enablers(I, v)})


def _starts_before_blocker(I, ctx):
    conflicts = ctx.get("conflicts") or []
    return sorted({v for _, v in conflicts}), {v: next((w for w in I[v]["warn"] if w.startswith("starts")), "") for _, v in conflicts}


def _priority_vs_wsjf(I, ctx):
    epics = _epics(I)
    scored = sorted(_ws(v) for v in epics.values() if _ws(v) >= 0)
    top = scored[int(len(scored) * 0.75)] if scored else 99
    return ([k for k, v in epics.items() if _ws(v) >= top and v["pr"] in ("Low", "Lowest")],
            {k: f"WSJF {v['ws']}, Priority {v['pr']}" for k, v in epics.items()})


def _no_owner(I, ctx):
    return [k for k, v in _epics(I).items() if not v["who"]], {}


def _not_sliced(I, ctx):
    return [k for k, v in _epics(I).items() if not v.get("children")], {}


def _no_wsjf(I, ctx):
    return [k for k, v in _epics(I).items() if _ws(v) < 0], {}


def _no_parent(I, ctx):
    return [k for k, v in _epics(I).items() if not v["par"]], {}


def _no_dates(I, ctx):
    return [k for k, v in _epics(I).items() if not (v["start"] and v["end"])], {}


def _l1_need_by_unknown(I, ctx):
    """Epics that serve an L1 request while `l1_need_by` is missing. Both fields are optional: absent means nothing to say."""
    ks, notes = [], {}
    for k, v in _epics(I).items():
        reqs = v.get("l1_requests") or []
        if reqs and _blank(v.get("l1_need_by")):
            ks.append(k)
            notes[k] = "serves " + ", ".join(reqs)[:90] + ", no need-by date"
    return ks, notes


def slice_cap_days(key, ctx):
    """Slice cap in days for the POD that owns `key`: ctx policy, then topology policy, then the default."""
    cfg = ctx.get("topology")
    pod = topology.classify(key, cfg)[1] if cfg else None
    for policy in (ctx.get("policy"), (cfg or {}).get("policy")):
        cap = ((policy or {}).get(pod) or {}).get("slice_cap_days")
        if cap is not None:
            return cap
    return DEFAULT_SLICE_CAP_DAYS


def _slice_too_long(I, ctx):
    """Epics with a child estimate over the cap. `children_days` is optional; an unestimated child (None) is unknown, not zero."""
    ks, notes = [], {}
    for k, v in _epics(I).items():
        days = [d for d in v.get("children_days") or [] if d is not None]
        cap = slice_cap_days(k, ctx)
        if days and max(days) > cap:
            ks.append(k)
            notes[k] = f"longest child {max(days):g} days, cap {cap:g}"
    return ks, notes


RULES = [
    Rule("external-blockers-not-ready", "External blockers not ready",
         "Blocked by another project's issue that is still early (Funnel, Backlog, New, To Do, Analyzing).",
         "Chase the owning team, or re-plan the epic around the external date.", "warn", _external_blockers_not_ready),
    Rule("blocked-by-enablers-not-started", "Blocked by enablers not started",
         "A task in this project blocks the epic and is still early (Funnel, Backlog, New, To Do, Analyzing). These are the roots to chase.",
         "Start or schedule the blocking enabler, or drop the link if it no longer blocks.", "warn", _blocked_by_enablers),
    Rule("starts-before-blocker-ends", "Starts before its blocker ends",
         "Planned dates overlap with a blocker. May be intended for a thin first slice; the PO decides.",
         "Move the dates, or slice the blocker so a first part lands before the start.", "warn", _starts_before_blocker),
    Rule("priority-vs-wsjf", "Priority does not match WSJF", "WSJF is in the top quarter but Priority is Low or Lowest.",
         "Raise the Priority, or re-check the WSJF inputs.", "warn", _priority_vs_wsjf),
    Rule("no-owner", "No owner", "No assignee.", "Assign an owner.", "warn", _no_owner),
    Rule("not-sliced", "Not sliced", "No child issues.", "Break the epic into releasable slices.", "warn", _not_sliced),
    Rule("no-wsjf", "No WSJF score", "Business Value, Time Criticality, Risk Reduction or Job Size missing.",
         "Fill in the four WSJF inputs.", "warn", _no_wsjf),
    Rule("no-parent", "No parent initiative", "Not under an initiative, so it is not in the plan.",
         "Link the epic to its initiative.", "warn", _no_parent),
    Rule("no-dates", "No target dates", "Target start or end missing, so the epic is not on the timeline.",
         "Set target start and end.", "warn", _no_dates),
    Rule("l1-need-by-unknown", "L1 need-by unknown",
         "The epic serves an L1 request that has no need-by date, so its urgency is unknown (not low).",
         "Ask the requesting product for a need-by date and record it.", "info", _l1_need_by_unknown, always_listed=False),
    Rule("slice-too-long", "Split me: slice too long",
         "A child issue is estimated longer than the slice cap for this POD (policy.slice_cap_days, default %d days)." % DEFAULT_SLICE_CAP_DAYS,
         "Split the child into slices that fit the cap, each releasable on its own.", "warn", _slice_too_long, always_listed=False),
]
RULE_BY_ID = {r.id: r for r in RULES}


def run(I, ctx=None):
    """Run every rule. Returns [(title, why, ordered_keys, notes)], the shape attention_html consumes.
    Keys are ordered by WSJF (highest first, unscored last) then issue number."""
    ctx = ctx or {}
    order = lambda ks: sorted(ks, key=lambda k: (-_ws(I[k]), int(k.split("-")[-1])))
    out = []
    for r in RULES:
        ks, notes = r.test(I, ctx)
        if ks or r.always_listed:
            out.append((r.title, r.why, order(ks), notes or {}))
    return out


def failing_rules(results):
    """{epic key: [rule ids]} from run() output, in rule order. Epics that pass every rule are absent."""
    by_title = {r.title: r.id for r in RULES}
    out = {}
    for title, _, ks, _ in results:
        for k in ks:
            out.setdefault(k, []).append(by_title[title])
    return out
