"""Command line: python -m understand_render BUNDLE_DIR OUT_DIR --source-root DIR."""
import argparse
import shutil
import sys

from .bundle import BundleError
from .run import render_run

DEFAULT_CHROMIUM = "/usr/bin/chromium-headless-shell"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="understand_render", description="Render an /understand bundle into a report.")
    parser.add_argument("bundle_dir", help="directory with graph.json, sections/, and optional anchors.json and glossary.json")
    parser.add_argument("out_dir", help="directory to write report.html, src/, anchors.json and render.log into")
    parser.add_argument("--source-root", default=None, help="repository root that cited paths are read from")
    parser.add_argument("--mmdc", default=shutil.which("mmdc") or "mmdc", help="path to mmdc (default: from PATH)")
    parser.add_argument("--chromium", default=shutil.which("chromium-headless-shell") or DEFAULT_CHROMIUM,
                        help="path to chromium-headless-shell")
    args = parser.parse_args(argv)

    def log(message):
        print(message, file=sys.stderr)

    try:
        render_run(args.bundle_dir, args.source_root, args.out_dir,
                   mmdc_path=args.mmdc, chromium_path=args.chromium, log=log)
    except BundleError as exc:
        log(f"bundle refused: {exc}")
        return 1
    return 0
