# pyright: reportMissingImports=false
"""BDD step definitions for skills/understand/features/report-runs.feature."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

import todo_navigator.parser as todo_parser
from understand_runs.slug import get_repo_slug
from understand_runs.storage import (
    create_run_dir,
    get_latest_run,
    get_lens_dir,
    get_shadow_root,
    list_runs,
)

scenarios("../../features/report-runs.feature")


@pytest.fixture
def run_world(git_repo, temp_cache):
    """Context state for report-runs scenarios."""
    return {
        "repo": git_repo,
        "cache": temp_cache,
        "runs": {},
        "oldest_auth": None,
        "full_run": None,
        "base_time": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "time_offset": 0,
    }


def _next_time(world: dict) -> datetime:
    world["time_offset"] += 1
    return world["base_time"] + timedelta(seconds=world["time_offset"])


# --- Scenario: Latest is the newest run of a lens -------------------------

@given(parsers.parse('runs of the full repository at commit "{c1}" and then at commit "{c2}"'))
def _runs_at_c1_and_c2(run_world, c1, c2):
    repo = run_world["repo"]
    r1 = create_run_dir(repo, "full", commit=c1, created_at=_next_time(run_world))
    r2 = create_run_dir(repo, "full", commit=c2, created_at=_next_time(run_world))
    run_world["runs"][c1] = r1
    run_world["runs"][c2] = r2


@then(parsers.parse('the latest report of the full repository is the one at commit "{commit}"'))
def _latest_is_commit(run_world, commit):
    repo = run_world["repo"]
    latest = get_latest_run(repo, "full")
    assert latest is not None
    assert latest.resolve() == run_world["runs"][commit].resolve()
    meta = json.loads((latest / "run.json").read_text(encoding="utf-8"))
    assert meta["commit"] == commit


# --- Scenario: A lens keeps its five newest runs --------------------------

@given(parsers.parse('five runs of the topic "{topic}"'))
def _five_runs_of_topic(run_world, topic):
    repo = run_world["repo"]
    topic_runs = []
    for i in range(5):
        r = create_run_dir(repo, topic, commit=f"t{i}", created_at=_next_time(run_world))
        topic_runs.append(r)
    run_world["runs"][topic] = topic_runs
    run_world["oldest_auth"] = topic_runs[0]


@when(parsers.parse('the user makes a sixth report on "{topic}"'))
def _sixth_report_on_topic(run_world, topic):
    repo = run_world["repo"]
    r6 = create_run_dir(repo, topic, commit="t6", created_at=_next_time(run_world))
    run_world["runs"].setdefault(topic, []).append(r6)


@then(parsers.parse('the oldest report on "{topic}" is removed'))
def _oldest_report_removed(run_world, topic):
    repo = run_world["repo"]
    lens_dir = get_lens_dir(repo, topic)
    runs = list_runs(lens_dir)
    assert len(runs) == 5
    oldest = run_world["oldest_auth"]
    assert oldest is not None
    assert not oldest.exists()
    assert oldest not in runs


# --- Scenario: Runs of one lens do not remove runs of another lens --------

@given(parsers.parse('five runs of the topic "{topic}" and one run of the full repository'))
def _five_topic_and_one_full(run_world, topic):
    repo = run_world["repo"]
    topic_runs = []
    for i in range(5):
        r = create_run_dir(repo, topic, commit=f"t{i}", created_at=_next_time(run_world))
        topic_runs.append(r)
    run_world["runs"][topic] = topic_runs
    run_world["oldest_auth"] = topic_runs[0]

    full_run = create_run_dir(repo, "full", commit="full-1", created_at=_next_time(run_world))
    run_world["full_run"] = full_run


@then("the report of the full repository is still there")
def _full_report_still_there(run_world):
    full_run = run_world["full_run"]
    assert full_run is not None
    assert full_run.exists()
    latest_full = get_latest_run(run_world["repo"], "full")
    assert latest_full is not None
    assert latest_full.resolve() == full_run.resolve()


# --- Scenario: Reports and todo cards of one repository share one name ----

@given("the repository has todo cards")
def _repo_has_todo_cards(run_world):
    repo = run_world["repo"]
    todo_dir = todo_parser.get_shadow_dir(repo)
    assert todo_dir.exists()
    run_world["todo_dir"] = todo_dir
    run_world["todo_slug"] = todo_parser.get_repo_slug(repo)


@when("a report of the repository is made")
def _report_is_made(run_world):
    repo = run_world["repo"]
    run_dir = create_run_dir(repo, "full", commit="c1", created_at=_next_time(run_world))
    run_world["report_run"] = run_dir
    run_world["understand_slug"] = get_repo_slug(repo)


@then("the report directory and the todo card directory use the same repository name")
def _report_and_todo_share_name(run_world):
    understand_slug = run_world["understand_slug"]
    todo_slug = run_world["todo_slug"]
    assert understand_slug == todo_slug

    shadow_root = get_shadow_root()
    understand_repo_dir = shadow_root / understand_slug
    assert understand_repo_dir.exists()
    assert understand_repo_dir.name == run_world["todo_dir"].name
