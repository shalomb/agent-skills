"""Plan overlay model. Each test names the scenario it covers (specs/plan-overlay.md)."""
import ast, copy, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import plan as P

CFG = {"pods": [{"id": "DSO", "projects": ["DSO"]}, {"id": "DPE", "projects": ["DPE"]}],
       "policy": {"DSO": {"slice_cap_days": 5}}}


def epic(k, st="Backlog", start=None, end=None):
    return dict(key=k, sum=k, st=st, pr="", ws=None, who="", team="", par="", start=start, end=end, url="", core=True,
                blocks=[], blockedBy=[], relates=[], labels=[])


def snapshot():
    return {k: epic(k) for k in ("DSO-1", "DSO-2", "DPE-3")} | {"DSO-9": epic("DSO-9", st="Done")}


def sl(id, epic_key="DSO-1", **kw):
    d = dict(id=id, epic=epic_key, title=f"slice {id}", kind="deliverable", mode="automated", days=3, value_share=0.25,
             unblocks=[], releasable=True, learn="", debt=None)
    d.update(kw)
    return d


def add(s):
    return {"op": "add_slice", "slice": s}


def mkplan(*ops):
    return {"name": "p", "base": {"project": "DSO", "fetched": "2025-01-01"}, "ops": list(ops)}


class Apply(unittest.TestCase):
    def test_S_plan_1_input_is_not_mutated(self):
        snap = snapshot()
        before = copy.deepcopy(snap)
        plan = mkplan(add(sl("S-1", unblocks=["DPE-3"])), {"op": "set_dates", "epic": "DSO-1", "start": "2025-02-01", "end": "2025-03-01"},
                      {"op": "defer_epic", "epic": "DSO-2"}, {"op": "add_link", "from": "DSO-1", "to": "DSO-2"})
        plan_before = copy.deepcopy(plan)
        out, _ = P.apply(snap, plan)
        self.assertEqual(snap, before)
        self.assertEqual(plan, plan_before)
        self.assertIsNot(out, snap)
        self.assertNotEqual(out, snap)

    def test_S_plan_2_slice_becomes_issue_with_blocks_edges(self):
        out, rep = P.apply(snapshot(), mkplan(add(sl("S-1", unblocks=["DPE-3"], title="first rung"))))
        s = out["S-1"]
        self.assertEqual((s["par"], s["sum"], s["core"]), ("DSO-1", "first rung", False))
        self.assertEqual(s["slice"]["days"], 3)
        self.assertEqual([r["k"] for r in s["blocks"]], ["DPE-3"])
        self.assertEqual([r["k"] for r in out["DPE-3"]["blockedBy"]], ["S-1"])
        self.assertEqual(rep["conflicts"], [])

    def test_S_plan_2_missing_id_gets_a_temporary_id(self):
        s = sl("x"); del s["id"]
        out, _ = P.apply(snapshot(), mkplan(add(s)))
        self.assertIn("S-1", out)

    def test_S_plan_2_slice_can_unblock_another_slice(self):
        out, _ = P.apply(snapshot(), mkplan(add(sl("S-1", unblocks=["S-2"])), add(sl("S-2"))))
        self.assertEqual([r["k"] for r in out["S-2"]["blockedBy"]], ["S-1"])

    def test_links_dates_defer(self):
        snap = snapshot()
        snap["DSO-1"]["blocks"] = [dict(k="DSO-2", st="Backlog", s="", ext=False)]
        snap["DSO-2"]["blockedBy"] = [dict(k="DSO-1", st="Backlog", s="", ext=False)]
        out, _ = P.apply(snap, mkplan({"op": "remove_link", "from": "DSO-1", "to": "DSO-2"},
                                      {"op": "add_link", "from": "DPE-3", "to": "DSO-1"},
                                      {"op": "set_dates", "epic": "DSO-2", "start": "2025-02-01", "end": "2025-03-01"},
                                      {"op": "defer_epic", "epic": "DSO-2"}))
        self.assertEqual(out["DSO-1"]["blocks"], [])
        self.assertEqual(out["DSO-2"]["blockedBy"], [])
        self.assertEqual([r["k"] for r in out["DSO-1"]["blockedBy"]], ["DPE-3"])
        self.assertEqual([r["k"] for r in out["DPE-3"]["blocks"]], ["DSO-1"])
        self.assertEqual((out["DSO-2"]["start"], out["DSO-2"]["end"], out["DSO-2"]["deferred"]), ("2025-02-01", "2025-03-01", True))

    def test_S_plan_8_closed_or_missing_epic_is_a_conflict_and_rest_applies(self):
        plan = mkplan(add(sl("S-1", "DSO-9")), add(sl("S-2", "DSO-1")), {"op": "defer_epic", "epic": "GONE-1"},
                      {"op": "set_dates", "epic": "DSO-2", "start": "2025-02-01", "end": "2025-03-01"})
        out, rep = P.apply(snapshot(), plan)
        named = {(c["epic"], c["reason"]) for c in rep["conflicts"]}
        self.assertEqual(named, {("DSO-9", "closed"), ("GONE-1", "missing")})
        self.assertNotIn("S-1", out)
        self.assertIn("S-2", out)
        self.assertEqual(out["DSO-2"]["start"], "2025-02-01")

    def test_S_plan_8_link_to_closed_epic_is_a_conflict(self):
        _, rep = P.apply(snapshot(), mkplan({"op": "add_link", "from": "DSO-1", "to": "DSO-9"}))
        self.assertEqual([c["epic"] for c in rep["conflicts"]], ["DSO-9"])

    def test_unknown_op_is_rejected(self):
        with self.assertRaises(ValueError):
            P.apply(snapshot(), mkplan({"op": "delete_epic", "epic": "DSO-1"}))


