"""Inline SVG icons from the Material Symbols subset in assets/icons.json."""
import html
import json
from functools import lru_cache
from pathlib import Path

ICONS_FILE = Path(__file__).resolve().parents[2] / "assets" / "icons.json"


@lru_cache(maxsize=1)
def _subset():
    return json.loads(ICONS_FILE.read_text(encoding="utf-8"))


def icon(name, label=None):
    """An inline `<svg>` for `name`. Decorative unless `label` is given."""
    subset = _subset()
    if name not in subset["paths"]:
        raise KeyError(name)
    access = (f'role="img" aria-label="{html.escape(label)}"' if label else 'aria-hidden="true"')
    return (f'<svg class="icon" viewBox="{subset["viewBox"]}" width="24" height="24" {access}>'
            f'<path d="{subset["paths"][name]}"/></svg>')
