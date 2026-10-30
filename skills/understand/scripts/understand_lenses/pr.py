# pyright: reportMissingImports=false
"""PR lens: gh pr view metadata and detached worktree lifecycle (Spec Unit 1 & Step 5)."""

from __future__ import annotations

import json
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from understand_runs.slug import get_repo_root, get_repo_slug
from understand_runs.storage import get_shadow_root

from .models import LensFocus


def fetch_pr_metadata(
    repo_path: Path,
    pr_number: int | str,
    gh_cmd: list[str] | None = None,
) -> dict[str, Any]:
    """Retrieves PR metadata using `gh pr view --json title,body,files,baseRefOid,headRefOid`."""
    cmd = list(gh_cmd) if gh_cmd is not None else [
        "gh",
        "pr",
        "view",
        str(pr_number),
        "--json",
        "title,body,files,baseRefOid,headRefOid",
    ]
    res = subprocess.run(
        cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(res.stdout)


def get_pr_worktree_path(
    repo_path: Path,
    pr_number: int | str,
    base_dir: Path | None = None,
) -> Path:
    """Returns the shadow worktree directory: <shadow>/<slug>/wt/pr-<n>."""
    root = get_repo_root(repo_path)
    slug = get_repo_slug(root)
    shadow = base_dir or get_shadow_root()
    return shadow / slug / "wt" / f"pr-{pr_number}"


def create_pr_worktree(
    repo_path: Path,
    wt_path: Path,
    head_ref_oid: str,
) -> Path:
    """Creates a temporary detached worktree at head_ref_oid."""
    root = get_repo_root(repo_path)
    wt_path.parent.mkdir(parents=True, exist_ok=True)
    if wt_path.exists():
        cleanup_pr_worktree(root, wt_path)

    subprocess.run(
        ["git", "worktree", "add", "--detach", str(wt_path), head_ref_oid],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return wt_path


def cleanup_pr_worktree(repo_path: Path, wt_path: Path) -> None:
    """Cleans up the temporary detached worktree and metadata."""
    root = get_repo_root(repo_path)
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(wt_path)],
        cwd=root,
        capture_output=True,
    )
    if wt_path.exists():
        shutil.rmtree(wt_path, ignore_errors=True)
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=root,
        capture_output=True,
    )


@contextmanager
def pr_worktree_context(
    repo_path: Path,
    pr_number: int | str,
    head_ref_oid: str,
    base_dir: Path | None = None,
) -> Generator[Path, None, None]:
    """Context manager ensuring temporary detached worktree is cleaned up on success and failure."""
    wt_path = get_pr_worktree_path(repo_path, pr_number, base_dir=base_dir)
    create_pr_worktree(repo_path, wt_path, head_ref_oid)
    try:
        yield wt_path
    finally:
        cleanup_pr_worktree(repo_path, wt_path)


def compute_pr_focus(
    repo_path: Path,
    pr_number: int | str,
    pr_metadata: dict[str, Any],
    source_root: Path | None = None,
) -> LensFocus:
    """Computes focus set for PR from metadata changed files."""
    files_list = pr_metadata.get("files", [])
    changed_paths: set[str] = set()
    for item in files_list:
        if isinstance(item, dict) and "path" in item:
            changed_paths.add(item["path"])
        elif isinstance(item, str):
            changed_paths.add(item)

    root = source_root or repo_path
    all_files = sorted(
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and not p.name.startswith(".")
    )

    return LensFocus(
        lens_type="pr",
        focus_set=changed_paths,
        seed_nodes=changed_paths,
        all_files=all_files,
        metadata={"pr_number": str(pr_number), **pr_metadata},
    )