class Validate(unittest.TestCase):
    def rules(self, plan, cfg=CFG):
        return sorted((f["rule"], f["slice"] if "slice" in f else f["epic"]) for f in P.validate(plan, snapshot(), cfg))

    def test_S_plan_3_over_pod_cap_says_split_me(self):
        plan = mkplan(add(sl("S-1", days=6)), add(sl("S-2", days=5)), add(sl("S-3", "DPE-3", days=10)), add(sl("S-4", "DPE-3", days=11)))
        self.assertEqual(self.rules(plan), [("split-me", "S-1"), ("split-me", "S-4")])

    def test_S_plan_3_default_cap_without_config(self):
        plan = mkplan(add(sl("S-1", days=10)), add(sl("S-2", days=11)))
        self.assertEqual(self.rules(plan, None), [("split-me", "S-2")])

    def test_S_plan_4_manual_debt_needs_existing_repaid_by(self):
        debt = lambda r: {"creates": "hand-run step", "repaid_by": r}
        s = lambda id, **kw: add(sl(id, value_share=0.1, **kw))
        plan = mkplan(s("S-1", mode="manual", debt=debt("S-2")), s("S-2"),
                      s("S-3", mode="manual", debt=debt("S-9")),
                      s("S-4", mode="manual", debt=debt(None)),
                      s("S-5", mode="manual"),
                      s("S-6", mode="scripted", debt=debt("S-9")))
        self.assertEqual(self.rules(plan), [("unrepaid-debt", "S-3"), ("unrepaid-debt", "S-4")])

    def test_S_plan_5_value_shares_over_one_per_epic(self):
        plan = mkplan(add(sl("S-1", value_share=0.6)), add(sl("S-2", value_share=0.5)),
                      add(sl("S-3", "DPE-3", value_share=0.5)), add(sl("S-4", "DPE-3", value_share=0.5)))
        self.assertEqual(self.rules(plan), [("value-share-over", "DSO-1")])

    def test_clean_plan_has_no_findings(self):
        self.assertEqual(P.validate(mkplan(add(sl("S-1"))), snapshot(), CFG), [])

    def test_unblocks_unknown_target(self):
        self.assertEqual(self.rules(mkplan(add(sl("S-1", unblocks=["NOPE-1", "DPE-3"])))), [("unknown-unblocks", "S-1")])


class TimeToFirstReleasable(unittest.TestCase):
    def test_S_plan_6_follows_dependency_order(self):
        plan = mkplan(add(sl("S-1", days=2, releasable=False, unblocks=["S-2"])),
                      add(sl("S-2", days=3, releasable=True, unblocks=["S-3"])),
                      add(sl("S-3", days=4, releasable=True)),
                      add(sl("S-4", "DPE-3", days=9)))
        self.assertEqual(P.time_to_first_releasable(plan, "DSO-1"), 5)
        self.assertEqual(P.time_to_first_releasable(plan, "DPE-3"), 9)

    def test_S_plan_6_independent_releasable_slice_wins(self):
        plan = mkplan(add(sl("S-1", days=2, releasable=False, unblocks=["S-2"])), add(sl("S-2", days=8)), add(sl("S-3", days=4)))
        self.assertEqual(P.time_to_first_releasable(plan, "DSO-1"), 4)

    def test_S_plan_6_none_without_releasable_slice(self):
        self.assertIsNone(P.time_to_first_releasable(mkplan(add(sl("S-1", releasable=False))), "DSO-1"))
        self.assertIsNone(P.time_to_first_releasable(mkplan(), "DSO-1"))


