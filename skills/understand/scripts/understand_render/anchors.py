"""Anchor ids: stable names for nodes and sections, derived from path and symbol."""
import re

SYMBOL_SEPARATOR = "::"


def node_anchor_id(path, symbol):
    """The id of a graph node. Only path and symbol feed it, never list order."""
    return f"{path}{SYMBOL_SEPARATOR}{symbol}" if symbol else path


def section_anchor_id(filename):
    """The id of a section: its file name without extension and order prefix."""
    stem = re.sub(r"\.md$", "", filename)
    stem = re.sub(r"^\d+[-_]", "", stem)
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def source_view_href(path, line):
    """Report-relative address of the source view of `path`, at `line` if given."""
    href = f"src/{path}.html"
    return f"{href}#L{line}" if line else href
