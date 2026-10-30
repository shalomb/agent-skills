# pyright: reportMissingImports=false
"""Unit tests for Topic Lens (Spec Unit 2 & Step 5)."""

from __future__ import annotations

from understand_lenses.topic import (
    compute_topic_focus,
    expand_topic,
    find_seed_nodes,
)


def test_expand_topic_semantic_terms():
    """Expanding a topic query produces semantic synonyms and related terms."""
    terms = expand_topic("how billing retries work")
    terms_lower = [t.lower() for t in terms]
    assert "billing" in terms_lower
    assert any("retry" in t or "retries" in t for t in terms_lower)
    assert any(term in terms_lower for term in ("backoff", "reschedule", "payment", "payments"))


def test_find_seed_nodes_with_different_words(tmp_path):
    """Topic query finds code that uses a different word via semantic expansion."""
    repo = tmp_path / "repo"
    billing = repo / "billing"
    billing.mkdir(parents=True)
    backoff = billing / "backoff.py"
    backoff.write_text("# Schedules failed payments again\ndef run(): pass\n", encoding="utf-8")

    auth = repo / "auth"
    auth.mkdir()
    (auth / "login.py").write_text("def login(): pass\n", encoding="utf-8")

    files = ["billing/backoff.py", "auth/login.py"]
    terms = expand_topic("how billing retries work")
    seeds = find_seed_nodes(repo, terms, files=files)

    assert "billing/backoff.py" in seeds
    assert "auth/login.py" not in seeds


def test_seed_node_1hop_neighbours_in_focus_set(tmp_path):
    """Direct 1-hop neighbours of a seed node are included in the focus set."""
    repo = tmp_path / "repo"
    billing = repo / "billing"
    billing.mkdir(parents=True)
    (billing / "retry.py").write_text("import billing.clock\n", encoding="utf-8")
    (billing / "clock.py").write_text("class Clock: pass\n", encoding="utf-8")

    auth = repo / "auth"
    auth.mkdir()
    (auth / "login.py").write_text("def login(): pass\n", encoding="utf-8")

    files = ["billing/retry.py", "billing/clock.py", "auth/login.py"]
    focus = compute_topic_focus(repo, topic="retry", files=files)

    assert "billing/retry.py" in focus.seed_nodes
    assert "billing/clock.py" in focus.focus_set
    assert "billing/retry.py" in focus.focus_set
    assert "auth/login.py" not in focus.focus_set


def test_nodes_outside_focus_set_retained_in_graph(tmp_path):
    """Nodes outside the focus set stay in the full graph but are not in the focus set."""
    repo = tmp_path / "repo"
    billing = repo / "billing"
    billing.mkdir(parents=True)
    (billing / "retry.py").write_text("def retry(): pass\n", encoding="utf-8")

    auth = repo / "auth"
    auth.mkdir()
    (auth / "login.py").write_text("def login(): pass\n", encoding="utf-8")

    files = ["billing/retry.py", "auth/login.py"]
    focus = compute_topic_focus(repo, topic="retry", files=files)

    assert "billing/retry.py" in focus.focus_set
    assert "auth/login.py" not in focus.focus_set
    assert set(focus.all_files) == set(files)