class Diff(unittest.TestCase):
    def test_S_plan_7_slices_links_dates(self):
        a = mkplan(add(sl("S-1")), add(sl("S-2", days=3)), {"op": "add_link", "from": "DSO-1", "to": "DSO-2"},
                   {"op": "set_dates", "epic": "DSO-1", "start": "2025-02-01", "end": "2025-03-01"})
        b = mkplan(add(sl("S-2", days=4)), add(sl("S-3")), {"op": "remove_link", "from": "DSO-1", "to": "DSO-2"},
                   {"op": "set_dates", "epic": "DSO-1", "start": "2025-02-01", "end": "2025-04-01"}, {"op": "defer_epic", "epic": "DSO-2"})
        d = P.diff(a, b)
        self.assertEqual((d["slices_added"], d["slices_removed"]), (["S-3"], ["S-1"]))
        self.assertEqual(d["slices_changed"], [{"id": "S-2", "fields": {"days": [3, 4]}}])
        self.assertEqual(d["links"], [{"from": "DSO-1", "to": "DSO-2", "a": "add", "b": "remove"}])
        self.assertEqual(d["dates"], [{"epic": "DSO-1", "a": {"start": "2025-02-01", "end": "2025-03-01"},
                                       "b": {"start": "2025-02-01", "end": "2025-04-01"}}])
        self.assertEqual(d["deferred"], [{"epic": "DSO-2", "a": False, "b": True}])

    def test_S_plan_7_identical_plans_have_empty_diff(self):
        a = mkplan(add(sl("S-1")), {"op": "add_link", "from": "DSO-1", "to": "DSO-2"})
        d = P.diff(a, copy.deepcopy(a))
        self.assertEqual([v for v in d.values() if v], [])


class RoundTrip(unittest.TestCase):
    def plan(self):
        return mkplan({"op": "remove_link", "from": "DSO-1", "to": "DSO-2"}, add(sl("S-2")), {"op": "defer_epic", "epic": "DSO-2"},
                      add(sl("S-1", unblocks=["S-2"])), {"op": "add_link", "from": "DPE-3", "to": "DSO-1"},
                      {"op": "set_dates", "epic": "DSO-1", "start": "2025-02-01", "end": "2025-03-01"})

    def test_S_plan_9_json_round_trip_with_stable_ordering(self):
        plan = self.plan()
        shuffled = copy.deepcopy(plan)
        shuffled["ops"].reverse()
        shuffled["ops"].sort(key=lambda o: o["op"], reverse=True)
        with tempfile.TemporaryDirectory() as d:
            p1, p2 = os.path.join(d, "a.json"), os.path.join(d, "b.json")
            P.dump_plan(plan, p1)
            P.dump_plan(shuffled, p2)
            t1 = open(p1).read()
            self.assertEqual(t1, open(p2).read())
            self.assertTrue(t1.endswith("\n"))
            self.assertEqual(t1, P.dump_plan(plan))
            back = P.load_plan(p1)
            self.assertEqual(json.loads(t1), back)
            self.assertEqual(P.dump_plan(back), t1)
        self.assertEqual([o["op"] for o in back["ops"]],
                         ["add_slice", "add_slice", "defer_epic", "set_dates", "add_link", "remove_link"])
        self.assertEqual([o["slice"]["id"] for o in back["ops"][:2]], ["S-1", "S-2"])

    def test_S_plan_9_ordering_keeps_remove_then_add_of_same_link(self):
        plan = mkplan({"op": "remove_link", "from": "A-1", "to": "B-1"}, {"op": "add_link", "from": "A-1", "to": "B-1"})
        self.assertEqual([o["op"] for o in json.loads(P.dump_plan(plan))["ops"]], ["remove_link", "add_link"])

    def test_S_plan_9_yaml_is_accepted_on_load(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        plan = self.plan()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.yaml")
            open(p, "w").write(yaml.safe_dump(plan))
            self.assertEqual(P.load_plan(p), plan)


class Purity(unittest.TestCase):
    def test_S_plan_10_no_network_or_jira_client_imports(self):
        src = open(os.path.join(HERE, "..", "scripts", "plan.py")).read()
        mods = set()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        banned = {"urllib", "http", "socket", "ssl", "requests", "httpx", "netrc", "subprocess", "jira", "jira_common", "po_view"}
        self.assertEqual(mods & banned, set())
        self.assertLessEqual(mods, {"copy", "json", "os", "sys", "topology"})

    def test_S_plan_10_no_network_calls_by_name(self):
        src = open(os.path.join(HERE, "..", "scripts", "plan.py")).read()
        for word in ("urlopen", "client(", "socket", "netrc", "Authorization"):
            self.assertNotIn(word, src)


if __name__ == "__main__":
    unittest.main()
