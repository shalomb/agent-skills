"""Architecture test: the graph and diagram libraries are vendored with their licences."""
import json
from pathlib import Path

import pytest

ASSETS = Path(__file__).resolve().parents[2] / "assets"
VENDOR = ASSETS / "vendor"


@pytest.mark.parametrize("library, marker", [
    ("cytoscape", "cytoscape"),
    ("mermaid", "mermaid"),
])
def test_library_is_vendored_with_its_licence(library, marker):
    code = (VENDOR / f"{library}.min.js").read_text(encoding="utf-8")
    assert marker in code
    assert "MIT" in (VENDOR / f"{library}.LICENSE").read_text(encoding="utf-8")


def test_material_symbols_licence_is_kept_with_the_icons():
    assert "Apache License" in (VENDOR / "material-symbols.LICENSE").read_text(encoding="utf-8")


def test_icon_subset_is_small_and_made_of_svg_paths():
    icons = json.loads((ASSETS / "icons.json").read_text(encoding="utf-8"))
    assert 8 <= len(icons["paths"]) <= 60
    assert all(d[0] in "Mm" for d in icons["paths"].values())


def test_no_icon_font_file_is_shipped():
    fonts = [p for p in ASSETS.rglob("*") if p.suffix in {".woff", ".woff2", ".ttf", ".otf", ".eot"}]
    assert fonts == []
