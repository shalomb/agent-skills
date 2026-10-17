"""Cycle D: the command line. Real subprocess, real repo."""
import json
import subprocess
import sys

from conftest import SCRIPT
from test_apply import feature


def cli(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--repo", str(repo.path)], capture_output=True, text=True)


def test_plan_is_read_only_and_shows_the_groups(repo):
    feature(repo)
    before = repo.git("for-each-ref")
    r = cli(repo, "plan", "--branch", "feature")
    assert r.returncode == 0, r.stderr
    assert "5 commits -> 2" in r.stdout and "fix: null filter" in r.stdout and "folds 3" in r.stdout
    assert repo.git("for-each-ref") == before


def test_plan_json_is_machine_readable(repo):
    feature(repo)
    r = cli(repo, "plan", "--branch", "feature", "--json")
    data = json.loads(r.stdout)
    assert data["before"] == 5 and data["after"] == 2 and data["groups"][-1]["anchor_subject"] == "fix: null filter"


def test_apply_creates_branch_and_writes_sha_map_outside_the_worktree(repo):
    feature(repo)
    r = cli(repo, "apply", "--branch", "feature")
    assert r.returncode == 0, r.stderr
    assert repo.git("rev-parse", "--verify", "feature-smart-squash")
    mapfile = repo.path / ".git" / "smart-squash" / "feature-smart-squash.json"
    data = json.loads(mapfile.read_text())
    assert len(data["sha_map"]) == 5 and "tag_map" in data
    assert repo.git("status", "--porcelain") == ""          # worktree untouched


def test_refusal_exits_2_with_a_message_and_writes_nothing(repo):
    repo.commit("initial", {"main.tf": "0\n"})
    before = repo.git("for-each-ref")
    r = cli(repo, "plan", "--branch", "main")
    assert r.returncode == 2 and "default branch" in r.stderr
    assert repo.git("for-each-ref") == before


def test_custom_out_branch_and_thresholds(repo):
    feature(repo)
    r = cli(repo, "apply", "--branch", "feature", "--out", "clean", "--no-runtime-anchor")
    assert r.returncode == 0, r.stderr
    assert repo.git("rev-parse", "--verify", "clean")


def test_a_non_repo_path_is_a_clean_error_not_a_traceback(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), "plan", "--repo", str(tmp_path / "nope"), "--branch", "x"],
                       capture_output=True, text=True)
    assert r.returncode == 1 and r.stderr.startswith("error:") and "Traceback" not in r.stderr
