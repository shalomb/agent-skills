"""Unit tests for bundle loading and schema validation (spec unit 3, ADR 0001)."""
import json
import shutil
from pathlib import Path

import pytest

from understand_render.bundle import BundleError, SCHEMA_VERSION, load_bundle

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "bundle-basic"


@pytest.fixture
def bundle(tmp_path):
    dest = tmp_path / "b"
    shutil.copytree(FIXTURE, dest)
    return dest


def edit_graph(bundle, change):
    path = bundle / "graph.json"
    graph = json.loads(path.read_text())
    change(graph)
    path.write_text(json.dumps(graph))


def test_fixture_bundle_loads(bundle):
    loaded = load_bundle(bundle)
    assert [n.anchor_id for n in loaded.nodes] == [
        "src/app.ts", "src/config.ts", "src/config.ts::parseConfig"]
    assert [s.anchor_id for s in loaded.sections] == ["overview", "configuration"]
    assert loaded.title == "Fixture app"


def test_schema_version_is_one():
    assert SCHEMA_VERSION == 1


@pytest.mark.parametrize("version", [0, 2, 99, "1", None])
def test_unknown_schema_version_is_refused(bundle, version):
    edit_graph(bundle, lambda g: g.update(schema_version=version))
    with pytest.raises(BundleError, match="schema_version"):
        load_bundle(bundle)


def test_missing_schema_version_is_refused(bundle):
    edit_graph(bundle, lambda g: g.pop("schema_version"))
    with pytest.raises(BundleError, match="schema_version"):
        load_bundle(bundle)


def test_node_without_path_is_refused_and_named(bundle):
    edit_graph(bundle, lambda g: g["nodes"][1].pop("path"))
    with pytest.raises(BundleError) as err:
        load_bundle(bundle)
    message = str(err.value)
    assert "Config module" in message
    assert "nodes[1]" in message
    assert "path" in message


def test_node_without_label_is_named_by_position(bundle):
    edit_graph(bundle, lambda g: g["nodes"][0].pop("label"))
    with pytest.raises(BundleError, match=r"nodes\[0\].*label"):
        load_bundle(bundle)


def test_node_with_non_integer_line_is_refused(bundle):
    edit_graph(bundle, lambda g: g["nodes"][2].update(line="twelve"))
    with pytest.raises(BundleError, match=r"parseConfig.*line"):
        load_bundle(bundle)


def test_edge_to_unknown_node_is_refused(bundle):
    edit_graph(bundle, lambda g: g["edges"][0].update(target="src/nope.ts"))
    with pytest.raises(BundleError, match=r"edges\[0\].*src/nope.ts"):
        load_bundle(bundle)


def test_two_nodes_with_one_anchor_are_refused(bundle):
    edit_graph(bundle, lambda g: g["nodes"].append(dict(g["nodes"][0], label="Again")))
    with pytest.raises(BundleError, match="src/app.ts.*twice|duplicate"):
        load_bundle(bundle)


def test_missing_graph_file_is_refused(bundle):
    (bundle / "graph.json").unlink()
    with pytest.raises(BundleError, match="graph.json"):
        load_bundle(bundle)


def test_graph_that_is_not_json_is_refused(bundle):
    (bundle / "graph.json").write_text("{not json")
    with pytest.raises(BundleError, match="graph.json"):
        load_bundle(bundle)


def test_bundle_without_sections_is_refused(bundle):
    for f in (bundle / "sections").iterdir():
        f.unlink()
    with pytest.raises(BundleError, match="sections"):
        load_bundle(bundle)


@pytest.mark.parametrize("name", ["glossary", "graph"])
def test_section_with_a_name_the_renderer_owns_is_refused(bundle, name):
    (bundle / "sections" / f"99-{name}.md").write_text("# Mine\n")
    with pytest.raises(BundleError, match=f"{name}.*renderer"):
        load_bundle(bundle)


@pytest.mark.parametrize("bad", ["../secret.txt", "/etc/passwd", "src/../../x", "a\\b.ts", ""])
def test_node_path_that_leaves_the_source_root_is_refused(bundle, bad):
    edit_graph(bundle, lambda g: g["nodes"][0].update(path=bad))
    with pytest.raises(BundleError, match=r"nodes\[0\].*path"):
        load_bundle(bundle)


def test_glossary_and_anchors_files_are_optional(bundle):
    (bundle / "glossary.json").unlink()
    (bundle / "anchors.json").unlink()
    loaded = load_bundle(bundle)
    assert loaded.glossary_contexts == [] and loaded.extra_anchors == {}


def test_glossary_term_without_meaning_is_refused_and_named(bundle):
    (bundle / "glossary.json").write_text(json.dumps(
        {"contexts": [{"name": "runtime", "terms": [{"term": "Config"}]}]}))
    with pytest.raises(BundleError, match=r"Config.*meaning"):
        load_bundle(bundle)


def test_anchor_entry_without_line_is_refused_and_named(bundle):
    (bundle / "anchors.json").write_text(json.dumps({"x": {"path": "src/app.ts"}}))
    with pytest.raises(BundleError, match=r"anchors.json.*x.*line"):
        load_bundle(bundle)


def test_sections_are_ordered_by_file_name(bundle):
    (bundle / "sections" / "00-intro.md").write_text("# Intro\n")
    assert [s.anchor_id for s in load_bundle(bundle).sections][0] == "intro"


def test_cited_files_cover_nodes_and_anchors(bundle):
    assert load_bundle(bundle).cited_paths() == ["src/app.ts", "src/config.ts"]


def test_section_keeps_its_file_name_for_the_anchor_index(bundle):
    assert [s.filename for s in load_bundle(bundle).sections] == ["01-overview.md", "02-configuration.md"]


def test_html_file_in_the_bundle_is_refused_because_agents_do_not_write_html(bundle):
    (bundle / "sections" / "extra.html").write_text("<p>hi</p>")
    with pytest.raises(BundleError, match=r"extra.html.*HTML"):
        load_bundle(bundle)
