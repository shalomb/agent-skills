"""Cycle B: read real history, decide the groups."""


def history(repo):
    """base, feat A, noise, noise, fix B, noise(tip)."""
    base = repo.commit("initial", {"main.tf": "v0\n"})
    a = repo.commit("feat: add rules", {"main.tf": "v1\n"})
    n1 = repo.commit("typo", {"README.md": "a\n"})
    n2 = repo.commit("lint", {"README.md": "b\n"})
    b = repo.commit("fix: null filter", {"main.tf": "v2\n"})
    n3 = repo.commit("wip", {"README.md": "c\n"})
    return dict(base=base, a=a, n1=n1, n2=n2, b=b, n3=n3)


def test_read_commits_is_first_parent_oldest_first_with_stats_and_tags(ss, repo):
    h = history(repo)
    repo.git("tag", "v1.0.0", h["a"])
    commits = ss.read_commits(repo.path, base=None, branch="main")
    assert [c.sha for c in commits] == [h["base"], h["a"], h["n1"], h["n2"], h["b"], h["n3"]]
    a = commits[1]
    assert a.subject == "feat: add rules" and a.files == ("main.tf",) and a.added == 1 and a.deleted == 1
    assert a.tags == ("v1.0.0",) and commits[2].tags == ()


def test_read_commits_excludes_base(ss, repo):
    h = history(repo)
    commits = ss.read_commits(repo.path, base=h["a"], branch="main")
    assert [c.sha for c in commits][0] == h["n1"]


def test_noise_folds_into_next_anchor(ss, repo):
    h = history(repo)
    plan = ss.build_plan(ss.read_commits(repo.path, None, "main"), ss.Config())
    subjects = [(g.anchor_subject, len(g.members)) for g in plan.groups]
    assert subjects == [("initial", 1), ("feat: add rules", 1), ("fix: null filter", 4)]  # typo, lint, the fix, trailing wip


def test_trailing_noise_folds_into_previous_anchor_and_tip_tree_wins(ss, repo):
    h = history(repo)
    plan = ss.build_plan(ss.read_commits(repo.path, None, "main"), ss.Config())
    last = plan.groups[-1]
    assert last.anchor == h["b"] and last.tip == h["n3"] and h["n3"] in last.members


def test_plan_counts(ss, repo):
    history(repo)
    plan = ss.build_plan(ss.read_commits(repo.path, None, "main"), ss.Config())
    assert (plan.before, plan.after) == (6, 3)


def test_plan_with_no_anchors_still_yields_one_group(ss, repo):
    repo.git("commit", "-q", "--allow-empty", "-m", "wip")  # root is always an anchor, so rebuild from a base
    base = repo.git("rev-parse", "HEAD")
    repo.commit("typo", {"README.md": "x\n"})
    repo.commit("lint", {"README.md": "y\n"})
    plan = ss.build_plan(ss.read_commits(repo.path, base, "main"), ss.Config())
    assert plan.after == 1 and len(plan.groups[0].members) == 2


def test_merge_commit_is_its_own_group_and_side_branch_not_walked(ss, repo):
    repo.commit("initial", {"main.tf": "0\n"})
    repo.git("checkout", "-q", "-b", "side")
    side = repo.commit("side work", {"s.txt": "s\n"})
    repo.git("checkout", "-q", "main")
    repo.commit("main work", {"m.txt": "m\n"})
    repo.git("merge", "-q", "--no-ff", "side", "-m", "Merge side")
    commits = ss.read_commits(repo.path, None, "main")
    assert side not in [c.sha for c in commits]
    plan = ss.build_plan(commits, ss.Config())
    assert plan.groups[-1].anchor_subject == "Merge side"
