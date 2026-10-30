# pyright: reportMissingImports=false
"""Unit tests for understand_runs storage and retention manager."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from understand_runs.storage import (
    create_run_dir,
    get_latest_run,
    get_lens_dir,
    get_shadow_root,
    list_runs,
    normalize_lens,
    prune_runs,
)


def test_get_shadow_root_xdg(temp_cache):
    root = get_shadow_root()
    assert root == temp_cache / "agent-skills" / "understand"


def test_normalize_lens():
    assert normalize_lens("full") == "full"
    assert normalize_lens("auth") == "topic-auth"
    assert normalize_lens("topic-auth") == "topic-auth"
    assert normalize_lens("topic", target="auth") == "topic-auth"
    assert normalize_lens("pr", target="123") == "pr-123"
    assert normalize_lens("diff", target="main") == "diff-main"


def test_create_run_and_latest_symlink(temp_cache, git_repo):
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    run_1 = create_run_dir(git_repo, "full", commit="c1", created_at=t0)
    assert run_1.exists()
    assert run_1.is_dir()
    assert "c1" in run_1.name

    latest = get_latest_run(git_repo, "full")
    assert latest is not None
    assert latest.resolve() == run_1.resolve()

    # Second run at c2 becomes the new latest
    t1 = t0 + timedelta(seconds=1)
    run_2 = create_run_dir(git_repo, "full", commit="c2", created_at=t1)
    assert run_2.exists()
    latest_2 = get_latest_run(git_repo, "full")
    assert latest_2 is not None
    assert latest_2.resolve() == run_2.resolve()


def test_retention_policy_keeps_five_newest(temp_cache, git_repo):
    base_t = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    runs = []
    for i in range(5):
        t = base_t + timedelta(seconds=i)
        r = create_run_dir(git_repo, "auth", commit=f"c{i}", created_at=t)
        runs.append(r)

    lens_dir = get_lens_dir(git_repo, "auth")
    current_runs = list_runs(lens_dir)
    assert len(current_runs) == 5

    # Create 6th run
    t5 = base_t + timedelta(seconds=5)
    run_6 = create_run_dir(git_repo, "auth", commit="c5", created_at=t5)
    current_runs_after = list_runs(lens_dir)
    assert len(current_runs_after) == 5
    assert runs[0] not in current_runs_after
    assert not runs[0].exists()
    assert run_6 in current_runs_after


def test_lens_isolation_during_pruning(temp_cache, git_repo):
    base_t = datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
    # Create 1 run in full lens
    full_run = create_run_dir(git_repo, "full", commit="cf1", created_at=base_t)

    # Create 6 runs in auth topic lens
    for i in range(6):
        t = base_t + timedelta(seconds=i + 1)
        create_run_dir(git_repo, "auth", commit=f"ca{i}", created_at=t)

    # Full run must remain untouched
    assert full_run.exists()
    latest_full = get_latest_run(git_repo, "full")
    assert latest_full is not None
    assert latest_full.resolve() == full_run.resolve()
