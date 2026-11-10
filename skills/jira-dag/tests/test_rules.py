"""Data-quality rule set (specs/data-quality-rules.md). Test names carry the scenario id (S-dq-N)."""
import copy, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import jira_timeline, po_view, rules, synth
from jira_common import EARLY, finalize

NINE = ["External blockers not ready", "Blocked by enablers not started", "Starts before its blocker ends", "Priority does not match WSJF",
        "No owner", "Not sliced", "No WSJF score", "No parent initiative", "No target dates"]


# stand-in for a rule whose empty section run() leaves out
NO_SECTION = ("", "", [], {})


def legacy_attention(I, tl):
    """Frozen copy of attention() as it was before the rule set: the oracle for S-dq-1 and S-dq-7."""
    epics = {k: v for k, v in I.items() if v["core"]}
    ws = lambda v: float(v["ws"]) if v["ws"] not in (None, "") else -1
    order = lambda ks: sorted(ks, key=lambda k: (-ws(I[k]), int(k.split("-")[-1])))
    scored = sorted(ws(v) for v in epics.values() if ws(v) >= 0)
    top = scored[int(len(scored) * 0.75)] if scored else 99
    secs = []

    def add(title, why, ks, note=None):
        secs.append((title, why, order(ks), note or {}))
    add("External blockers not ready", "Blocked by another project's issue that is still early (Funnel, Backlog, New, To Do, Analyzing).",
        [k for k, v in epics.items() if v["warn"] and any("external blocker" in w for w in v["warn"])],
        {k: next((w for w in v["warn"] if "external blocker" in w), "") for k, v in epics.items()})

    def enab(v):
        return [r for r in v["blockedBy"] if not r["ext"] and r["k"] in I and not I[r["k"]]["core"] and r["st"] in EARLY]
    add("Blocked by enablers not started", "A task in this project blocks the epic and is still early (Funnel, Backlog, New, To Do, Analyzing). These are the roots to chase.",
        [k for k, v in epics.items() if enab(v)], {k: "waiting on " + ", ".join(r["k"] + " [" + r["st"] + "]" for r in enab(v))[:110] for k, v in epics.items() if enab(v)})
    add("Starts before its blocker ends", "Planned dates overlap with a blocker. May be intended for a thin first slice; the PO decides.",
        sorted({v for _, v in tl["conflicts"]}) if tl else [],
        {v: next((w for w in I[v]["warn"] if w.startswith("starts")), "") for _, v in (tl["conflicts"] if tl else [])})
    add("Priority does not match WSJF", "WSJF is in the top quarter but Priority is Low or Lowest.",
        [k for k, v in epics.items() if ws(v) >= top and v["pr"] in ("Low", "Lowest")], {k: f"WSJF {v['ws']}, Priority {v['pr']}" for k, v in epics.items()})
    add("No owner", "No assignee.", [k for k, v in epics.items() if not v["who"]])
    add("Not sliced", "No child issues.", [k for k, v in epics.items() if not v.get("children")])
    add("No WSJF score", "Business Value, Time Criticality, Risk Reduction or Job Size missing.", [k for k, v in epics.items() if ws(v) < 0])
    add("No parent initiative", "Not under an initiative, so it is not in the plan.", [k for k, v in epics.items() if not v["par"]])
    add("No target dates", "Target start or end missing, so the epic is not on the timeline.", [k for k, v in epics.items() if not (v["start"] and v["end"])])
    return secs


def data(mutate=None):
    """Synthetic issues plus the timeline built on them (build() adds the 'starts before' warnings to I)."""
    I = synth.build()
    if mutate:
        mutate(I)
        finalize(I, synth.P)
    return I, jira_timeline.build(I, synth.BASE)


def ctx_for(tl, topology=None):
    return dict(conflicts=tl["conflicts"] if tl else [], topology=topology)


def tough(I):
    """Exercise branches the stock synthetic set leaves empty: early enabler, Low priority on a top WSJF epic, priority-less epic."""
    I["PLT-90"]["st"] = "Backlog"
    I["PLT-10"]["blockedBy"][0]["st"] = "Backlog"
    I["PLT-10"]["pr"] = "Low"
    I["PLT-12"]["who"] = ""
    I["PLT-14"]["ws"] = ""
    I["PLT-15"]["start"] = None


