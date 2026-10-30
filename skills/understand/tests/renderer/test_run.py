"""Unit tests for the render run: files written, anchors index, log, refusal."""
import json
import shutil
from pathlib import Path

import pytest

from understand_render.bundle import BundleError
from understand_render.run import render_run

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def run(tmp_path, fake_mmdc):
    def go(bundle=FIXTURES / "bundle-basic", source=FIXTURES / "source-basic", mmdc=None, out=None):
        lines = []
        out = out or tmp_path / "out"
        render_run(bundle, source, out, mmdc_path=str(mmdc or fake_mmdc),
                   chromium_path="/usr/bin/chromium-headless-shell", log=lines.append)
        return out, lines
    return go


def test_writes_report_source_views_anchors_and_log(run):
    out, _ = run()
    written = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert written == ["anchors.json", "render.log", "report.html", "src/src/app.ts.html", "src/src/config.ts.html"]


def test_only_html_under_the_output_directory_is_written(run, tmp_path):
    out, _ = run()
    html_files = {p for p in tmp_path.rglob("*.html")}
    assert html_files and all(out in p.parents for p in html_files)


def test_anchors_index_has_url_path_and_line_for_nodes_and_cited_places(run):
    out, _ = run()
    index = json.loads((out / "anchors.json").read_text())
    assert index["src/config.ts::parseConfig"] == {
        "url": "report.html#src/config.ts::parseConfig", "path": "src/config.ts", "line": 12}
    assert index["src/app.ts"]["line"] == 1
    assert index["src/app.ts:entry-call"] == {
        "url": "report.html#src/app.ts:entry-call", "path": "src/app.ts", "line": 42}


def test_a_markdown_link_to_a_source_file_opens_its_source_view(run):
    out, _ = run()
    html = (out / "report.html").read_text()
    assert 'href="src/src/app.ts.html#L42"' in html


def test_source_view_of_a_missing_file_says_so(run, tmp_path):
    empty = tmp_path / "empty-source"
    empty.mkdir()
    out, _ = run(source=empty)
    assert "not available" in (out / "src" / "src" / "app.ts.html").read_text()


def test_source_view_links_back_to_the_report_from_its_depth(run):
    out, _ = run()
    assert 'href="../../report.html"' in (out / "src" / "src" / "app.ts.html").read_text()


def test_refused_bundle_writes_nothing(run, tmp_path):
    bad = tmp_path / "bad"
    shutil.copytree(FIXTURES / "bundle-basic", bad)
    graph = json.loads((bad / "graph.json").read_text())
    graph["schema_version"] = 99
    (bad / "graph.json").write_text(json.dumps(graph))
    with pytest.raises(BundleError, match="schema_version"):
        run(bundle=bad)
    assert not (tmp_path / "out").exists()


def test_log_records_that_diagrams_were_drawn_ahead_of_time(run):
    out, lines = run()
    assert any("drawn ahead of time" in line for line in lines)
    assert "drawn ahead of time" in (out / "render.log").read_text()


def test_a_source_path_that_climbs_out_of_the_root_is_not_read(run, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret")
    (tmp_path / "source").mkdir()
    (tmp_path / "source" / "link.ts").symlink_to(secret)
    bundle = tmp_path / "b"
    shutil.copytree(FIXTURES / "bundle-basic", bundle)
    anchors = {"x": {"path": "link.ts", "line": 1}}
    (bundle / "anchors.json").write_text(json.dumps(anchors))
    out, _ = run(bundle=bundle, source=tmp_path / "source")
    view = (out / "src" / "link.ts.html").read_text()
    assert "top secret" not in view and "not available" in view
