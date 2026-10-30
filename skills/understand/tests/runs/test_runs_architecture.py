# pyright: reportMissingImports=false
"""Architecture tests for understand_runs (spec.md Architecture tests)."""

from pathlib import Path
import todo_navigator.parser as todo_parser
from understand_runs.slug import get_repo_slug


def test_repo_slug_equals_todo_navigator():
    """Rule: repo_slug equals todo-navigator's (Unit test: both call the same slug function on one path)."""
    p = Path("/media/psf/Home/projects/shalomb/agent-skills")
    assert get_repo_slug(p) == todo_parser.get_repo_slug(p)
