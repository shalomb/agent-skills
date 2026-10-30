"""Mermaid diagrams: pre-render to inline SVG with mmdc, else draw them in the page.

The fallback is a `<pre class="mermaid">` block that the vendored in-page
Mermaid turns into an SVG when the report opens. Every fallback is logged.
"""
import html
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 60


def puppeteer_config(chromium_path):
    return {"executablePath": chromium_path, "args": ["--no-sandbox", "--disable-gpu"]}


class DiagramRenderer:
    def __init__(self, mmdc_path, chromium_path, log, timeout=DEFAULT_TIMEOUT_SECONDS):
        self.mmdc_path = mmdc_path
        self.chromium_path = chromium_path
        self.log = log
        self.timeout = timeout
        self.total = 0
        self.fallback_count = 0

    def render(self, source):
        """HTML for one diagram: inline SVG when mmdc works, else an in-page block."""
        self.total += 1
        number = self.total
        svg = self._prerender(source, f"diagram-{number}")
        if svg is None:
            self.fallback_count += 1
            return f'<figure class="diagram"><pre class="mermaid">{html.escape(source, quote=False)}</pre></figure>'
        return f'<figure class="diagram">{svg}</figure>'

    def log_summary(self):
        if self.fallback_count:
            self.log(f"diagrams drawn in the page: {self.fallback_count} of {self.total} "
                     "(mmdc could not draw them ahead of time)")
        elif self.total:
            self.log(f"diagrams drawn ahead of time: {self.total} of {self.total}")

    def uses_in_page_mermaid(self):
        return self.fallback_count > 0

    def _prerender(self, source, svg_id):
        if not os.path.exists(self.chromium_path):
            self.log(f"chromium not found at {self.chromium_path}; {svg_id} falls back to the page")
            return None
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src, out, cfg = tmp_path / "in.mmd", tmp_path / "out.svg", tmp_path / "puppeteer.json"
            src.write_text(source, encoding="utf-8")
            cfg.write_text(json.dumps(puppeteer_config(self.chromium_path)), encoding="utf-8")
            command = [self.mmdc_path, "-i", str(src), "-o", str(out), "-p", str(cfg),
                       "-I", svg_id, "-b", "transparent", "-q"]
            try:
                proc = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout)
            except FileNotFoundError:
                self.log(f"mmdc not found ({self.mmdc_path}); {svg_id} falls back to the page")
                return None
            except subprocess.TimeoutExpired:
                self.log(f"mmdc timed out after {self.timeout}s; {svg_id} falls back to the page")
                return None
            if proc.returncode != 0:
                message = (proc.stderr or proc.stdout).strip().splitlines()
                self.log(f"mmdc failed for {svg_id}: {message[0] if message else 'no message'}")
                return None
            if not out.is_file():
                self.log(f"mmdc wrote no file for {svg_id}; it falls back to the page")
                return None
            return re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", out.read_text(encoding="utf-8"))
