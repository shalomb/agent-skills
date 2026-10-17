"""Cycle C: apply the plan to a NEW branch and prove nothing was lost."""
import json

import pytest


def feature(repo):
    """main: initial. feature: feat A, typo, lint, fix B, wip."""
    repo.commit("initial", {"main.tf": "v0\n"})
    repo.git("checkout", "-q", "-b", "feature")
    h = {}
    h["a"] = repo.commit("feat: add rules", {"main.tf": "v1\n"}, author="Ann <ann@example.com>")
    h["n1"] = repo.commit("typo", {"README.md": "a\n"})
    h["n2"] = repo.commit("lint", {"README.md": "b\n"})
    h["b"] = repo.commit("fix: null filter", {"main.tf": "v2\n"}, body="Why: upstream deref.")
    h["n3"] = repo.commit("wip", {"README.md": "c\n"})
    return h


def run(ss, repo, branch="feature", **kw):
    base, _ = ss.resolve_range(repo.path, branch, kw.pop("base", None))
    plan = ss.build_plan(ss.read_commits(repo.path, base, branch), ss.Config())
    return plan, ss.apply_plan(repo.path, plan, branch, base)


def test_apply_creates_new_branch_with_identical_tree(ss, repo):
    feature(repo)
    plan, res = run(ss, repo)
    assert res.branch == "feature-smart-squash"
    assert repo.git("rev-parse", "feature-smart-squash^{tree}") == repo.git("rev-parse", "feature^{tree}")


def test_history_is_shorter_by_the_folded_count(ss, repo):
    feature(repo)
    plan, res = run(ss, repo)
    assert repo.git("rev-list", "--count", "main..feature-smart-squash") == str(plan.after) == "2"
    assert repo.git("rev-list", "--count", "main..feature") == "5"


def test_anchor_messages_survive_and_folded_commits_are_listed(ss, repo):
    feature(repo)
    run(ss, repo)
    msgs = repo.git("log", "--format=%B%x1e", "main..feature-smart-squash").split("\x1e")
    fix = next(m for m in msgs if m.strip().startswith("fix: null filter"))
    assert "Why: upstream deref." in fix
    assert "Folded commits (3):" in fix and "typo" in fix and "lint" in fix and "wip" in fix


def test_author_of_the_anchor_is_preserved(ss, repo):
    feature(repo)
    run(ss, repo)
    authors = repo.git("log", "--format=%an <%ae>", "main..feature-smart-squash").splitlines()
    assert "Ann <ann@example.com>" in authors


def test_existing_refs_are_never_moved(ss, repo):
    h = feature(repo)
    before = repo.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags")
    run(ss, repo)
    after = repo.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags").splitlines()
    assert set(before.splitlines()) <= set(after) and len(after) == len(before.splitlines()) + 1
    assert repo.git("rev-parse", "feature") == h["n3"]


def test_sha_map_covers_every_source_commit(ss, repo):
    h = feature(repo)
    plan, res = run(ss, repo)
    assert set(res.sha_map) == {h["a"], h["n1"], h["n2"], h["b"], h["n3"]}
    assert res.sha_map[h["n1"]] == res.sha_map[h["b"]] == res.sha_map[h["n3"]] != res.sha_map[h["a"]]


def test_tagged_commit_survives_and_tag_map_reports_new_sha(ss, repo):
    h = feature(repo)
    repo.git("tag", "v0.1.0", h["n1"])           # a tag on a would-be-noise commit
    plan, res = run(ss, repo)
    assert plan.after == 3
    assert res.tag_map["v0.1.0"] == (h["n1"], res.sha_map[h["n1"]])
    assert repo.git("rev-parse", "v0.1.0") == h["n1"]    # tag itself not moved


def test_merge_commit_keeps_its_second_parent(ss, repo):
    repo.commit("initial", {"main.tf": "0\n"})
    repo.git("checkout", "-q", "-b", "feature")
    repo.commit("typo", {"README.md": "a\n"})
    repo.git("checkout", "-q", "-b", "side", "main")
    side = repo.commit("side work", {"s.txt": "s\n"})
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "side", "-m", "Merge side")
    run(ss, repo)
    parents = repo.git("log", "-1", "--format=%P", "feature-smart-squash").split()
    assert len(parents) == 2 and parents[1] == side
    assert repo.git("rev-parse", "feature-smart-squash^{tree}") == repo.git("rev-parse", "feature^{tree}")


def test_refuses_to_overwrite_an_existing_output_branch(ss, repo):
    feature(repo)
    repo.git("branch", "feature-smart-squash", "main")
    with pytest.raises(ss.Refused, match="exists"):
        run(ss, repo)


def test_refuses_to_squash_the_default_branch(ss, repo):
    repo.commit("initial", {"main.tf": "0\n"})
    repo.commit("typo", {"README.md": "a\n"})
    with pytest.raises(ss.Refused, match="default branch"):
        ss.resolve_range(repo.path, "main", None)


def test_default_branch_allowed_only_when_explicit(ss, repo):
    repo.commit("initial", {"main.tf": "0\n"})
    repo.commit("typo", {"README.md": "a\n"})
    base, _ = ss.resolve_range(repo.path, "main", None, allow_default=True)
    assert base is None


def test_feature_base_is_merge_base_with_default(ss, repo):
    feature(repo)
    base, _ = ss.resolve_range(repo.path, "feature", None)
    assert base == repo.git("rev-parse", "main")


def test_nothing_to_squash_is_refused(ss, repo):
    repo.commit("initial", {"main.tf": "0\n"})
    repo.git("checkout", "-q", "-b", "feature")
    repo.commit("feat: a", {"main.tf": "1\n"})
    repo.commit("fix: b", {"main.tf": "2\n"})
    with pytest.raises(ss.Refused, match="nothing to squash"):
        run(ss, repo)


def test_signing_is_honoured_when_configured(ss, repo):
    assert ss.signing_args(repo.path) == []
    repo.git("config", "commit.gpgsign", "true")
    assert ss.signing_args(repo.path) == ["-S"]
