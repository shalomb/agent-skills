"""Unit tests for Mermaid pre-render with mmdc and the in-page fallback."""
import json
import shutil
import stat
from pathlib import Path

import pytest

from understand_render.diagrams import DiagramRenderer, puppeteer_config

CHROMIUM = "/usr/bin/chromium-headless-shell"
FLOW = "flowchart LR\n  A --> B"


def script(tmp_path, name, body):
    path = tmp_path / name
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


@pytest.fixture
def recording_mmdc(tmp_path):
    """Records its arguments, the puppeteer config and the diagram source, then draws an SVG."""
    return script(tmp_path, "mmdc-recording", f'''
echo "$@" > "{tmp_path}/args.txt"
while [ $# -gt 0 ]; do
  case "$1" in -i) in="$2"; shift;; -o) out="$2"; shift;; -p) cfg="$2"; shift;; esac
  shift
done
cp "$cfg" "{tmp_path}/puppeteer.json"
cp "$in" "{tmp_path}/source.mmd"
printf '<?xml version="1.0"?><svg id="x"><g/></svg>' > "$out"
''')


def test_puppeteer_config_names_the_system_chromium_and_safe_flags():
    assert puppeteer_config(CHROMIUM) == {
        "executablePath": CHROMIUM, "args": ["--no-sandbox", "--disable-gpu"]}


def test_mmdc_is_given_the_diagram_source_and_the_puppeteer_config(tmp_path, recording_mmdc):
    log = []
    DiagramRenderer(str(recording_mmdc), CHROMIUM, log.append).render(FLOW)
    assert (tmp_path / "source.mmd").read_text() == FLOW
    assert json.loads((tmp_path / "puppeteer.json").read_text()) == puppeteer_config(CHROMIUM)


def test_prerendered_diagram_is_inline_svg_without_xml_prolog(tmp_path, recording_mmdc):
    renderer = DiagramRenderer(str(recording_mmdc), CHROMIUM, [].append)
    html = renderer.render(FLOW)
    assert html.startswith('<figure class="diagram">') and "<svg" in html
    assert "<?xml" not in html
    assert renderer.fallback_count == 0


def test_each_diagram_gets_its_own_svg_id(tmp_path, recording_mmdc):
    renderer = DiagramRenderer(str(recording_mmdc), CHROMIUM, [].append)
    renderer.render(FLOW)
    first = (tmp_path / "args.txt").read_text()
    renderer.render(FLOW)
    assert (tmp_path / "args.txt").read_text() != first


def test_absent_mmdc_falls_back_and_logs(tmp_path):
    log = []
    renderer = DiagramRenderer(str(tmp_path / "missing"), CHROMIUM, log.append)
    html = renderer.render(FLOW)
    assert '<pre class="mermaid">flowchart LR\n  A --&gt; B</pre>' in html
    assert renderer.fallback_count == 1 and renderer.total == 1
    assert any("mmdc" in line and "not found" in line for line in log)


def test_failing_mmdc_falls_back_and_logs_its_message(tmp_path):
    bad = script(tmp_path, "mmdc-bad", 'echo "Parse error on line 2" >&2\nexit 1\n')
    log = []
    renderer = DiagramRenderer(str(bad), CHROMIUM, log.append)
    html = renderer.render(FLOW)
    assert 'class="mermaid"' in html
    assert any("Parse error on line 2" in line for line in log)


def test_mmdc_that_writes_no_file_falls_back(tmp_path):
    silent = script(tmp_path, "mmdc-silent", "exit 0\n")
    renderer = DiagramRenderer(str(silent), CHROMIUM, [].append)
    assert 'class="mermaid"' in renderer.render(FLOW)


def test_mmdc_that_hangs_falls_back_after_the_timeout(tmp_path):
    hang = script(tmp_path, "mmdc-hang", "sleep 30\n")
    log = []
    renderer = DiagramRenderer(str(hang), CHROMIUM, log.append, timeout=0.3)
    assert 'class="mermaid"' in renderer.render(FLOW)
    assert any("timed out" in line for line in log)


def test_missing_chromium_falls_back_without_calling_mmdc(tmp_path, recording_mmdc):
    log = []
    renderer = DiagramRenderer(str(recording_mmdc), str(tmp_path / "no-chromium"), log.append)
    assert 'class="mermaid"' in renderer.render(FLOW)
    assert not (tmp_path / "args.txt").exists()
    assert any("chromium" in line for line in log)


def test_diagram_source_cannot_inject_markup_in_the_fallback(tmp_path):
    renderer = DiagramRenderer(str(tmp_path / "missing"), CHROMIUM, [].append)
    assert "<script>" not in renderer.render("flowchart LR\n  A[<script>x</script>] --> B")


def test_summary_line_says_diagrams_were_drawn_in_the_page(tmp_path):
    log = []
    renderer = DiagramRenderer(str(tmp_path / "missing"), CHROMIUM, log.append)
    renderer.render(FLOW)
    renderer.render(FLOW)
    renderer.log_summary()
    assert log[-1] == "diagrams drawn in the page: 2 of 2 (mmdc could not draw them ahead of time)"


def test_summary_is_silent_when_every_diagram_was_prerendered(recording_mmdc):
    log = []
    renderer = DiagramRenderer(str(recording_mmdc), CHROMIUM, log.append)
    renderer.render(FLOW)
    renderer.log_summary()
    assert log == ["diagrams drawn ahead of time: 1 of 1"]


@pytest.mark.mmdc
@pytest.mark.skipif(not (shutil.which("mmdc") and Path(CHROMIUM).exists()), reason="mmdc or chromium-headless-shell missing")
def test_real_mmdc_draws_an_svg_with_the_system_chromium():
    renderer = DiagramRenderer(shutil.which("mmdc"), CHROMIUM, [].append)
    html = renderer.render(FLOW)
    assert "<svg" in html and renderer.fallback_count == 0
    assert "A" in html and "B" in html