class Characterisation(unittest.TestCase):
    def check(self, mutate):
        I, tl = data(mutate)
        old = legacy_attention(I, tl)
        self.assertEqual(rules.run(I, ctx_for(tl)), old)
        self.assertEqual(po_view.attention(I, tl), old)
        return old

    def test_S_dq_1_nine_checks_same_as_before_on_synthetic_data(self):
        old = self.check(None)
        self.assertEqual([s[0] for s in old], NINE)
        self.assertTrue(any(s[2] for s in old))

    def test_S_dq_1_same_with_early_enablers_and_priority_mismatch(self):
        old = dict((s[0], s) for s in self.check(tough))
        self.assertTrue(old["Blocked by enablers not started"][2])
        self.assertTrue(old["Priority does not match WSJF"][2])

    def test_S_dq_7_attention_tab_is_built_from_the_rule_set(self):
        I, tl = data()
        self.assertEqual(po_view.attention(I, tl), rules.run(I, ctx_for(tl)))

    def test_S_dq_7_without_timeline_conflicts_are_empty(self):
        I, _ = data()
        self.assertEqual(po_view.attention(I, None), legacy_attention(I, None))


class RuleSet(unittest.TestCase):
    def test_S_dq_2_every_rule_has_id_title_why_fix_and_severity(self):
        for r in rules.RULES:
            for f in ("id", "title", "why", "fix"):
                self.assertTrue(getattr(r, f).strip(), (r.id, f))
            self.assertIn(r.severity, ("warn", "info"))

    def test_S_dq_2_ids_and_titles_are_unique_and_stable(self):
        ids = [r.id for r in rules.RULES]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len({r.title for r in rules.RULES}), len(rules.RULES))
        self.assertEqual(ids, ["external-blockers-not-ready", "blocked-by-enablers-not-started", "starts-before-blocker-ends", "priority-vs-wsjf",
                               "no-owner", "not-sliced", "no-wsjf", "no-parent", "no-dates", "l1-need-by-unknown", "slice-too-long"])
        self.assertEqual([r.title for r in rules.RULES[:9]], NINE)


class NoDates(unittest.TestCase):
    def flagged(self, **kw):
        I, tl = data()
        I["PLT-12"].update(kw)
        return "PLT-12" in dict((s[0], s[2]) for s in rules.run(I, ctx_for(tl)))["No target dates"]

    def test_S_dq_3_epic_without_dates_is_flagged(self):
        self.assertTrue(self.flagged(start=None, end=None))

    def test_S_dq_3_missing_start_or_end_alone_is_missing(self):
        self.assertTrue(self.flagged(start=None))
        self.assertTrue(self.flagged(end=None))
        self.assertTrue(self.flagged(start="", end=""))

    def test_S_dq_3_dated_epic_is_not_flagged(self):
        self.assertFalse(self.flagged())

    def test_S_dq_3_undated_epic_is_never_a_timeline_conflict(self):
        I, tl = data()
        I["PLT-19"]["start"] = I["PLT-19"]["end"] = None
        res = dict((s[0], s[2]) for s in rules.run(I, ctx_for(tl)))
        self.assertIn("PLT-19", res["No target dates"])
        self.assertNotIn("PLT-19", res["Starts before its blocker ends"])


class L1NeedBy(unittest.TestCase):
    def result(self, **kw):
        I, tl = data()
        I["PLT-12"].update(kw)
        return dict((s[0], s) for s in rules.run(I, ctx_for(tl))).get("L1 need-by unknown", NO_SECTION)

    def test_S_dq_4_l1_request_without_need_by_is_flagged(self):
        for missing in (None, "", "  "):
            sec = self.result(l1_requests=["REQ-1"], l1_need_by=missing)
            self.assertEqual(sec[2], ["PLT-12"])
            self.assertIn("REQ-1", sec[3]["PLT-12"])

    def test_S_dq_4_absent_need_by_field_counts_as_unknown(self):
        self.assertEqual(self.result(l1_requests=["REQ-1"])[2], ["PLT-12"])

    def test_S_dq_4_known_need_by_is_not_flagged(self):
        self.assertEqual(self.result(l1_requests=["REQ-1"], l1_need_by="2030-01-31"), NO_SECTION)

    def test_S_dq_4_epic_serving_no_l1_request_is_not_flagged(self):
        self.assertEqual(self.result(l1_requests=[], l1_need_by=None), NO_SECTION)

    def test_S_dq_4_absent_inputs_flag_nothing_and_add_no_section(self):
        I, tl = data()
        self.assertEqual(rules.RULE_BY_ID["l1-need-by-unknown"].test(I, ctx_for(tl)), ([], {}))
        self.assertEqual([s[0] for s in rules.run(I, ctx_for(tl))], NINE)

    def test_S_dq_4_unknown_need_by_is_not_ranked_as_low_urgency(self):
        # the rule only reports; it does not rewrite or default any date on the epic
        I, tl = data()
        I["PLT-12"].update(l1_requests=["REQ-1"])
        before = copy.deepcopy(I)
        rules.run(I, ctx_for(tl))
        self.assertEqual(I, before)
        self.assertNotIn("l1_need_by", I["PLT-12"])


