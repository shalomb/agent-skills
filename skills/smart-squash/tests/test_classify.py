"""Cycle A: is a commit an ANCHOR (keep) or NOISE (fold)?"""
import pytest


def mk(ss, subject, **kw):
    base = dict(sha="a" * 40, parents=("b" * 40,), subject=subject, body="", files=("main.tf",), added=5, deleted=1, tags=())
    base.update(kw)
    return ss.Commit(**base)


@pytest.mark.parametrize("subject", [
    "feat: add lifecycle rules", "feat(s3): x", "fix: null filter", "fix(alb): port",
    "perf: faster plan", "revert: feat: x", "feat!: drop var", "Fix: capitalised conventional",
])
def test_release_driving_types_are_anchors(ss, subject):
    assert ss.classify(mk(ss, subject), ss.Config()).anchor


@pytest.mark.parametrize("subject", ["wip", "WIP stuff", "typo", "fix typo in readme", "lint", "ruff format",
                                      "address review comments", "fixup! feat: x", "squash! y", "oops", "tmp"])
def test_explicit_noise_patterns_are_noise(ss, subject):
    assert not ss.classify(mk(ss, subject, files=("README.md",)), ss.Config()).anchor


def test_noise_pattern_beats_runtime_tf(ss):
    c = mk(ss, "lint", files=("main.tf",))
    assert not ss.classify(c, ss.Config()).anchor


def test_breaking_change_footer_is_anchor(ss):
    c = mk(ss, "chore: tidy", body="BREAKING CHANGE: removes var x")
    assert ss.classify(c, ss.Config()).anchor


def test_merge_commit_is_anchor(ss):
    assert ss.classify(mk(ss, "Merge branch 'x'", parents=("1" * 40, "2" * 40)), ss.Config()).anchor


def test_tagged_commit_is_anchor_even_if_noise(ss):
    assert ss.classify(mk(ss, "wip", tags=("v1.2.0",)), ss.Config()).anchor


def test_pr_reference_is_anchor(ss):
    assert ss.classify(mk(ss, "tidy things (#123)"), ss.Config()).anchor


def test_root_commit_is_anchor(ss):
    assert ss.classify(mk(ss, "initial", parents=()), ss.Config()).anchor


def test_large_free_form_commit_is_anchor(ss):
    assert ss.classify(mk(ss, "rework modules", files=("docs/a.md",), added=150, deleted=0), ss.Config()).anchor


def test_small_free_form_docs_commit_is_noise(ss):
    assert not ss.classify(mk(ss, "update docs", files=("docs/a.md",), added=3, deleted=1), ss.Config()).anchor


def test_free_form_touching_runtime_tf_is_anchor(ss):
    assert ss.classify(mk(ss, "handle null port", files=("main.tf",)), ss.Config()).anchor


@pytest.mark.parametrize("path", ["tests/unit/x.tftest.hcl", "examples/a/main.tf", "docs/x.md", ".github/w.yml", "README.md"])
def test_non_runtime_paths_do_not_make_an_anchor(ss, path):
    assert not ss.classify(mk(ss, "small tweak", files=(path,), added=2, deleted=2), ss.Config()).anchor


def test_runtime_anchor_can_be_disabled(ss):
    cfg = ss.Config(runtime_tf_is_anchor=False)
    assert not ss.classify(mk(ss, "handle null port", files=("main.tf",)), cfg).anchor


def test_classification_explains_itself(ss):
    r = ss.classify(mk(ss, "feat: x"), ss.Config())
    assert r.reason and "feat" in r.reason


def test_automated_sync_commits_are_noise(ss):
    assert not ss.classify(mk(ss, "sync: update framework from template", files=("src/framework/a.py",)), ss.Config()).anchor
