"""The index page of one repository: every lens with its runs, newest first."""
import html
from pathlib import Path

from .icons import icon
from .page import page


def write_repo_index(repo_dir, repo_name):
    """Write `index.html` in `repo_dir`, listing `<lens>/<run>/report.html`."""
    repo_dir = Path(repo_dir)
    lenses = []
    for lens_dir in sorted(p for p in repo_dir.iterdir() if p.is_dir() and not p.is_symlink()):
        reports = [r for r in lens_dir.glob("*/report.html") if not r.parent.is_symlink()]
        reports.sort(key=lambda r: (-r.stat().st_mtime, r.parent.name))
        if reports:
            lenses.append((lens_dir.name, reports))
    body = "".join(_lens_block(repo_dir, name, reports) for name, reports in lenses)
    if not body:
        body = '<p class="notice">No reports yet.</p>'
    header = (f'<header class="masthead"><p class="eyebrow">{icon("folder")} Understand</p>'
              f'<h1>{html.escape(repo_name)}</h1><p>Reports of this repository</p></header>')
    (repo_dir / "index.html").write_text(
        page(f"{repo_name}: reports", f'<div class="wrap">{header}<article>{body}</article></div>'),
        encoding="utf-8")


def _lens_block(repo_dir, name, reports):
    items = "".join(
        f'<li><a href="{html.escape(r.relative_to(repo_dir).as_posix())}">{html.escape(r.parent.name)}</a></li>'
        for r in reports)
    return f"<h2>{html.escape(name)}</h2><ul class=\"entries\">{items}</ul>"