class SliceTooLong(unittest.TestCase):
    CFG = {"art": "A", "pods": [{"id": "PLT", "projects": ["PLT"]}, {"id": "OTH", "projects": ["OTH"]}],
           "policy": {"PLT": {"slice_cap_days": 5}, "OTH": {"slice_cap_days": 30}}}

    def sec(self, days, cfg, key="PLT-12", **ctx):
        I, tl = data()
        I[key]["children_days"] = days
        return dict((s[0], s) for s in rules.run(I, dict(ctx_for(tl, cfg), **ctx))).get("Split me: slice too long", NO_SECTION)

    def test_S_dq_5_child_over_the_pod_cap_is_flagged_with_that_cap(self):
        sec = self.sec([3, 6], self.CFG)
        self.assertEqual(sec[2], ["PLT-12"])
        self.assertIn("5", sec[3]["PLT-12"])

    def test_S_dq_5_child_at_the_cap_is_fine(self):
        self.assertEqual(self.sec([5, 4], self.CFG), NO_SECTION)

    def test_S_dq_5_cap_is_per_pod(self):
        cfg = copy.deepcopy(self.CFG)
        cfg["policy"]["PLT"]["slice_cap_days"] = 30
        self.assertEqual(self.sec([20], cfg), NO_SECTION)
        self.assertNotEqual(self.sec([20], self.CFG), NO_SECTION)

    def test_S_dq_5_pod_without_policy_uses_default_cap(self):
        cfg = {"pods": [{"id": "PLT", "projects": ["PLT"]}]}
        self.assertEqual(rules.DEFAULT_SLICE_CAP_DAYS, 10)
        self.assertNotEqual(self.sec([11], cfg), NO_SECTION)
        self.assertEqual(self.sec([10], cfg), NO_SECTION)
        cfg["policy"] = {"OTH": {"slice_cap_days": 1}}
        self.assertEqual(self.sec([10], cfg), NO_SECTION)

    def test_S_dq_5_no_topology_config_uses_default_cap(self):
        self.assertNotEqual(self.sec([11], None), NO_SECTION)
        self.assertEqual(self.sec([10], None), NO_SECTION)

    def test_S_dq_5_unestimated_children_are_unknown_not_zero_and_not_flagged(self):
        self.assertEqual(self.sec([None, 4], self.CFG), NO_SECTION)
        self.assertNotEqual(self.sec([None, 9], self.CFG), NO_SECTION)

    def test_S_dq_5_absent_children_days_flags_nothing(self):
        I, tl = data()
        self.assertEqual(rules.RULE_BY_ID["slice-too-long"].test(I, ctx_for(tl)), ([], {}))

    def test_S_dq_5_ctx_policy_overrides_topology_policy(self):
        self.assertEqual(self.sec([6], self.CFG, policy={"PLT": {"slice_cap_days": 8}}), NO_SECTION)


class FailingRules(unittest.TestCase):
    def test_S_dq_6_maps_each_epic_to_its_failing_rule_ids(self):
        I, tl = data()
        res = rules.run(I, ctx_for(tl))
        f = rules.failing_rules(res)
        self.assertEqual(f["PLT-13"].count("no-owner"), 1)
        self.assertIn("no-dates", f["PLT-19"])
        self.assertIn("no-parent", f["PLT-20"])
        self.assertNotIn("PLT-10", {k for k, ids in f.items() if "no-owner" in ids})

    def test_S_dq_6_ids_follow_rule_order_and_clean_epics_are_absent(self):
        I, tl = data()
        res = rules.run(I, ctx_for(tl))
        f = rules.failing_rules(res)
        order = [r.id for r in rules.RULES]
        for ids in f.values():
            self.assertEqual(ids, sorted(ids, key=order.index))
        flagged = {k for s in res for k in s[2]}
        self.assertEqual(set(f), flagged)

    def test_S_dq_6_includes_the_new_rules(self):
        I, tl = data()
        I["PLT-12"].update(l1_requests=["REQ-1"], children_days=[30])
        f = rules.failing_rules(rules.run(I, ctx_for(tl)))
        self.assertIn("l1-need-by-unknown", f["PLT-12"])
        self.assertIn("slice-too-long", f["PLT-12"])


if __name__ == "__main__":
    unittest.main()
