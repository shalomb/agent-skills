"""Browser scenarios for the Topologies filter drawer (specs/filters-state.md, S-ui-1..S-ui-5).

Same harness style as the pin tests: a synthetic page, one headless Chrome run (filters_ui_driver.js), assertions here.
Logic (matching, ghosts, hash round-trip) is covered without a browser in tests/js.
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import topology
from jira_common import ISSUE_FIELDS, app_page
from test_topology_pin_hover import ALL_BOXES, CFG, CHROME, DRAWN, MISSING, NODE, PUPPETEER, synthetic_issues

SHOTS = os.environ.get("FILTER_SHOTS_DIR")
LABELS = {"REQ-1": ["kind-enabler", "for-web"], "AAA-1": ["kind-enabler", "area-x"], "BBB-1": ["kind-deliverable"], "AAA-2": ["kind-deliverable", "pi-q1"]}
DATES = {"REQ-1": ("2025-01-01", "2025-02-15"), "AAA-1": ("2025-02-01", "2025-03-15"), "BBB-1": ("2025-03-01", "2025-06-30"), "AAA-2": ("2025-07-01", "2025-08-31")}


def build_page(path, components=None):
    I = synthetic_issues()
    for k, v in I.items():
        v["labels"], v["components"] = LABELS.get(k, []), (components or {}).get(k, [])
        v["start"], v["end"] = DATES.get(k, (None, None))
    r = topology.render(I, CFG)
    issues = {k: {f: v.get(f) for f in ISSUE_FIELDS} | {"tl": []} for k, v in I.items()}
    lister = '<div class=att><ul><li data-k="BBB-3">BBB-3</li></ul></div>'
    panels = [dict(id="topology", label="Topologies", svg=r["svg"], legend=topology.LEGEND, edges=r["edges"]), dict(id="list", label="List", html=lister)]
    with open(path, "w") as f:
        f.write(app_page("Synthetic topology", "test fixture", panels, dict(base="https://jira.example.com", issues=issues),
                         sorted({v["st"] for v in I.values()}), topology.CSS, topology.js(r)))
    return r


def shot(name):
    return [{"shot": os.path.join(SHOTS, name + ".png")}] if SHOTS else []


KIND_ENABLER = {"clickText": ["#p-topology .tdrawer label.opt", "kind-enabler"]}
OPEN = {"clickText": ["#p-topology .tbar button", "Filters"]}
SCENARIOS = {
    "rest": {"steps": [{"snap": "closed"}]},
    "drawer": {"steps": [{"snap": "closed"}, OPEN, {"snap": "open"}] + shot("drawer-open") + [{"press": "Escape"}, {"snap": "esc"}]},
    "before_bar": {"steps": [{"eval": "document.body.removeAttribute('data-tab')"}, {"snap": "global_bar_back"}]},
    "other_tab": {"steps": [{"click": "nav button[data-t=list]"}, {"snap": "list_tab"}, {"eval": "document.getElementById('q').value='x';document.getElementById('q').dispatchEvent(new Event('input'))"},
                            {"eval": "document.querySelector('nav button[data-t=topology]').click()"}, {"snap": "back"}]},
    "filter": {"steps": [{"snap": "rest"}, OPEN, KIND_ENABLER, {"wait": 300}, {"snap": "filtered"}] + shot("filtered") + [{"clickText": ["#p-topology .tbar .fc", "kind-enabler"]}, {"wait": 300}, {"snap": "cleared"}]},
    "filter_hash": {"steps": [OPEN, KIND_ENABLER, {"wait": 300}, {"snap": "filtered"}, {"reload": 1}, {"snap": "reloaded"}]},
    "clear_all": {"steps": [{"snap": "rest"}, OPEN, KIND_ENABLER, {"clickText": ["#p-topology .tdrawer button", "Blocking others"]}, {"snap": "two"},
                            {"clickText": ["#p-topology .tbar button", "Clear filters"]}, {"snap": "cleared"}]},
    "date_filter": {"steps": [OPEN, {"eval": "const r=document.querySelectorAll('#p-topology .tdrawer input[type=range]');r[0].value=r[0].max*0.6;r[0].dispatchEvent(new Event('input'))"},
                              {"snap": "dated"}]},
    "components_none": {"steps": [OPEN, {"snap": "open"}]},
    "pin_then_unpin": {"steps": [OPEN, KIND_ENABLER, {"wait": 300}, {"snap": "filtered"}, {"shiftClick": "BBB-1"}, {"snap": "pinned"}, {"press": "Escape"}, {"press": "Escape"}, {"wait": 300}, {"snap": "unpinned"}]},
    "pin_chip_unpin": {"steps": [{"eval": "window.topoPin(['BBB-1'])"}, OPEN, KIND_ENABLER, {"clickText": ["#p-topology .tbar .pc", "BBB-1"]}, {"wait": 300}, {"snap": "unpinned"}]},
    "legend": {"steps": [{"clickText": ["#p-topology .tbar button", "?"]}, {"snap": "legend"}]},
}
COMPONENT_SCENARIOS = {"components_some": {"steps": [OPEN, {"snap": "open"}]}}


@unittest.skipIf(bool(MISSING), MISSING or "")
class FiltersUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.mkdtemp(prefix="filters-bdd-")
        cls.addClassCleanup(shutil.rmtree, tmp, True)
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
        plain, withc = os.path.join(tmp, "plain.html"), os.path.join(tmp, "components.html")
        cls.server = build_page(plain)
        build_page(withc, {"BBB-1": ["api"], "AAA-2": ["api", "ui"]})
        scenarios = {n: dict(s, url="file://" + plain) for n, s in SCENARIOS.items()} | {n: dict(s, url="file://" + withc) for n, s in COMPONENT_SCENARIOS.items()}
        job = os.path.join(tmp, "job.json")
        with open(job, "w") as f:
            json.dump(dict(puppeteer=PUPPETEER, chrome=CHROME, scenarios=scenarios), f)
        run = subprocess.run([str(NODE), os.path.join(HERE, "filters_ui_driver.js"), job], capture_output=True, text=True, timeout=240)
        if run.returncode:
            raise RuntimeError("driver failed: " + run.stderr)
        cls.out = json.loads(run.stdout)

    def snaps(self, name):
        sc = self.out[name]
        self.assertEqual(sc["errors"], [], name)
        return sc["snaps"]

    @staticmethod
    def shown(s):
        return {k for k, b in s["boxes"].items() if b["shown"]}

    @staticmethod
    def ghosts(s):
        return {k for k, b in s["boxes"].items() if b["shown"] and b["ghost"]}

    @staticmethod
    def edges_shown(s):
        return {e for e, p in s["edges"].items() if p["shown"]}

    def assert_unfiltered(self, s, rest):
        self.assertEqual(self.shown(s), ALL_BOXES)
        self.assertEqual(self.edges_shown(s), DRAWN)
        self.assertEqual(self.ghosts(s), set())
        self.assertEqual({k: b["pos"] for k, b in s["boxes"].items()}, {k: b["pos"] for k, b in rest["boxes"].items()})
        self.assertEqual(s["svgHeight"], rest["svgHeight"])

    # S-ui-1
    def test_S_ui_1_filter_controls_live_in_a_drawer_behind_one_filters_button(self):
        s = self.snaps("drawer")
        self.assertEqual(s["closed"]["filtersButton"], "Filters (0)")
        self.assertFalse(s["closed"]["drawer"]["open"])
        self.assertTrue(s["open"]["drawer"]["open"])
        self.assertFalse(s["esc"]["drawer"]["open"], "Esc closes the drawer before it clears anything")
        groups = {g["prefix"]: g["labels"] for g in s["open"]["drawer"]["labelGroups"]}
        self.assertEqual(groups, {"kind-": ["kind-deliverable", "kind-enabler"], "for-": ["for-web"], "pi-": ["pi-q1"], "other": ["area-x"]})
        self.assertEqual({(b["kind"], b["value"]) for b in s["open"]["drawer"]["buttons"] if b["kind"] == "rel"},
                         {("rel", "incoming"), ("rel", "external"), ("rel", "blocking")})
        self.assertTrue(s["open"]["drawer"]["ranges"] >= 2, "two date handles")
        self.assertIn("undated", s["open"]["drawer"]["checked"], "Undated is on by default")

    def test_S_ui_1_drawer_overlays_the_diagram_and_the_global_bar_is_gone_on_this_tab(self):
        s = self.snaps("drawer")
        self.assertEqual(s["open"]["svgTop"], s["closed"]["svgTop"], "opening the drawer does not push the diagram down")
        self.assertFalse(s["closed"]["globalFilterBarVisible"])
        before = self.snaps("before_bar")["global_bar_back"]
        self.assertTrue(before["globalFilterBarVisible"])
        # Old layout above the diagram: header with the global filter bar, the legend row, and the pin bar row. Now: header without the bar, one strip.
        old_top = before["headerHeight"] + self.snaps("legend")["legend"]["legendHeight"] + s["closed"]["stripHeight"]
        self.assertLess(s["closed"]["svgTop"], old_top, "the diagram starts higher than with the old filter bar and legend above it")

    def test_S_ui_1_other_tabs_keep_the_global_filter_bar(self):
        s = self.snaps("other_tab")
        self.assertTrue(s["list_tab"]["globalFilterBarVisible"])
        self.assertEqual(self.shown(s["back"]), ALL_BOXES, "global filter text does not touch the Topologies view")

    def test_S_ui_1_legend_sits_behind_a_question_mark_popover(self):
        s = self.snaps("legend")["legend"]
        self.assertTrue(s["legendOpen"])

    # S-ui-2
    def test_S_ui_2_filter_removes_non_matches_closes_layout_and_ghosts_neighbours_faded(self):
        s = self.snaps("filter")
        f, rest = s["filtered"], s["rest"]
        self.assertEqual(self.shown(f), {"REQ-1", "AAA-1", "BBB-1"})
        self.assertEqual(self.ghosts(f), {"BBB-1"})
        self.assertLess(f["boxes"]["BBB-1"]["opacity"], 0.5)
        self.assertEqual(f["boxes"]["AAA-1"]["opacity"], 1)
        self.assertEqual(self.edges_shown(f), {"REQ-1|AAA-1", "AAA-1|BBB-1"})
        self.assertTrue(f["edges"]["AAA-1|BBB-1"]["ghost"])
        self.assertLess(f["edges"]["AAA-1|BBB-1"]["opacity"], 0.5)
        self.assertFalse(f["edges"]["REQ-1|AAA-1"]["ghost"])
        self.assertLess(f["svgHeight"], rest["svgHeight"], "the layout closes up")
        self.assertEqual(f["filterChips"], ["kind-enabler ✕"])
        self.assertEqual(f["filtersButton"], "Filters (1)")
        self.assertIn("2 epics shown of 8", f["count"])

    def test_S_ui_2_a_status_chip_filters_too(self):
        s = self.snaps("clear_all")["two"]
        self.assertEqual(s["filterChips"], ["kind-enabler ✕", "Blocking others ✕"])
        self.assertEqual(s["filtersButton"], "Filters (2)")

    def test_S_ui_2_date_range_handle_filters_and_keeps_undated_on(self):
        s = self.snaps("date_filter")["dated"]
        self.assertEqual(len(s["filterChips"]), 1)
        self.assertTrue(s["filterChips"][0].startswith("Target 2025-"))
        self.assertIn("from=", s["hash"])
        self.assertIn("BBB-1", self.shown(s))

    # S-ui-3
    def test_S_ui_3_reloading_the_url_restores_the_same_view(self):
        s = self.snaps("filter_hash")
        self.assertIn("label=kind-enabler", s["filtered"]["hash"])
        r, f = s["reloaded"], s["filtered"]
        self.assertEqual(self.shown(r), self.shown(f))
        self.assertEqual(self.ghosts(r), self.ghosts(f))
        visible = self.shown(f)
        self.assertEqual({k: r["boxes"][k]["pos"] for k in visible}, {k: f["boxes"][k]["pos"] for k in visible})
        self.assertEqual(r["filterChips"], f["filterChips"])
        self.assertIn("kind-enabler", r["drawer"]["checked"])

    def test_S_ui_3_clearing_the_chips_returns_the_unfiltered_layout_exactly(self):
        s = self.snaps("filter")
        self.assert_unfiltered(s["cleared"], s["rest"])
        self.assertEqual(s["cleared"]["filterChips"], [])
        self.assertNotIn("label", s["cleared"]["hash"])
        c = self.snaps("clear_all")
        self.assert_unfiltered(c["cleared"], c["rest"])
        self.assertEqual(c["cleared"]["filtersButton"], "Filters (0)")
        server = self.server["spec"]["nodes"]
        for k, b in c["cleared"]["boxes"].items():
            self.assertEqual(tuple(b["pos"]), (server[k]["x"], server[k]["y"]), k)

    # S-ui-4
    def test_S_ui_4_components_control_is_present_but_disabled_with_a_hint_when_empty(self):
        c = self.snaps("components_none")["open"]["components"]
        self.assertIsNotNone(c, "present, not hidden")
        self.assertTrue(c["disabled"])
        self.assertTrue(c["hint"])
        self.assertEqual(c["inputs"], 0)

    def test_S_ui_4_components_control_is_enabled_when_epics_have_components(self):
        c = self.snaps("components_some")["open"]["components"]
        self.assertFalse(c["disabled"])
        self.assertEqual(c["inputs"], 2)

    # S-ui-5
    def test_S_ui_5_unpinning_returns_to_the_filtered_view_not_the_unfiltered_one(self):
        s = self.snaps("pin_then_unpin")
        self.assertEqual(self.shown(s["pinned"]), {"AAA-1", "BBB-1", "AAA-2"}, "pinned BBB-1 and its direct neighbours; the filter is paused")
        self.assertEqual(s["pinned"]["pinChips"], ["BBB-1 ✕"])
        u, f = s["unpinned"], s["filtered"]
        self.assertEqual(u["pinChips"], [])
        self.assertEqual(self.shown(u), self.shown(f))
        self.assertEqual(self.ghosts(u), self.ghosts(f))
        visible = self.shown(f)
        self.assertEqual({k: u["boxes"][k]["pos"] for k in visible}, {k: f["boxes"][k]["pos"] for k in visible}, "hidden boxes keep stale positions; shown ones must match")
        self.assertEqual(u["filterChips"], ["kind-enabler ✕"])

    def test_S_ui_5_unpinning_with_the_chip_also_returns_to_the_filtered_view(self):
        u = self.snaps("pin_chip_unpin")["unpinned"]
        self.assertEqual(u["pinChips"], [])
        self.assertEqual(self.shown(u), {"REQ-1", "AAA-1", "BBB-1"})
        self.assertEqual(self.ghosts(u), {"BBB-1"})


if __name__ == "__main__":
    unittest.main()
