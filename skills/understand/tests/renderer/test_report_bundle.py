"""Outer loop for features/report-bundle.feature."""
import json

import pytest
from pytest_bdd import given, scenarios, then, when

from conftest import dump_dom, needs_browser, read_json
from pages import Page

scenarios("../../features/report-bundle.feature")


@pytest.fixture
def ctx():
    return {}


@given("a bundle where a graph node has no path")
def _node_without_path(ctx, fixture_bundle):
    graph_file = fixture_bundle / "graph.json"
    graph = read_json(graph_file)
    for node in graph["nodes"]:
        if node["label"] == "Config module":
            del node["path"]
    graph_file.write_text(json.dumps(graph))
    ctx["bundle"] = fixture_bundle


@given("diagrams cannot be drawn ahead of time on this computer")
def _no_mmdc(ctx, fixture_bundle, absent_mmdc):
    ctx["bundle"] = fixture_bundle
    ctx["mmdc"] = absent_mmdc


@when("the renderer runs")
def _run(ctx, render):
    ctx["proc"] = render(ctx["bundle"], mmdc=ctx.get("mmdc"))


@when("a report is made")
def _make_report(ctx, render, fixture_bundle):
    ctx["proc"] = render(fixture_bundle)
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr


@then("no report is made")
def _no_report(ctx):
    assert ctx["proc"].returncode != 0
    out = ctx["proc"].out_dir
    assert not list(out.rglob("*.html")) if out.exists() else True


@then("the run says which node has no path")
def _names_node(ctx):
    assert "Config module" in ctx["proc"].stderr
    assert "path" in ctx["proc"].stderr


@then("the report shows each diagram")
@needs_browser
def _each_diagram(ctx):
    assert ctx["proc"].returncode == 0, ctx["proc"].stderr
    dom = dump_dom(ctx["proc"].out_dir / "report.html")
    overview = dom.split('id="overview"', 1)[1].split("</section>", 1)[0]
    assert "<svg" in overview, "the in-page renderer drew no diagram"


@then("the run log says that diagrams were drawn in the page")
def _log_says(ctx):
    assert "diagrams drawn in the page" in ctx["proc"].stderr
    log = (ctx["proc"].out_dir / "render.log").read_text()
    assert "diagrams drawn in the page" in log


@then("the glossary is the last section of the report")
def _glossary_last(ctx):
    page = Page.read(ctx["proc"].out_dir / "report.html")
    assert page.section_ids[-1] == "glossary"
    assert page.section_ids.count("glossary") == 1
