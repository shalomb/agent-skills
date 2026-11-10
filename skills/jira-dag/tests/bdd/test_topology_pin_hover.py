"""Characterisation of Topologies hover and pin (specs/topology-pin-hover.md, S-pin-1..S-pin-9).

The page is built from a synthetic issue set with scripts/topology.py and the shared shell in jira_common.app_page
(hover and cards live in the shell's script). No Jira, no po_view.py, no network. A Node/puppeteer driver
(pin_hover_driver.js) runs every scenario once in one headless Chrome and returns DOM snapshots; assertions are here.
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import topology
from jira_common import ISSUE_FIELDS, app_page

PUPPETEER = os.environ.get("PUPPETEER_MODULE", "/home/unop/.local/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer")
CHROME = os.environ.get("CHROME_BIN") or next(iter(sorted(glob.glob(os.path.expanduser("~/.cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell")))), None)
NODE = shutil.which("node")
MISSING = ("node not found" if not NODE else "puppeteer module not found" if not os.path.isdir(PUPPETEER)
           else "chrome-headless-shell not found" if not CHROME or not os.path.exists(CHROME) else None)

CFG = {"art": "Synthetic ART", "pods": [{"id": "A", "projects": ["AAA"]}, {"id": "B", "projects": ["BBB"]}], "interface": {"projects": ["REQ"]}}

# REQ-1 -> AAA-1 -> BBB-1 -> AAA-2 is the chain of three epics across two PODs, with REQ-1 (interface) in front.
# BBB-2 -> EXT-9 leaves the ART; EXT-5 -> AAA-3 enters it. BBB-3 -> BBB-4 is a same-POD link (not drawn).
SUMMARIES = {"REQ-1": ("Product request", "Analyzing", 9), "AAA-1": ("Platform base", "In Progress", 8), "BBB-1": ("Shared service", "Backlog", 5),
             "AAA-2": ("Consumer rollout", "Backlog", 3), "BBB-2": ("Export feed", "Backlog", 2), "EXT-9": ("Other ART intake", "Funnel", None),
             "EXT-5": ("Other ART provider", "In Progress", None), "AAA-3": ("Needs outside input", "Analyzing", 4),
             "BBB-3": ("Same POD first", "Backlog", 1), "BBB-4": ("Same POD second", "Backlog", 1)}
LINKS = [("REQ-1", "AAA-1"), ("AAA-1", "BBB-1"), ("BBB-1", "AAA-2"), ("BBB-2", "EXT-9"), ("EXT-5", "AAA-3"), ("BBB-3", "BBB-4")]
DRAWN = {"REQ-1|AAA-1", "AAA-1|BBB-1", "BBB-1|AAA-2", "BBB-2|EXT-9", "EXT-5|AAA-3"}
ALL_BOXES = {"REQ-1", "AAA-1", "BBB-1", "AAA-2", "BBB-2", "EXT-9", "EXT-5", "AAA-3"}


def synthetic_issues():
    I = {}
    for k, (s, st, ws) in SUMMARIES.items():
        I[k] = dict(key=k, sum=s, st=st, ws=ws, blocks=[], blockedBy=[], relates=[], core=not k.startswith("EXT"), url="https://jira.example.com/browse/" + k)
    for a, b in LINKS:
        I[a]["blocks"].append(dict(k=b, st=I[b]["st"], s=I[b]["sum"], ext=False))
        I[b]["blockedBy"].append(dict(k=a, st=I[a]["st"], s=I[a]["sum"], ext=False))
    return I


def build_page(path):
    """Write the page under test; return the render() dict (server-side layout)."""
    I = synthetic_issues()
    r = topology.render(I, CFG)
    issues = {k: {f: v.get(f) for f in ISSUE_FIELDS} | {"tl": []} for k, v in I.items()}
    lister = '<div class=att><ul>' + "".join(f'<li data-k="{k}">{k}</li>' for k in ("BBB-3",)) + "</ul></div>"
    panels = [dict(id="topology", label="Topologies", svg=r["svg"], legend=topology.LEGEND, edges=r["edges"]), dict(id="list", label="List", html=lister)]
    data = dict(base="https://jira.example.com", issues=issues)
    with open(path, "w") as f:
        f.write(app_page("Synthetic topology", "test fixture", panels, data, sorted({v["st"] for v in I.values()}), topology.CSS, topology.js(r)))
    return r


def server_boxes(svg):
    """Positions of each box as written by the server-side renderer."""
    return {k: (float(x), float(y)) for k, x, y in re.findall(r'<g data-key="([^"]+)" class="tn"><rect x="([\d.]+)" y="([\d.]+)"', svg)}


def numbers(d):
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]


HOVER, LEAVE = "hover", "leave"
pin_steps = lambda *keys: [{"shiftClick": k} for k in keys]
FULL = {"clickText": [".tbar button", "Full chain"]}
DIRECT = {"clickText": [".tbar button", "Direct"]}
UNPIN_ALL = {"clickText": [".tbar button", "Unpin all"]}
SCENARIOS = {
    "hover_chain": {"steps": [{"snap": "rest"}, {"hover": "BBB-1"}, {"wait": 300}, {"snap": "middle"}, {"hover": "AAA-2"}, {"wait": 300}, {"snap": "end"},
                              {"leave": 1}, {"wait": 300}, {"snap": "away"}]},
    "pin_one": {"steps": [{"snap": "rest"}] + pin_steps("AAA-1") + [{"snap": "pinned"}]},
    "pin_external": {"steps": pin_steps("BBB-2") + [{"snap": "pinned"}]},
    "pin_two_neighbours": {"steps": pin_steps("AAA-1", "BBB-1") + [{"snap": "pinned"}]},
    "pin_two_apart": {"steps": pin_steps("AAA-1") + [{"eval": "window.topoToggle('AAA-3')"}, {"snap": "pinned"}]},
    "depth": {"steps": pin_steps("BBB-1") + [{"snap": "direct"}, FULL, {"snap": "full"}, DIRECT, {"snap": "back"}]},
    "unpin_chip": {"steps": [{"snap": "rest"}] + pin_steps("AAA-1") + [{"eval": "window.topoToggle('AAA-3')"}, {"clickText": [".tbar .pc", "AAA-1"]}, {"snap": "one_left"},
                                                                                 {"clickText": [".tbar .pc", "AAA-3"]}, {"snap": "after"}]},
    "unpin_all": {"steps": [{"snap": "rest"}] + pin_steps("AAA-1") + [FULL, UNPIN_ALL, {"snap": "after"}]},
    "unpin_esc": {"steps": [{"snap": "rest"}] + pin_steps("AAA-1") + [{"press": "Escape"}, {"snap": "after"}]},
    "stale_on_pin": {"steps": [{"hover": "AAA-3"}, {"snap": "hovering"}, {"evalSnap": "window.topoToggle('AAA-3')", "label": "pinned"}]},
    "stale_on_unpin": {"steps": [{"eval": "window.topoPin(['AAA-1','AAA-3'])"}, {"hover": "AAA-1"}, {"snap": "hovering"},
                                 {"evalSnap": "window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))", "label": "unpinned"}]},
    "hash_written": {"steps": [{"snap": "rest"}] + pin_steps("AAA-1", "BBB-1") + [{"snap": "direct"}, FULL, {"snap": "full"}, UNPIN_ALL, {"snap": "none"}]},
    "hash_restore": {"hash": "#pin=AAA-1,BBB-1&depth=full", "steps": [{"snap": "loaded"}]},
    "hash_restore_encoded": {"hash": "#tab=topology&pin=AAA-1%2CBBB-1&depth=full", "steps": [{"snap": "loaded"}]},
    "rest": {"steps": [{"snap": "rest"}]},
    "card_pin": {"steps": [{"click": "AAA-1"}, {"snap": "card"}, {"clickText": ["#card .pinb", "Pin"]}, {"snap": "pinned"},
                           {"click": "AAA-1"}, {"snap": "card_again"}, {"clickText": ["#card .pinb", "Unpin"]}, {"snap": "unpinned"}]},
    "card_not_pinnable": {"steps": [{"eval": "document.querySelector('.att li').click()"}, {"snap": "card"}]},
}


@unittest.skipIf(bool(MISSING), MISSING or "")
class TopologyPinHover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.mkdtemp(prefix="topology-bdd-")
        cls.addClassCleanup(shutil.rmtree, tmp, True)
        page = os.path.join(tmp, "topology.html")
        cls.server = build_page(page)
        job = os.path.join(tmp, "job.json")
        with open(job, "w") as f:
            json.dump(dict(puppeteer=PUPPETEER, chrome=CHROME, url="file://" + page, scenarios=SCENARIOS), f)
        run = subprocess.run([str(NODE), os.path.join(HERE, "pin_hover_driver.js"), job], capture_output=True, text=True, timeout=180)
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
    def dimmed(s):
        return {k for k, b in s["boxes"].items() if b["dim"]}

    @staticmethod
    def edges_shown(s):
        return {e for e, p in s["edges"].items() if p["shown"]}

    @staticmethod
    def edges_dimmed(s):
        return {e for e, p in s["edges"].items() if p["dim"]}

    @staticmethod
    def hash_params(s):
        from urllib.parse import parse_qs
        return {k: v[0] for k, v in parse_qs(s["hash"].lstrip("#")).items()}

    def assert_at_rest(self, s):
        self.assertEqual(self.shown(s), ALL_BOXES)
        self.assertEqual(self.edges_shown(s), DRAWN)
        self.assertEqual(self.dimmed(s), set())
        self.assertEqual(self.edges_dimmed(s), set())
        self.assertEqual({b for b, v in s["bands"].items() if v["hidden"]}, set())
        self.assertEqual(s["chips"], [])

    # S-pin-1
    def test_S_pin_1_hover_dims_everything_outside_the_chain_and_leaving_restores(self):
        s = self.snaps("hover_chain")
        self.assertEqual(self.dimmed(s["rest"]), set())
        for label, other_end in (("middle", "BBB-1"), ("end", "AAA-2")):
            h = s[label]
            self.assertEqual(self.shown(h), ALL_BOXES, "hover only dims, nothing is hidden")
            self.assertEqual(self.dimmed(h), {"BBB-2", "EXT-9", "EXT-5", "AAA-3"}, f"hover {other_end}: chain is REQ-1, AAA-1, BBB-1, AAA-2")
            self.assertEqual(self.edges_dimmed(h), {"BBB-2|EXT-9", "EXT-5|AAA-3"})
            for k in ALL_BOXES - self.dimmed(h):
                self.assertEqual(h["boxes"][k]["opacity"], 1, k)
            for k in self.dimmed(h):
                self.assertAlmostEqual(h["boxes"][k]["opacity"], 0.14, 2, k)
            for e in self.edges_dimmed(h):
                self.assertEqual(h["edges"][e]["opacity"], 0, e)
            for e in DRAWN - self.edges_dimmed(h):
                self.assertEqual(h["edges"][e]["opacity"], 1, e)
        away = s["away"]
        self.assertEqual(self.dimmed(away), set())
        self.assertEqual(self.edges_dimmed(away), set())
        self.assertTrue(all(b["opacity"] == 1 for b in away["boxes"].values()))
        self.assertTrue(all(p["opacity"] == 1 for p in away["edges"].values()))

    # S-pin-2
    def test_S_pin_2_shift_click_shows_only_the_epic_and_its_direct_neighbours(self):
        s = self.snaps("pin_one")
        p = s["pinned"]
        self.assertEqual(self.shown(p), {"REQ-1", "AAA-1", "BBB-1"})
        self.assertEqual(self.edges_shown(p), {"REQ-1|AAA-1", "AAA-1|BBB-1"}, "lines between hidden boxes are gone")
        self.assertEqual({b for b, v in p["bands"].items() if v["hidden"]}, {"product", "ext_out"}, "empty bands collapse; interface and lanes stay")
        self.assertEqual(s["rest"]["bands"]["product"]["hidden"], False, "at rest the empty product band is still drawn")
        self.assertLess(p["boxes"]["REQ-1"]["pos"][1], s["rest"]["boxes"]["REQ-1"]["pos"][1], "collapsed bands pull the rest up")
        self.assertLess(p["svgHeight"], s["rest"]["svgHeight"])
        self.assertEqual(p["chips"], ["AAA-1 ✕"])
        self.assertIn("3 epics shown", p["bar"])
        self.assertEqual(self.hash_params(p).get("pin"), "AAA-1")

    def test_S_pin_2_pinning_an_epic_with_an_external_neighbour_keeps_the_external_band(self):
        p = self.snaps("pin_external")["pinned"]
        self.assertEqual(self.shown(p), {"BBB-2", "EXT-9"})
        self.assertEqual(self.edges_shown(p), {"BBB-2|EXT-9"})
        self.assertEqual({b for b, v in p["bands"].items() if v["hidden"]}, {"product", "interface"})

    # S-pin-3
    def test_S_pin_3_second_pin_shows_both_and_their_direct_neighbours(self):
        p = self.snaps("pin_two_neighbours")["pinned"]
        self.assertEqual(self.shown(p), {"REQ-1", "AAA-1", "BBB-1", "AAA-2"})
        self.assertEqual(p["chips"], ["AAA-1 ✕", "BBB-1 ✕"])
        self.assertEqual(self.edges_shown(p), {"REQ-1|AAA-1", "AAA-1|BBB-1", "BBB-1|AAA-2"})
        self.assertEqual(self.hash_params(p).get("pin"), "AAA-1,BBB-1")

    def test_S_pin_3_two_unrelated_pins_each_bring_their_own_neighbours(self):
        p = self.snaps("pin_two_apart")["pinned"]
        self.assertEqual(self.shown(p), {"REQ-1", "AAA-1", "BBB-1", "AAA-3", "EXT-5"})
        self.assertEqual(self.edges_shown(p), {"REQ-1|AAA-1", "AAA-1|BBB-1", "EXT-5|AAA-3"})

    # S-pin-4
    def test_S_pin_4_full_chain_shows_whole_chain_and_direct_returns_to_neighbours(self):
        s = self.snaps("depth")
        self.assertEqual(self.shown(s["direct"]), {"AAA-1", "BBB-1", "AAA-2"})
        self.assertEqual(self.edges_shown(s["direct"]), {"AAA-1|BBB-1", "BBB-1|AAA-2"})
        self.assertEqual([b["text"] for b in s["direct"]["buttons"] if b["on"]], ["Direct"])
        self.assertEqual(self.shown(s["full"]), {"REQ-1", "AAA-1", "BBB-1", "AAA-2"}, "upstream and downstream reach beyond direct neighbours")
        self.assertEqual(self.edges_shown(s["full"]), {"REQ-1|AAA-1", "AAA-1|BBB-1", "BBB-1|AAA-2"})
        self.assertEqual([b["text"] for b in s["full"]["buttons"] if b["on"]], ["Full chain"])
        self.assertEqual(self.shown(s["back"]), self.shown(s["direct"]))
        self.assertEqual(self.edges_shown(s["back"]), self.edges_shown(s["direct"]))
        self.assertEqual([b["text"] for b in s["back"]["buttons"] if b["on"]], ["Direct"])

    # S-pin-5
    def assert_restored(self, rest, after):
        self.assert_at_rest(after)
        for k, b in after["boxes"].items():
            self.assertEqual(b["pos"], rest["boxes"][k]["pos"], k)
        self.assertEqual(after["svgHeight"], rest["svgHeight"])
        self.assertEqual({k: v["top"] for k, v in after["bands"].items()}, {k: v["top"] for k, v in rest["bands"].items()})
        self.assertNotIn("pin", self.hash_params(after))

    def test_S_pin_5_unpinning_the_last_pin_with_its_chip_restores_everything(self):
        s = self.snaps("unpin_chip")
        self.assertEqual(s["one_left"]["chips"], ["AAA-3 ✕"], "one pin left still filters")
        self.assertEqual(self.shown(s["one_left"]), {"AAA-3", "EXT-5"})
        self.assert_restored(s["rest"], s["after"])

    def test_S_pin_5_unpin_all_button_restores_everything(self):
        s = self.snaps("unpin_all")
        self.assert_restored(s["rest"], s["after"])

    def test_S_pin_5_escape_restores_everything(self):
        s = self.snaps("unpin_esc")
        self.assert_restored(s["rest"], s["after"])

    # S-pin-6
    def test_S_pin_6_pinning_under_an_active_hover_leaves_no_dimming(self):
        s = self.snaps("stale_on_pin")
        self.assertTrue(self.dimmed(s["hovering"]), "precondition: hover is dimming")
        self.assertEqual(self.dimmed(s["pinned"]), set())
        self.assertEqual(self.edges_dimmed(s["pinned"]), set())

    def test_S_pin_6_unpinning_under_an_active_hover_leaves_no_dimming(self):
        s = self.snaps("stale_on_unpin")
        self.assertEqual(self.dimmed(s["hovering"]), {"AAA-3", "EXT-5", "BBB-2", "EXT-9"}, "precondition: hover dims everything outside the chain, hidden boxes included")
        self.assertEqual(self.dimmed(s["unpinned"]), set())
        self.assertEqual(self.edges_dimmed(s["unpinned"]), set())
        self.assertEqual(self.shown(s["unpinned"]), ALL_BOXES)

    # S-pin-7
    def test_S_pin_7_hash_holds_pins_and_depth(self):
        s = self.snaps("hash_written")
        self.assertEqual(self.hash_params(s["direct"]).get("pin"), "AAA-1,BBB-1")  # the page writes the comma as %2C; same value once decoded
        self.assertNotIn("depth", self.hash_params(s["direct"]))
        self.assertEqual(self.hash_params(s["full"]).get("pin"), "AAA-1,BBB-1")
        self.assertEqual(self.hash_params(s["full"]).get("depth"), "full")
        self.assertNotIn("pin", self.hash_params(s["none"]))
        self.assertNotIn("depth", self.hash_params(s["none"]))

    def test_S_pin_7_loading_a_hash_restores_the_same_view(self):
        written = self.snaps("hash_written")["full"]
        for name in ("hash_restore", "hash_restore_encoded"):
            loaded = self.snaps(name)["loaded"]
            self.assertEqual(self.shown(loaded), self.shown(written), name)
            self.assertEqual(self.edges_shown(loaded), self.edges_shown(written), name)
            self.assertEqual({k: b["pos"] for k, b in loaded["boxes"].items()}, {k: b["pos"] for k, b in written["boxes"].items()}, name)
            self.assertEqual(loaded["chips"], written["chips"], name)
            self.assertEqual([b["text"] for b in loaded["buttons"] if b["on"]], ["Full chain"], name)

    # S-pin-8
    def test_S_pin_8_without_pins_box_positions_equal_the_server_layout(self):
        s = self.snaps("rest")["rest"]
        server = server_boxes(self.server["svg"])
        self.assertEqual(set(server), ALL_BOXES)
        self.assert_at_rest(s)
        for k, (x, y) in server.items():
            self.assertEqual(tuple(s["boxes"][k]["pos"]), (x, y), k)
        self.assertEqual(s["svgHeight"], self.server["spec"]["height"])
        for e, p in s["edges"].items():
            server_d = re.search(r'<path d="([^"]+)"[^>]*data-edge="%s"' % re.escape(e), self.server["svg"]).group(1)
            self.assertEqual(numbers(p["d"]), numbers(server_d), e)

    # S-pin-9
    def test_S_pin_9_card_offers_pin_or_unpin_matching_the_pin_state(self):
        s = self.snaps("card_pin")
        self.assertEqual((s["card"]["card"]["title"], s["card"]["card"]["pinText"]), ("AAA-1 ↗", "Pin on Topologies"))
        self.assertEqual(s["pinned"]["chips"], ["AAA-1 ✕"], "the card's Pin pins the epic")
        self.assertFalse(s["pinned"]["card"]["visible"], "and closes the card")
        self.assertEqual(s["card_again"]["card"]["pinText"], "Unpin from Topologies")
        self.assertEqual(s["unpinned"]["chips"], [], "the card's Unpin unpins it")
        self.assertEqual(self.shown(s["unpinned"]), ALL_BOXES)

    def test_S_pin_9_card_of_an_epic_that_is_not_on_the_topology_offers_no_pin(self):
        card = self.snaps("card_not_pinnable")["card"]["card"]
        self.assertTrue(card["visible"])
        self.assertTrue(card["title"].startswith("BBB-3"))
        self.assertIsNone(card["pinText"])


if __name__ == "__main__":
    unittest.main()
