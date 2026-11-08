# pyright: reportMissingImports=false
"""Client-side catalog SPA dashboard deployer and atomic catalog writer (ADR 0004)."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any

REQUIRED_ENTRY_KEYS = {
    "repo_slug",
    "lens",
    "target",
    "run_id",
    "timestamp",
    "commit",
    "summary",
    "urls",
    "report_rel_url",
}

SPA_ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "catalog_spa.html"


# mkstemp creates 0600; the web server (www-data, ADR 0007) must be able to read published files.
_PUBLISHED_MODE = 0o644


def _get_understand_dir(shadow_root: Path) -> Path:
    """Returns the understand directory under shadow_root, avoiding double understand/ nesting."""
    root = Path(shadow_root).resolve()
    if root.name == "understand":
        return root
    return root / "understand"


def _validate_entry(entry: dict[str, Any]) -> None:
    if not isinstance(entry, dict):
        raise TypeError(f"entry must be a dict, got {type(entry).__name__}")
    missing = REQUIRED_ENTRY_KEYS - entry.keys()
    if missing:
        raise ValueError(f"entry is missing required keys: {sorted(missing)}")
    if not isinstance(entry["repo_slug"], str):
        raise TypeError("entry['repo_slug'] must be a str")
    if not isinstance(entry["lens"], str):
        raise TypeError("entry['lens'] must be a str")
    if entry["target"] is not None and not isinstance(entry["target"], str):
        raise TypeError("entry['target'] must be a str or None")
    if not isinstance(entry["run_id"], str):
        raise TypeError("entry['run_id'] must be a str")
    if not isinstance(entry["timestamp"], str):
        raise TypeError("entry['timestamp'] must be a str")
    if entry["commit"] is not None and not isinstance(entry["commit"], str):
        raise TypeError("entry['commit'] must be a str or None")
    if not isinstance(entry["summary"], str):
        raise TypeError("entry['summary'] must be a str")
    if not isinstance(entry["urls"], dict):
        raise TypeError("entry['urls'] must be a dict")
    if not isinstance(entry["report_rel_url"], str):
        raise TypeError("entry['report_rel_url'] must be a str")


def update_catalog(shadow_root: Path, entry: dict[str, Any]) -> Path:
    """Appends or updates a report run record in catalog.json under shadow_root / 'understand' / 'catalog.json'.

    Uses fcntl.flock on catalog.json.lock to prevent concurrency race conditions.
    Writes to a temporary file first and atomically renames to catalog.json (os.replace).
    """
    _validate_entry(entry)

    understand_dir = _get_understand_dir(shadow_root)
    understand_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = understand_dir / "catalog.json"
    lock_path = understand_dir / "catalog.json.lock"

    lock_fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            entries: list[dict[str, Any]] = []
            is_dict_wrapper = False
            original_wrapper: dict[str, Any] = {}

            if catalog_path.is_file():
                try:
                    content = catalog_path.read_text(encoding="utf-8")
                    if content.strip():
                        data = json.loads(content)
                        if isinstance(data, list):
                            entries = data
                        elif isinstance(data, dict):
                            is_dict_wrapper = True
                            original_wrapper = data
                            entries = list(data.get("runs", []))
                except (json.JSONDecodeError, OSError):
                    entries = []

            # Update if (repo_slug, run_id) exists, else append
            updated = False
            for i, existing in enumerate(entries):
                if (
                    isinstance(existing, dict)
                    and existing.get("repo_slug") == entry["repo_slug"]
                    and existing.get("run_id") == entry["run_id"]
                ):
                    entries[i] = entry
                    updated = True
                    break

            if not updated:
                entries.append(entry)

            if is_dict_wrapper:
                out_data: Any = {**original_wrapper, "runs": entries}
            else:
                out_data = entries

            tmp_fd, tmp_path_str = tempfile.mkstemp(
                prefix=".tmp-catalog-",
                suffix=".json",
                dir=str(understand_dir),
            )
            tmp_path = Path(tmp_path_str)
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    json.dump(out_data, f, indent=2)
                    f.write("\n")
                    f.flush()
                    os.fsync(f.fileno())
                os.chmod(tmp_path, _PUBLISHED_MODE)
                os.replace(tmp_path, catalog_path)
            except BaseException:
                if tmp_path.exists():
                    tmp_path.unlink()
                raise
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
    finally:
        os.close(lock_fd)

    return catalog_path


def _get_catalog_spa_html() -> str:
    if SPA_ASSET_PATH.is_file():
        return SPA_ASSET_PATH.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Catalog SPA template not found at {SPA_ASSET_PATH}")


def deploy_catalog_spa(shadow_root: Path) -> Path:
    """Writes index.html to shadow_root / 'understand' / 'index.html'."""
    understand_dir = _get_understand_dir(shadow_root)
    understand_dir.mkdir(parents=True, exist_ok=True)
    index_path = understand_dir / "index.html"

    content = _get_catalog_spa_html()

    tmp_fd, tmp_path_str = tempfile.mkstemp(
        prefix=".tmp-index-",
        suffix=".html",
        dir=str(understand_dir),
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, _PUBLISHED_MODE)
        os.replace(tmp_path, index_path)
    except BaseException:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    return index_path


__all__ = [
    "REQUIRED_ENTRY_KEYS",
    "deploy_catalog_spa",
    "update_catalog",
]
