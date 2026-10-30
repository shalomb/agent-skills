# pyright: reportMissingImports=false
"""Unit tests for runner integration of glossary extraction (Step 6)."""

import json
import subprocess
from pathlib import Path

from understand_plan.models import Lens
from understand_runs.runner import make_report


def test_runner_converge_populates_glossary_json_and_draft_in_run_dir(temp_cache, git_repo):
    map_file = git_repo / "GLOSSARY-MAP.md"
    map_file.write_text(
        "## billing\n"
        "**Invoice**: Bill sent to customer.\n"
        "**Account**: Payer of invoices.\n\n"
        "## identity\n"
        "**Account**: Login principal.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "add glossary map"], cwd=git_repo, check=True)

    result = make_report(git_repo, Lens("full"))
    assert result.run_dir.exists()

    # glossary.json should exist in run_dir (shadow storage)
    glossary_json = result.run_dir / "glossary.json"
    assert glossary_json.exists(), "glossary.json was not created in shadow run_dir"
    data = json.loads(glossary_json.read_text(encoding="utf-8"))
    assert "contexts" in data
    assert {c["name"] for c in data["contexts"]} == {"billing", "identity"}

    # glossary-draft.md should exist in run_dir
    draft_file = result.run_dir / "glossary-draft.md"
    assert draft_file.exists(), "glossary-draft.md was not created in shadow run_dir"
    draft_content = draft_file.read_text(encoding="utf-8")
    assert "# Glossary" in draft_content
    assert "billing" in draft_content

    # Target repository must NOT have any new files or changes from report generation
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=git_repo, text=True).strip()
    assert status == "", f"Target repository was mutated by report run: {status}"


def test_runner_preserves_zero_mutation_when_no_glossary_exists(temp_cache, git_repo):
    result = make_report(git_repo, Lens("full"))
    assert result.run_dir.exists()

    # Draft offered in shadow storage
    draft_file = result.run_dir / "glossary-draft.md"
    assert draft_file.exists()

    # No files written to git_repo
    assert not (git_repo / "GLOSSARY.md").exists()
    assert not (git_repo / "glossary-draft.md").exists()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=git_repo, text=True).strip()
    assert status == ""
