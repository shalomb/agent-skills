"""Architecture tests for the renderer (spec "Architecture tests"; ADR 0001). Not Gherkin."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import FIXTURES, UNDERSTAND
from pages import Page

EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']\s*(?:https?:)?//|@import|url\(\s*["']?\s*(?:https?:)?//""", re.I)


def module_run(bundle, out, source, mmdc):
    return subprocess.run(
        [sys.executable, "-m", "understand_render", str(bundle), str(out),
         "--source-root", str(source), "--mmdc", str(mmdc)],
        capture_output=True, text=True, cwd=UNDERSTAND / "scripts")


def test_cli_entry_point_renders_a_bundle(tmp_path, fake_mmdc, source_root, fixture_bundle):
    proc = module_run(fixture_bundle, tmp_path / "out", source_root, fake_mmdc)
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "out" / "report.html").is_file()


def test_agents_do_not_write_html__only_the_renderer_output_directory_holds_html(
        tmp_path, fake_mmdc, source_root, fixture_bundle):
    out = tmp_path / "out"
    assert module_run(fixture_bundle, out, source_root, fake_mmdc).returncode == 0
    found = list(tmp_path.rglob("*.html"))
    assert found and all(out in p.parents for p in found)


def test_the_fixture_inputs_hold_no_html():
    assert not list(FIXTURES.rglob("*.html"))


def test_a_bundle_with_html_is_refused_and_nothing_is_written(tmp_path, fake_mmdc, source_root, fixture_bundle):
    (fixture_bundle / "sections" / "page.html").write_text("<p>agent</p>")
    out = tmp_path / "out"
    proc = module_run(fixture_bundle, out, source_root, fake_mmdc)
    assert proc.returncode != 0 and "HTML" in proc.stderr and not out.exists()


@pytest.mark.parametrize("version", [0, 2, "1", None, 99])
def test_unknown_schema_version_is_refused(tmp_path, fake_mmdc, source_root, fixture_bundle, version):
    graph_file = fixture_bundle / "graph.json"
    graph = json.loads(graph_file.read_text())
    graph["schema_version"] = version
    graph_file.write_text(json.dumps(graph))
    out = tmp_path / "out"
    proc = module_run(fixture_bundle, out, source_root, fake_mmdc)
    assert proc.returncode != 0 and "schema_version" in proc.stderr and not out.exists()


def test_a_bundle_without_a_schema_version_is_refused(tmp_path, fake_mmdc, source_root, fixture_bundle):
    graph_file = fixture_bundle / "graph.json"
    graph = json.loads(graph_file.read_text())
    del graph["schema_version"]
    graph_file.write_text(json.dumps(graph))
    proc = module_run(fixture_bundle, tmp_path / "out", source_root, fake_mmdc)
    assert proc.returncode != 0 and "schema_version" in proc.stderr


@pytest.mark.parametrize("mmdc_available", [True, False])
def test_graph_library_is_vendored__no_page_loads_a_script_or_style_by_address(
        tmp_path, fake_mmdc, absent_mmdc, source_root, fixture_bundle, mmdc_available):
    out = tmp_path / "out"
    mmdc = fake_mmdc if mmdc_available else absent_mmdc
    assert module_run(fixture_bundle, out, source_root, mmdc).returncode == 0
    pages = list(out.rglob("*.html"))
    assert len(pages) >= 3
    for path in pages:
        text = path.read_text(encoding="utf-8")
        page = Page(text)
        assert page.script_srcs == [] and page.link_hrefs == [], path
        assert not EXTERNAL.search(text.split("<script", 1)[0]), path
        assert not re.search(r"<(?:script|link|img|iframe)\b[^>]*\b(?:src|href)\s*=\s*[\"']?(?:https?:)?//", text, re.I), path


def test_report_inlines_cytoscape_from_the_vendored_file(tmp_path, fake_mmdc, source_root, fixture_bundle):
    out = tmp_path / "out"
    module_run(fixture_bundle, out, source_root, fake_mmdc)
    assert (UNDERSTAND / "assets" / "vendor" / "cytoscape.min.js").is_file()
    assert "cytoscape" in (out / "report.html").read_text()
