# pyright: reportMissingImports=false
"""Shadow directory and run retention manager for /understand (Spec Unit 4)."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from understand_runs.slug import get_repo_slug

RETENTION_LIMIT = 5


def get_shadow_root(cache_home: Path | str | None = None) -> Path:
    """Returns the base shadow directory under XDG_CACHE_HOME."""
    if cache_home is not None:
        base = Path(cache_home)
    else:
        xdg = os.environ.get("XDG_CACHE_HOME")
        base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "agent-skills" / "understand"


def normalize_lens(lens: str, target: str | None = None) -> str:
    """Normalizes lens and target into a lens identifier directory name."""
    clean_target = (target or "").strip()
    if lens == "full":
        return "full"
    if lens == "topic":
        return f"topic-{clean_target}" if clean_target else "topic"
    if lens == "pr":
        return f"pr-{clean_target}" if clean_target else "pr"
    if lens == "diff":
        return f"diff-{clean_target}" if clean_target else "diff"
    if lens.startswith(("topic-", "pr-", "diff-")):
        return lens
    # If lens name is given as topic name directly (e.g. "auth")
    return f"topic-{lens}"


def get_lens_dir(
    repo_root: Path,
    lens: str,
    target: str | None = None,
    base_dir: Path | None = None,
) -> Path:
    """Returns the lens directory for a repository slug and lens."""
    shadow = base_dir or get_shadow_root()
    slug = get_repo_slug(repo_root)
    lens_id = normalize_lens(lens, target)
    lens_dir = shadow / slug / lens_id
    lens_dir.mkdir(parents=True, exist_ok=True)
    return lens_dir


def _run_sort_key(run_dir: Path) -> tuple[str, float]:
    meta_file = run_dir / "run.json"
    if meta_file.is_file():
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            created = data.get("created_at")
            if created:
                return (str(created), 0.0)
        except (json.JSONDecodeError, OSError):
            created = None
    try:
        mtime = run_dir.stat().st_mtime
    except OSError:
        mtime = 0.0
    return ("", mtime)


def list_runs(lens_dir: Path) -> list[Path]:
    """Lists all valid run directories in lens_dir, ordered oldest to newest."""
    if not lens_dir.is_dir():
        return []
    runs = [
        p
        for p in lens_dir.iterdir()
        if p.is_dir() and not p.is_symlink() and not p.name.startswith(".") and p.name != "latest"
    ]
    runs.sort(key=_run_sort_key)
    return runs


def update_latest(lens_dir: Path, run_dir: Path) -> Path:
    """Maintains atomic symlink 'latest' pointing to newest run."""
    latest = lens_dir / "latest"
    tmp_link = lens_dir / f".tmp-latest-{os.getpid()}"
    if tmp_link.is_symlink() or tmp_link.exists():
        tmp_link.unlink()
    tmp_link.symlink_to(run_dir.name)
    tmp_link.replace(latest)
    return latest


def prune_runs(lens_dir: Path, keep: int = RETENTION_LIMIT) -> list[Path]:
    """Prunes older runs beyond `keep` limit, maintaining isolation per lens."""
    runs = list_runs(lens_dir)
    pruned: list[Path] = []
    if len(runs) > keep:
        to_remove = runs[: len(runs) - keep]
        for p in to_remove:
            shutil.rmtree(p, ignore_errors=True)
            pruned.append(p)
    return pruned


def create_run_dir(
    repo_root: Path,
    lens: str,
    target: str | None = None,
    commit: str | None = None,
    run_id: str | None = None,
    created_at: datetime | None = None,
    base_dir: Path | None = None,
) -> Path:
    """Creates a new run directory, records metadata, links latest, and prunes older runs."""
    lens_dir = get_lens_dir(repo_root, lens, target=target, base_dir=base_dir)
    ts = created_at or datetime.now(timezone.utc)
    ts_str = ts.strftime("%Y%m%dT%H%M%S%fZ")

    if run_id:
        rid = run_id
    elif commit:
        rid = f"{commit}-{ts_str}"
    else:
        rid = ts_str

    run_dir = lens_dir / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    meta: dict[str, Any] = {
        "run_id": rid,
        "commit": commit,
        "lens": normalize_lens(lens, target),
        "created_at": ts.isoformat(),
    }
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    update_latest(lens_dir, run_dir)
    prune_runs(lens_dir, keep=RETENTION_LIMIT)
    return run_dir


def get_latest_run(
    repo_root: Path,
    lens: str,
    target: str | None = None,
    base_dir: Path | None = None,
) -> Path | None:
    """Returns the run directory pointed to by latest, or newest existing run."""
    shadow = base_dir or get_shadow_root()
    slug = get_repo_slug(repo_root)
    lens_id = normalize_lens(lens, target)
    lens_dir = shadow / slug / lens_id
    latest = lens_dir / "latest"
    if latest.is_symlink():
        target_name = os.readlink(latest)
        resolved = lens_dir / target_name
        if resolved.is_dir():
            return resolved
    runs = list_runs(lens_dir)
    return runs[-1] if runs else None
