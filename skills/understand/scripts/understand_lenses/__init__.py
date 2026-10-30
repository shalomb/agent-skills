# pyright: reportMissingImports=false
"""Lenses for /understand reports: topic, PR, and diff (Spec Units 1 & 2)."""

from .diff import compute_diff_focus, get_merge_base
from .models import LensFocus
from .pr import (
    cleanup_pr_worktree,
    compute_pr_focus,
    create_pr_worktree,
    fetch_pr_metadata,
    get_pr_worktree_path,
    pr_worktree_context,
)
from .topic import compute_topic_focus, expand_topic, find_seed_nodes

__all__ = [
    "LensFocus",
    "cleanup_pr_worktree",
    "compute_diff_focus",
    "compute_pr_focus",
    "compute_topic_focus",
    "create_pr_worktree",
    "expand_topic",
    "fetch_pr_metadata",
    "find_seed_nodes",
    "get_merge_base",
    "get_pr_worktree_path",
    "pr_worktree_context",
]
