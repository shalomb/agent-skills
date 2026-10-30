"""Outer loop for features/report-reading.feature."""
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urldefrag

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import dump_dom, needs_browser, read_json
from pages import Page

scenarios("../../features/report-reading.feature")


@pytest.fixture
def ctx():
    return {}


# --- A report opens without network access -------------------------------

@given("a report on a computer with no network connection")
def _offline_report(ctx, render, fixture_bundle):
    ctx["proc"] = render(fixture_bundle)
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr
    ctx["report"] = ctx["proc"].out_dir / "report.html"


@when("the reader opens the report")
def _open_offline(ctx):
    ctx["dom"] = dump_dom(ctx["report"])


@then("all sections, diagrams, and the graph are shown")
@needs_browser
def _all_shown(ctx):
    dom = ctx["dom"]
    page = Page(dom)
    assert {"overview", "configuration", "glossary"} <= set(page.section_ids)
    assert 'data-fake-mmdc="1"' in dom, "the pre-rendered diagram is missing"
    graph = page.attrs_by_id["graph-canvas"]
    assert graph.get("data-graph-nodes") == "3", graph
    assert graph.get("data-graph-edges") == "2", graph


# --- Citation links ------------------------------------------------------

@given(parsers.parse('the report cites line {line:d} of "{path}"'))
def _cites(ctx, render, fixture_bundle, line, path):
    ctx["proc"] = render(fixture_bundle)
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr
    ctx["cited"] = (path, line)


@when("the reader follows the citation")
def _follow(ctx):
    path, line = ctx["cited"]
    out = ctx["proc"].out_dir
    links = Page.read(out / "report.html").links
    hits = [h for h in links if h.endswith(f"#L{line}") and path in unquote(h)]
    assert hits, f"no link to {path} at line {line} among {links}"
    target, fragment = urldefrag(hits[0])
    ctx["opened"] = out / unquote(target)
    ctx["fragment"] = fragment


@then(parsers.parse('the source view of "{path}" opens at line {line:d}'))
def _opens_at(ctx, path, line):
    view = Page.read(ctx["opened"])
    assert view.attrs_by_id[ctx["fragment"]]["id"] == f"L{line}"
    assert view.attrs_by_id["source-path"]["data-path"] == path


# --- Source view line ids -----------------------------------------------

@given(parsers.parse('the report cites "{path}", which has {count:d} lines'))
def _cites_with_count(ctx, render, fixture_bundle, source_root, path, count):
    assert len((source_root / path).read_text().splitlines()) == count
    ctx["proc"] = render(fixture_bundle)
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr
    ctx["path"] = path
    ctx["count"] = count


@then(parsers.parse('the source view of "{path}" has a link target for each of the {count:d} lines'))
def _line_targets(ctx, path, count):
    view = Page.read(ctx["proc"].out_dir / "src" / f"{path}.html")
    line_ids = [i for i in view.ids if re.fullmatch(r"L\d+", i)]
    assert line_ids == [f"L{n}" for n in range(1, count + 1)]


# --- Anchors for nodes and sections --------------------------------------

@given(parsers.parse('the bundle has a node with the anchor "{node}" and a section with the anchor "{section}"'))
def _bundle_with_anchors(ctx, render, fixture_bundle, node, section):
    ctx["proc"] = render(fixture_bundle)
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr


@then(parsers.parse('the report has a place named "{node}" and a place named "{section}"'))
def _places(ctx, node, section):
    ids = Page.read(ctx["proc"].out_dir / "report.html").ids
    assert node in ids and section in ids


# --- Anchors stable under reordering -------------------------------------

@given(parsers.parse('the function "{symbol}" in "{path}" has an anchor in a first report'))
def _first_report(ctx, render, fixture_bundle, tmp_path, symbol, path):
    ctx["bundle"] = fixture_bundle
    ctx["first"] = render(fixture_bundle, out=tmp_path / "first")
    assert ctx["first"].returncode == 0, ctx["first"].stderr
    ctx["symbol_id"] = f"{path}::{symbol}"


@when("a second report is made after the files are listed in a different order")
def _second_report(ctx, render, tmp_path):
    graph_file = ctx["bundle"] / "graph.json"
    graph = read_json(graph_file)
    graph["nodes"].reverse()
    graph["edges"].reverse()
    import json
    graph_file.write_text(json.dumps(graph))
    ctx["second"] = render(ctx["bundle"], out=tmp_path / "second")
    assert ctx["second"].returncode == 0, ctx["second"].stderr


@then(parsers.parse('the anchor of "{symbol}" is the same in both reports'))
def _same_anchor(ctx, symbol):
    first = read_json(ctx["first"].out_dir / "anchors.json")
    second = read_json(ctx["second"].out_dir / "anchors.json")
    assert ctx["symbol_id"] in first
    assert first[ctx["symbol_id"]] == second[ctx["symbol_id"]]
    for out in (ctx["first"].out_dir, ctx["second"].out_dir):
        assert ctx["symbol_id"] in Page.read(out / "report.html").ids


# --- Anchor index --------------------------------------------------------

@given(parsers.parse('the report has an anchor for the function "{symbol}" in "{path}"'))
def _report_with_function(ctx, render, fixture_bundle, symbol, path):
    ctx["proc"] = render(fixture_bundle)
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr
    ctx["symbol_id"] = f"{path}::{symbol}"


@then(parsers.parse('the anchor index gives the report address, the file, and the line of "{symbol}"'))
def _anchor_index(ctx, symbol):
    index = read_json(ctx["proc"].out_dir / "anchors.json")
    assert index[ctx["symbol_id"]] == {
        "url": "report.html#src/config.ts::parseConfig",
        "path": "src/config.ts",
        "line": 12,
    }
