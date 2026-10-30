# pyright: reportMissingImports=false
"""Pre-scan analyzer that categorizes directories into code, docs, or mixed profiles."""

from __future__ import annotations

import os
from pathlib import Path

from .models import PreScan

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".cache"}

CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".cc",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".kts",
    ".sh",
    ".bash",
    ".zsh",
    ".scala",
    ".m",
    ".mm",
    ".lua",
    ".pl",
    ".sql",
}

DOC_EXTENSIONS = {
    ".md",
    ".markdown",
    ".mdown",
    ".mkdn",
    ".rst",
    ".adoc",
    ".asciidoc",
}


def scan_directory(root: Path) -> PreScan:
    """Scans root directory and computes file counts, distribution, and top directories."""
    code_count = 0
    docs_count = 0
    other_count = 0
    all_files: list[str] = []
    top_dirs_set: set[str] = set()
    depth2_dirs_set: set[str] = set()

    for current, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        curr_p = Path(current)
        try:
            rel = curr_p.relative_to(root)
            parts = rel.parts
            if len(parts) == 1:
                top_dirs_set.add(parts[0])
            elif len(parts) >= 2:
                top_dirs_set.add(parts[0])
                depth2_dirs_set.add(f"{parts[0]}/{parts[1]}")
        except ValueError:
            continue

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            fpath = curr_p / fname
            try:
                rel_f = str(fpath.relative_to(root))
                all_files.append(rel_f)
            except ValueError:
                continue

            suffix = fpath.suffix.lower()
            if suffix in CODE_EXTENSIONS:
                code_count += 1
            elif suffix in DOC_EXTENSIONS:
                docs_count += 1
            else:
                other_count += 1

    return PreScan(
        total_files=len(all_files),
        code_files=code_count,
        docs_files=docs_count,
        other_files=other_count,
        top_directories=sorted(top_dirs_set),
        depth2_directories=sorted(depth2_dirs_set),
        files=sorted(all_files),
    )
