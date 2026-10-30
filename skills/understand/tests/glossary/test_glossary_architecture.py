# pyright: reportMissingImports=false
"""Architecture tests for /understand glossary (Spec Units 3, 5)."""

import subprocess
from pathlib import Path

from understand_plan.models import Lens
from understand_runs.runner import make_report


def test_report_generation_never_writes_to_target_repository(temp_cache, git_repo):
    """Architecture test: report generation is strictly read-only for target repository."""
    # Record initial files
    initial_files = set(git_repo.rglob("*"))

    result = make_report(git_repo, Lens("full"))
    assert result.run_dir.exists()

    # The repo should have exact same files
    current_files = set(git_repo.rglob("*"))
    assert current_files == initial_files

    # Git working tree must be clean
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=git_repo, text=True
    ).strip()
    assert status == ""


def test_glossary_draft_lives_only_in_shadow_storage(temp_cache, git_repo):
    """Architecture test: glossary draft lives strictly in shadow storage, never in repo."""
    result = make_report(git_repo, Lens("full"))

    assert (result.run_dir / "glossary-draft.md").exists()
    assert not (git_repo / "glossary-draft.md").exists()
    assert not (git_repo / "GLOSSARY.md").exists()
