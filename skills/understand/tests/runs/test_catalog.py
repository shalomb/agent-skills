# pyright: reportMissingImports=false
"""Unit tests for understand_runs catalog updater, atomic locking, and SPA deployer (ADR 0004)."""

from __future__ import annotations

import concurrent.futures
import json
import re
from pathlib import Path
from typing import Any

import pytest

from understand_plan.models import Lens
from understand_runs.catalog import (
    REQUIRED_ENTRY_KEYS,
    deploy_catalog_spa,
    update_catalog,
)
from understand_runs.runner import make_report


def _make_sample_entry(
    repo_slug: str = "demo-repo",
    lens: str = "full",
    target: str | None = None,
    run_id: str = "run-001",
    summary: str = "Full overview of demo repo.",
    commit: str | None = "abc1234",
) -> dict[str, Any]:
    return {
        "repo_slug": repo_slug,
        "lens": lens,
        "target": target,
        "run_id": run_id,
        "timestamp": "2026-11-02T12:00:00Z",
        "commit": commit,
        "summary": summary,
        "urls": {
            "parallels": f"http://10.211.55.3:8787/r/understand/{repo_slug}/{lens}/{run_id}/",
            "tailnet": f"http://100.99.83.53:8787/r/understand/{repo_slug}/{lens}/{run_id}/",
        },
        "report_rel_url": f"{repo_slug}/{lens}/{run_id}/report.html",
    }


def test_catalog_entry_validation_missing_keys(tmp_path: Path):
    entry = _make_sample_entry()
    del entry["summary"]
    with pytest.raises(ValueError, match="missing required keys"):
        update_catalog(tmp_path, entry)


def test_catalog_entry_validation_invalid_types(tmp_path: Path):
    entry = _make_sample_entry()
    entry["repo_slug"] = 12345  # type: ignore
    with pytest.raises(TypeError, match="repo_slug"):
        update_catalog(tmp_path, entry)

    entry = _make_sample_entry()
    entry["urls"] = "http://example.com"  # type: ignore
    with pytest.raises(TypeError, match="urls"):
        update_catalog(tmp_path, entry)


def test_catalog_entry_appending_and_schema(tmp_path: Path):
    entry1 = _make_sample_entry(repo_slug="service-a", run_id="r1")
    catalog_file = update_catalog(tmp_path, entry1)

    assert catalog_file.exists()
    assert catalog_file == tmp_path / "understand" / "catalog.json"

    data = json.loads(catalog_file.read_text(encoding="utf-8"))
    entries = data if isinstance(data, list) else data.get("runs", [])
    assert len(entries) == 1
    assert entries[0]["repo_slug"] == "service-a"
    assert entries[0]["run_id"] == "r1"
    assert set(entries[0].keys()) == REQUIRED_ENTRY_KEYS

    # Append second entry
    entry2 = _make_sample_entry(repo_slug="service-b", lens="topic", target="auth", run_id="r2")
    update_catalog(tmp_path, entry2)

    data_after = json.loads(catalog_file.read_text(encoding="utf-8"))
    entries_after = data_after if isinstance(data_after, list) else data_after.get("runs", [])
    assert len(entries_after) == 2
    assert entries_after[0]["run_id"] == "r1"
    assert entries_after[1]["run_id"] == "r2"
    assert entries_after[1]["target"] == "auth"


def test_catalog_entry_updating_existing_record(tmp_path: Path):
    entry1 = _make_sample_entry(repo_slug="service-a", run_id="r1", summary="Initial summary")
    update_catalog(tmp_path, entry1)

    updated_entry = _make_sample_entry(
        repo_slug="service-a", run_id="r1", summary="Updated summary with new analysis"
    )
    catalog_file = update_catalog(tmp_path, updated_entry)

    data = json.loads(catalog_file.read_text(encoding="utf-8"))
    entries = data if isinstance(data, list) else data.get("runs", [])
    assert len(entries) == 1
    assert entries[0]["summary"] == "Updated summary with new analysis"


def test_catalog_path_when_already_understand_dir(tmp_path: Path):
    understand_dir = tmp_path / "understand"
    understand_dir.mkdir()

    entry = _make_sample_entry(run_id="r-direct")
    catalog_file = update_catalog(understand_dir, entry)

    # Must write to understand_dir / "catalog.json", not understand / understand
    assert catalog_file == understand_dir / "catalog.json"
    assert not (understand_dir / "understand").exists()


def test_concurrency_locking_and_atomic_write(tmp_path: Path):
    num_workers = 15
    entries = [_make_sample_entry(repo_slug=f"repo-{i}", run_id=f"run-{i}") for i in range(num_workers)]

    def worker_task(entry: dict[str, Any]) -> None:
        update_catalog(tmp_path, entry)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker_task, e) for e in entries]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    catalog_path = tmp_path / "understand" / "catalog.json"
    assert catalog_path.exists()
    lock_path = tmp_path / "understand" / "catalog.json.lock"
    assert lock_path.exists()

    # Verify no temp files left behind
    tmp_files = list((tmp_path / "understand").glob(".tmp-catalog-*"))
    assert tmp_files == []

    # Verify all records saved and valid JSON
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    saved_runs = data if isinstance(data, list) else data.get("runs", [])
    assert len(saved_runs) == num_workers
    saved_ids = {r["run_id"] for r in saved_runs}
    assert saved_ids == {f"run-{i}" for i in range(num_workers)}


def test_deploy_catalog_spa_content(tmp_path: Path):
    index_file = deploy_catalog_spa(tmp_path)
    assert index_file.exists()
    assert index_file == tmp_path / "understand" / "index.html"

    html = index_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "Understand Reports Catalog" in html
    assert "--md-sys-color-primary" in html
    assert "prefers-color-scheme: dark" in html
    assert "data-theme" in html

    # Search input element
    assert 'id="catalog-search"' in html
    assert 'type="search"' in html

    # Fetch catalog.json
    assert "./catalog.json" in html

    # Empty state handling
    assert "empty-state" in html

    # Pure vanilla: no external CDN scripts or remote links
    assert not re.search(r'<script[^>]+src=["\']https?://', html)
    assert not re.search(r'<link[^>]+href=["\']https?://', html)


def test_runner_records_catalog_and_deploys_spa(temp_cache: Path, git_repo: Path):
    result = make_report(git_repo, Lens("full"))
    assert result.run_dir.exists()

    understand_dir = temp_cache / "agent-skills" / "understand"
    catalog_path = understand_dir / "catalog.json"
    index_path = understand_dir / "index.html"

    assert catalog_path.exists(), "catalog.json must be created in understand root"
    assert index_path.exists(), "index.html must be deployed in understand root"

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    runs = data if isinstance(data, list) else data.get("runs", [])
    assert len(runs) >= 1

    last_run = next(r for r in runs if r["run_id"] == result.run_dir.name)
    assert last_run["lens"] == "full"
    assert "report.html" in last_run["report_rel_url"]
    assert "parallels" in last_run["urls"]
    assert "tailnet" in last_run["urls"]
