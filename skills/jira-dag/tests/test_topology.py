import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import topology

CFG = {"art": "Platform ART",
       "pods": [{"id": "DSO", "projects": ["DSO"]}, {"id": "DPE", "projects": ["DPE"]}, {"id": "APE", "projects": ["APE"]}],
       "interface": {"projects": ["REQ"]},
       "products": [{"id": "P1", "projects": ["P1"]}]}


def node(k, st="Backlog", blocks=(), blocked=()):
    r = lambda x: dict(k=x, st="Backlog", s=x, ext=False)
    return dict(key=k, sum=k, st=st, ws=None, blocks=[r(x) for x in blocks], blockedBy=[r(x) for x in blocked], relates=[], core=True)


def graph(*edges, extra=()):
    I = {}
    for a, b in edges:
        for k in (a, b):
            I.setdefault(k, node(k))
        I[a]["blocks"].append(dict(k=b, st="Backlog", s=b, ext=False))
        I[b]["blockedBy"].append(dict(k=a, st="Backlog", s=a, ext=False))
    for k in extra:
        I.setdefault(k, node(k))
    return I


class Classify(unittest.TestCase):
    def test_kinds(self):
        c = lambda k: topology.classify(k, CFG)
        self.assertEqual(c("DSO-1"), ("pod", "DSO"))
        self.assertEqual(c("REQ-9"), ("interface", "interface"))
        self.assertEqual(c("P1-2"), ("product", "P1"))
        self.assertEqual(c("OTHER-3"), ("external", "OTHER"))  # anything not in config is external


class Layout(unittest.TestCase):
    def test_cross_pod_incoming_goes_left_and_providers_stay_right(self):
        L = topology.layout(graph(("DPE-1", "DSO-1")), CFG)
        self.assertEqual(L["nodes"]["DSO-1"]["side"], "left")    # receives from another POD
        self.assertEqual(L["nodes"]["DPE-1"]["side"], "right")   # only provides

    def test_same_pod_edges_are_not_drawn(self):
        L = topology.layout(graph(("DSO-1", "DSO-2")), CFG)
        self.assertEqual(L["nodes"], {})
        self.assertEqual(L["intra"]["DSO"], 1)

    def test_external_outgoing_sits_under_the_art(self):
        L = topology.layout(graph(("DSO-1", "AIDPG-5")), CFG)
        self.assertEqual(L["nodes"]["AIDPG-5"]["zone"], "ext_out")

    def test_external_incoming_sits_in_the_left_gutter_and_marks_receiver_left(self):
        L = topology.layout(graph(("AIDPG-5", "DSO-1")), CFG)
        self.assertEqual(L["nodes"]["AIDPG-5"]["zone"], "ext_in")
        self.assertEqual(L["nodes"]["DSO-1"]["side"], "left")

    def test_interface_spans_all_pods_and_is_not_incoming(self):
        L = topology.layout(graph(("DSO-1", "REQ-1"), ("REQ-1", "DPE-2")), CFG)
        self.assertEqual(L["nodes"]["REQ-1"]["zone"], "interface")
        self.assertEqual(L["nodes"]["DPE-2"]["side"], "right")

    def test_products_go_in_the_on_the_platform_band(self):
        L = topology.layout(graph(("DSO-1", "P1-1")), CFG)
        self.assertEqual(L["nodes"]["P1-1"]["zone"], "product")

    def test_edges_between_drawn_nodes_only(self):
        L = topology.layout(graph(("DPE-1", "DSO-1"), ("DSO-2", "DSO-3")), CFG)
        self.assertEqual(L["edges"], [("DPE-1", "DSO-1")])


class Render(unittest.TestCase):
    def test_svg_has_bands_lanes_and_clickable_nodes(self):
        s = topology.render(graph(("DPE-1", "DSO-1"), ("DSO-1", "AIDPG-5"), ("DSO-1", "REQ-1")), CFG)
        for t in ("On the platform", "In the platform", "External", "DSO", "DPE", "APE", 'data-key="DSO-1"', "<svg"):
            self.assertIn(t, s["svg"])
        self.assertTrue(s["edges"])

    def test_edges_are_addressable_so_hover_can_hide_unrelated_ones(self):
        svg = topology.render(graph(("DPE-1", "DSO-1")), CFG)["svg"]
        self.assertIn('data-edge="DPE-1|DSO-1"', svg)
        self.assertIn("#p-topology path.dim", topology.CSS)

    def test_svg_is_well_formed_xml(self):
        import xml.dom.minidom
        xml.dom.minidom.parseString(topology.render(graph(("DPE-1", "DSO-1"), ("DSO-1", "AIDPG-5")), CFG)["svg"])

    def test_no_products_is_labelled_not_blank(self):
        cfg = dict(CFG, products=[])
        self.assertIn("no product data yet", topology.render(graph(("DPE-1", "DSO-1")), cfg)["svg"])


