"""Unit tests for the inline SVG icon subset."""
import pytest

from understand_render.icons import icon


def test_icon_is_inline_svg_with_the_material_symbols_viewbox():
    svg = icon("search")
    assert svg.startswith('<svg class="icon"') and 'viewBox="0 -960 960 960"' in svg
    assert svg.count("<path ") == 1 and svg.endswith("</svg>")


def test_icon_is_hidden_from_screen_readers_unless_labelled():
    assert 'aria-hidden="true"' in icon("search")
    labelled = icon("search", label="Search")
    assert 'role="img"' in labelled and 'aria-label="Search"' in labelled
    assert "aria-hidden" not in labelled


def test_unknown_icon_name_is_an_error():
    with pytest.raises(KeyError, match="no-such-icon"):
        icon("no-such-icon")


def test_icon_uses_no_external_reference():
    svg = icon("code")
    assert "http" not in svg.replace("http://www.w3.org/2000/svg", "") and "xlink" not in svg
