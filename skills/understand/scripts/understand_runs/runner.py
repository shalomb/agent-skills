# pyright: reportMissingImports=false
"""Report runner executing the plan, discover, converge, and render phases (Spec Units 1 & 4)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from understand_render.run import render_run
from understand_runs.slug import get_repo_root, get_repo_slug, is_git_repo
from understand_runs.storage import create_run_dir, normalize_lens
from understand_runs.urls import format_end_message, get_report_urls

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".cache"}


class GitRequiredError(Exception):
    """Raised when a lens requires a git repository but the target directory has none."""


@dataclass(frozen=True)
class Lens:
    type: str  # "full" | "topic" | "pr" | "diff"
    target: str | None = None


@dataclass(frozen=True)
class ReportResult:
    run_dir: Path
    lens: Lens
    urls: dict[str, str]
    summary: str
    end_message: str


def parse_command(command_or_args: str) -> Lens:
    """Parses a slash command or arguments into a Lens."""
    text = command_or_args.strip()
    if text.startswith("/understand-pr"):
        arg = text[len("/understand-pr") :].strip()
        return Lens("pr", arg or None)
    if text.startswith("/understand-diff"):
        arg = text[len("/understand-diff") :].strip()
        return Lens("diff", arg or None)
    if text.startswith("/understand"):
        text = text[len("/understand") :].strip()

    if not text:
        return Lens("full")

    parts = text.split(maxsplit=1)
    sub = parts[0]
    rest = parts[1].strip() if len(parts) > 1 else ""

    if sub == "pr":
        return Lens("pr", rest or None)
    if sub == "diff":
        return Lens("diff", rest or None)
    return Lens("topic", text)


def _scan_files_and_folders(root: Path) -> tuple[list[str], list[str]]:
    """Discovers files and folders under root without modifying anything."""
    files: list[str] = []
    folders: list[str] = []
    for current, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        curr_p = Path(current)
        try:
            rel = curr_p.relative_to(root)
            if str(rel) != ".":
                folders.append(str(rel))
        except ValueError:
            continue
        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            fpath = curr_p / fname
            try:
                rel_f = fpath.relative_to(root)
                files.append(str(rel_f))
            except ValueError:
                continue
    return sorted(folders), sorted(files)


def _create_bundle(
    bundle_dir: Path,
    repo_path: Path,
    lens: Lens,
    folders: list[str],
    files: list[str],
) -> str:
    """Writes a minimal schema-compliant bundle for the repository and lens."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = bundle_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    nodes = []
    for f in files[:20]:
        nodes.append({
            "anchor_id": f.replace("/", "-").replace(".", "-"),
            "label": Path(f).name,
            "path": f,
            "kind": "file",
            "summary": f"File {f}",
        })
    if not nodes:
        nodes.append({
            "anchor_id": "root",
            "label": repo_path.name or "root",
            "path": "",
            "kind": "folder",
            "summary": "Root folder",
        })

    graph = {
        "schema_version": 1,
        "title": f"Report: {lens.target or lens.type.capitalize()}",
        "nodes": nodes,
        "edges": [],
    }
    (bundle_dir / "graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    if lens.type == "topic":
        title = f"Topic: {lens.target}"
        content = (
            f"# {title}\n\n"
            f"This topic report focuses on **{lens.target}**.\n\n"
            f"### Files examined\n"
            + "\n".join(f"- `{f}`" for f in files[:30])
        )
        summary = f"Topic report on {lens.target} covering {len(files)} files."
    else:
        title = "Repository Structure"
        folders_list = "\n".join(f"- `{f}/`" for f in folders[:15]) if folders else "- (root only)"
        files_list = "\n".join(f"- `{f}`" for f in files[:30]) if files else "- (empty)"
        content = (
            f"# {title}\n\n"
            f"### Folders\n{folders_list}\n\n"
            f"### Files\n{files_list}\n"
        )
        summary = f"Full overview of {len(files)} files and {len(folders)} folders."

    (sections_dir / "01-overview.md").write_text(content + "\n", encoding="utf-8")
    return summary


def make_report(
    repo_path: Path,
    lens: Lens | str,
    target: str | None = None,
    on_phase: Callable[[str], None] | None = None,
    commit: str | None = None,
    base_dir: Path | None = None,
) -> ReportResult:
    """Executes a report run through the 4 phases: plan, discover, converge, render."""
    if isinstance(lens, str):
        parsed_lens = parse_command(lens)
        if target:
            parsed_lens = Lens(parsed_lens.type, target)
    else:
        parsed_lens = lens

    # Enforce git requirements
    if parsed_lens.type in ("pr", "diff"):
        if not is_git_repo(repo_path):
            if parsed_lens.type == "pr":
                raise GitRequiredError("A pull request report needs a git repository")
            raise GitRequiredError("A diff report needs a git repository")

    # Phase 1: plan
    if on_phase:
        on_phase("plan")

    # Phase 2: discover
    if on_phase:
        on_phase("discover")
    folders, files = _scan_files_and_folders(repo_path)

    # Phase 3: converge
    if on_phase:
        on_phase("converge")
    temp_bundle_dir = Path(tempfile.mkdtemp(prefix="understand-bundle-"))
    try:
        summary = _create_bundle(temp_bundle_dir, repo_path, parsed_lens, folders, files)

        # Phase 4: render
        if on_phase:
            on_phase("render")

        repo_root = get_repo_root(repo_path)
        repo_slug = get_repo_slug(repo_root)
        lens_id = normalize_lens(parsed_lens.type, parsed_lens.target)
        run_dir = create_run_dir(
            repo_root,
            lens=parsed_lens.type,
            target=parsed_lens.target,
            commit=commit,
            base_dir=base_dir,
        )

        render_run(
            temp_bundle_dir,
            source_root=repo_path,
            out_dir=run_dir,
            mmdc_path="mmdc",
            chromium_path="/usr/bin/chromium-headless-shell",
            log=lambda m: None,
        )

        urls = get_report_urls(repo_slug, lens_id, run_dir.name)
        end_message = format_end_message(repo_slug, lens_id, urls, summary=summary)

        return ReportResult(
            run_dir=run_dir,
            lens=parsed_lens,
            urls=urls,
            summary=summary,
            end_message=end_message,
        )
    finally:
        shutil.rmtree(temp_bundle_dir, ignore_errors=True)