class NodeShape(unittest.TestCase):
    """Same information as a Dependencies node: key, summary, status · WSJF · blocks N, external flag, status colour, critical star."""
    def setUp(self):
        I = graph(("DPE-1", "DSO-1"), ("DSO-1", "DSO-2"), ("DSO-1", "AIDPG-5"))
        I["DPE-1"].update(st="Implementing", ws=17.67, sum="Shared actions follow one qualified pipeline contract")
        I["DSO-1"]["ws"] = 9.0
        self.out = topology.render(I, CFG)["svg"]

    def test_meta_line_has_status_wsjf_and_downstream_count(self):
        self.assertIn("Implementing · WSJF 17.67 · blocks 3", self.out)

    def test_summary_is_wrapped_not_dropped(self):
        self.assertIn("Shared actions follow one", self.out)
        self.assertIn("qualified pipeline contract", self.out)

    def test_critical_path_gets_a_star(self):
        self.assertIn("★ DPE-1", self.out)

    def test_status_colours_match_the_dependencies_view(self):
        self.assertIn("#d6f0df", self.out)  # Implementing
        self.assertIn("#e6edf7", self.out)  # Backlog

    def test_external_flag_when_a_link_leaves_the_art(self):
        self.assertIn("EXTERNAL OUT ▶", self.out)


class Pin(unittest.TestCase):
    def setUp(self):
        self.r = topology.render(graph(("DPE-1", "DSO-1"), ("DSO-1", "AIDPG-5"), ("DSO-1", "REQ-1")), CFG)

    def test_spec_places_every_box_in_a_band_and_column(self):
        n = self.r["spec"]["nodes"]
        self.assertEqual(n["DSO-1"]["band"], "lanes")
        self.assertEqual(n["DSO-1"]["col"], "DSO|left")
        self.assertEqual(n["REQ-1"]["band"], "interface")
        self.assertEqual(n["AIDPG-5"]["band"], "ext_out")

    def test_js_exposes_pin_api_and_embeds_spec(self):
        js = topology.js(self.r)
        for t in ("topoToggle", "topoHas", "topoPin", "DSO-1", "direct"):
            self.assertIn(t, js)
        self.assertNotIn("</script", js)

    def test_relayout_clears_stale_hover_dimming(self):
        js = topology.js(self.r)
        self.assertIn("querySelectorAll('.dim').forEach", js)
        self.assertIn("mouseleave", js)

    def test_edge_d_goes_right_to_left_when_target_is_to_the_right(self):
        self.assertTrue(topology.edge_d((0, 0), (500, 100)).startswith("M250"))


class CardLabels(unittest.TestCase):
    def test_groups_by_prefix_and_strips_it(self):
        g = topology.card_groups(["pi-3-26", "kind-enablement", "for-pic", "for-aida", "cap-hosting", "tech-eks"], {})
        self.assertEqual(dict(g), {"Work kind": ["enablement"], "Serves": ["pic", "aida"], "Capability": ["hosting"]})

    def test_config_overrides_groups(self):
        cfg = {"label_groups": [{"prefix": "tech-", "title": "Tech"}]}
        self.assertEqual(topology.card_groups(["tech-eks", "kind-run"], cfg), [("Tech", ["eks"])])

    def test_exact_labels_and_no_match(self):
        cfg = {"label_groups": [{"label": "blocked-external", "title": "Flag"}]}
        self.assertEqual(topology.card_groups(["blocked-external"], cfg), [("Flag", ["blocked-external"])])
        self.assertEqual(topology.card_groups([], cfg), [])


class Config(unittest.TestCase):
    def test_load_json(self):
        import json, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(CFG, f)
        self.assertEqual(topology.load_config(f.name)["art"], "Platform ART")

    def test_all_projects_lists_every_configured_project(self):
        self.assertEqual(sorted(topology.all_projects(CFG)), ["APE", "DPE", "DSO", "P1", "REQ"])


if __name__ == "__main__":
    unittest.main()
