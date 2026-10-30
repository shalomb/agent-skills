"""Unit tests for anchor id derivation (spec unit 5)."""
import pytest

from understand_render.anchors import node_anchor_id, section_anchor_id, source_view_href


def test_file_node_anchor_is_its_path():
    assert node_anchor_id("src/app.ts", None) == "src/app.ts"


def test_symbol_node_anchor_is_path_and_symbol():
    assert node_anchor_id("src/config.ts", "parseConfig") == "src/config.ts::parseConfig"


def test_node_anchor_does_not_depend_on_position_or_label():
    # Derivation takes only path and symbol, so no list order can reach it.
    assert node_anchor_id("a/b.py", "f") == node_anchor_id("a/b.py", "f")
    assert node_anchor_id("a/b.py", "f") != node_anchor_id("a/b.py", "g")
    assert node_anchor_id("a/b.py", "f") != node_anchor_id("a/c.py", "f")


@pytest.mark.parametrize("filename, expected", [
    ("01-overview.md", "overview"),
    ("overview.md", "overview"),
    ("10_data-flow.md", "data-flow"),
    ("2-Auth Layer.md", "auth-layer"),
])
def test_section_anchor_comes_from_the_file_name_without_the_order_prefix(filename, expected):
    assert section_anchor_id(filename) == expected


def test_reordering_sections_by_renumbering_keeps_the_anchor():
    assert section_anchor_id("01-overview.md") == section_anchor_id("07-overview.md")


def test_source_view_href_points_at_the_line():
    assert source_view_href("src/app.ts", 42) == "src/src/app.ts.html#L42"


def test_source_view_href_without_line_opens_the_top():
    assert source_view_href("src/app.ts", None) == "src/src/app.ts.html"
