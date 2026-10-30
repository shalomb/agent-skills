"""Serve-root resolution.

`~/projects` is a symlink to a directory elsewhere (on the VM, a Parallels shared
folder). nginx's `disable_symlinks ... from=$document_root` checks links only
*below* the root it is given, so the root itself must be the real directory:
we resolve the configured root once, when the config is generated, and hand
nginx the resolved path. A link inside the root that leaves it is then refused.
"""

from __future__ import annotations

from pathlib import Path


def resolve_serve_root(configured: Path) -> Path:
    resolved = configured.resolve(strict=True)
    if not resolved.is_dir():
        raise NotADirectoryError(f"serve root is not a directory: {resolved}")
    return resolved
