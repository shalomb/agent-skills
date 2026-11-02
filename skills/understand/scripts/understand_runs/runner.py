# pyright: reportMissingImports=false
"""Report runner executing the plan, discover, converge, and render phases (Spec Units 1 & 4)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import understand_lenses.diff as diff_lens
import understand_lenses.pr as pr_lens
import understand_lenses.topic as topic_lens
from understand_deps.extractor import DependencyGraph, extract_dependencies
from understand_glossary import extract_glossary
from understand_lenses.models import LensFocus
from understand_plan.docs import generate_docs_bundle
from understand_plan.models import Lens
from understand_plan.planner import plan_discovery
from understand_plan.scanner import scan_directory
from understand_render.bundle import load_bundle
from understand_render.run import render_run
from understand_runs.slug import get_repo_root, get_repo_slug, is_git_repo
from understand_runs.storage import create_run_dir, normalize_lens
from understand_runs.urls import format_end_message, get_report_urls
from understand_synth.sections import synthesize_sections

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".cache"}


class GitRequiredError(Exception):
    """Raised when a lens requires a git repository but the target directory has none."""


@dataclass(frozen=True)
class ReportResult:
    run_dir: Path
    lens: Lens
    urls: dict[str, str]
    summary: str
    end_message: str
    focus_set: set[str] = field(default_factory=set)
    seed_nodes: set[str] = field(default_factory=set)
    glossary: Any = None
    dep_graph: Any = None


def parse_command(command_or_args: str) -> Lens:
    """Parses a slash command, CLI flag, or arguments into a Lens."""
    text = command_or_args.strip()
    if text.startswith("--lens"):
        text = text[len("--lens") :].strip()
        if text.startswith("="):
            text = text[1:].strip()
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
    if sub == "full":
        return Lens("full")
    if sub == "topic":
        return Lens("topic", rest or None)
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
    dep_graph: DependencyGraph | None = None,
    focus_set: set[str] | None = None,
    seed_nodes: set[str] | None = None,
    edges: list[Any] | None = None,
    repo_name: str | None = None,
) -> str:
    """Writes a schema-compliant bundle utilizing synthesize_sections and dep_graph."""
    if isinstance(dep_graph, (set, frozenset)):
        actual_focus_set: set[str] | None = set(dep_graph)
        actual_seed_nodes: set[str] | None = (
            set(focus_set) if isinstance(focus_set, (set, frozenset)) else seed_nodes
        )
        actual_edges: list[Any] | None = edges
        actual_dep_graph: DependencyGraph | None = None
    else:
        actual_dep_graph = dep_graph
        actual_focus_set = focus_set
        actual_seed_nodes = seed_nodes
        actual_edges = edges

    if actual_dep_graph is None:
        actual_dep_graph = extract_dependencies(repo_path, files)

    bundle_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = bundle_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    clean_repo_name = repo_name or repo_path.name or "repository"

    # Multi-section markdown generation via synthesize_sections
    sections = synthesize_sections(
        repo_path,
        clean_repo_name,
        folders,
        files,
        dep_graph=actual_dep_graph,
        lens=lens,
        focus_set=actual_focus_set,
        seed_nodes=actual_seed_nodes,
    )
    for filename, content in sections.items():
        (sections_dir / filename).write_text(content, encoding="utf-8")

    # Build graph.json nodes with hub: True/False
    hub_files = (
        set(actual_dep_graph.hubs)
        if actual_dep_graph and hasattr(actual_dep_graph, "hubs")
        else set()
    )
    nodes = []
    for f in files:
        dimmed = (actual_focus_set is not None and f not in actual_focus_set)
        is_hub = f in hub_files
        nodes.append({
            "anchor_id": f,
            "label": Path(f).name,
            "path": f,
            "kind": "file",
            "summary": f"File {f}",
            "dimmed": dimmed,
            "hub": is_hub,
        })
    if not nodes:
        nodes.append({
            "anchor_id": "root",
            "label": clean_repo_name or "root",
            "path": ".",
            "kind": "folder",
            "summary": "Root folder",
            "dimmed": False,
            "hub": False,
        })

    valid_anchors = {n["anchor_id"] for n in nodes}

    # Build graph.json edges from dep_graph.edges with kinds (imports, calls, depends_on)
    raw_edges: list[tuple[str, str, str]] = []
    if actual_dep_graph and hasattr(actual_dep_graph, "edges") and actual_dep_graph.edges:
        raw_edges.extend(actual_dep_graph.edges)
    elif actual_edges:
        for item in actual_edges:
            if len(item) >= 3:
                raw_edges.append((item[0], item[1], item[2]))
            elif len(item) == 2:
                raw_edges.append((item[0], item[1], "imports"))

    valid_kinds = {"imports", "calls", "depends_on"}
    graph_edges = []
    seen_edges = set()
    for s, t, k in raw_edges:
        if s in valid_anchors and t in valid_anchors and s != t:
            kind = k if k in valid_kinds else "imports"
            edge_key = (s, t, kind)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                graph_edges.append({
                    "source": s,
                    "target": t,
                    "kind": kind,
                })

    graph = {
        "schema_version": 1,
        "title": f"Report: {lens.target or lens.type.capitalize()}",
        "nodes": nodes,
        "edges": graph_edges,
    }
    (bundle_dir / "graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    # Validate schema version 1
    load_bundle(bundle_dir)

    if lens.type == "topic":
        summary = f"Topic report on {lens.target} focusing on {len(actual_focus_set or [])} of {len(files)} files."
    elif lens.type == "diff":
        summary = f"Diff report against {lens.target} focusing on {len(actual_focus_set or [])} changed files."
    elif lens.type == "pr":
        summary = f"Pull request report for PR #{lens.target} focusing on {len(actual_focus_set or [])} changed files."
    else:
        summary = f"Full overview of {len(files)} files and {len(folders)} folders."

    return summary


def _execute_phases(
    repo_path: Path,
    source_root: Path,
    parsed_lens: Lens,
    on_phase: Callable[[str], None] | None = None,
    commit: str | None = None,
    base_dir: Path | None = None,
    lens_focus: LensFocus | None = None,
) -> ReportResult:
    """Executes the 4 phases: plan, discover, converge, render."""
    # Phase 1: plan
    if on_phase:
        on_phase("plan")
    prescan = scan_directory(source_root)
    plan = plan_discovery(prescan, parsed_lens)

    # Phase 2: discover
    if on_phase:
        on_phase("discover")
    folders, files = _scan_files_and_folders(source_root)
    dep_graph = extract_dependencies(source_root, files)

    # Compute or complete lens focus (topic, pr, diff, or full)
    focus_set: set[str] = set()
    seed_nodes: set[str] = set()
    edges: list[tuple[str, str]] = [(s, t) for s, t, _ in dep_graph.edges]

    if parsed_lens.type == "topic":
        computed = topic_lens.compute_topic_focus(
            source_root,
            parsed_lens.target or "",
            files=files,
            edges=edges if edges else None,
        )
        focus_set = computed.focus_set
        seed_nodes = computed.seed_nodes
        if not edges:
            edges = computed.metadata.get("edges", [])
    elif parsed_lens.type == "diff":
        if lens_focus is not None:
            focus_set = lens_focus.focus_set
            seed_nodes = lens_focus.seed_nodes
        else:
            computed = diff_lens.compute_diff_focus(source_root, parsed_lens.target or "main")
            focus_set = computed.focus_set
            seed_nodes = computed.seed_nodes
    elif parsed_lens.type == "pr":
        if lens_focus is not None:
            focus_set = lens_focus.focus_set
            seed_nodes = lens_focus.seed_nodes
    else:  # full
        focus_set = set(files)
        seed_nodes = set(files)

    # Phase 3: converge
    if on_phase:
        on_phase("converge")
    temp_bundle_dir = Path(tempfile.mkdtemp(prefix="understand-bundle-"))
    try:
        repo_root = get_repo_root(repo_path)
        repo_name = repo_root.name or source_root.name or "repository"

        if plan.profile == "docs":
            summary = generate_docs_bundle(temp_bundle_dir, source_root, parsed_lens, files)
        else:
            summary = _create_bundle(
                bundle_dir=temp_bundle_dir,
                repo_path=source_root,
                lens=parsed_lens,
                folders=folders,
                files=files,
                dep_graph=dep_graph,
                focus_set=focus_set if parsed_lens.type != "full" else None,
                seed_nodes=seed_nodes if parsed_lens.type != "full" else None,
                edges=edges,
                repo_name=repo_name,
            )

        # Glossary extraction (Step 6)
        glossary_result = extract_glossary(source_root)
        glossary_data = glossary_result.to_json_dict()
        (temp_bundle_dir / "glossary.json").write_text(
            json.dumps(glossary_data, indent=2) + "\n", encoding="utf-8"
        )
        if glossary_result.draft:
            (temp_bundle_dir / "glossary-draft.md").write_text(
                glossary_result.draft, encoding="utf-8"
            )

        # Phase 4: render
        if on_phase:
            on_phase("render")

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
            source_root=source_root,
            out_dir=run_dir,
            mmdc_path="mmdc",
            chromium_path="/usr/bin/chromium-headless-shell",
            log=lambda m: None,
        )

        # Copy glossary bundle files to shadow storage run_dir
        (run_dir / "glossary.json").write_text(
            json.dumps(glossary_data, indent=2) + "\n", encoding="utf-8"
        )
        if glossary_result.draft:
            (run_dir / "glossary-draft.md").write_text(
                glossary_result.draft, encoding="utf-8"
            )

        urls = get_report_urls(repo_slug, lens_id, run_dir.name)
        end_message = format_end_message(repo_slug, lens_id, urls, summary=summary)

        return ReportResult(
            run_dir=run_dir,
            lens=parsed_lens,
            urls=urls,
            summary=summary,
            end_message=end_message,
            focus_set=focus_set,
            seed_nodes=seed_nodes,
            glossary=glossary_result,
            dep_graph=dep_graph,
        )
    finally:
        shutil.rmtree(temp_bundle_dir, ignore_errors=True)


def run_report(
    repo_path: Path | str,
    lens: Lens | str | None = None,
    target: str | None = None,
    on_phase: Callable[[str], None] | None = None,
    commit: str | None = None,
    base_dir: Path | None = None,
    **kwargs: Any,
) -> ReportResult:
    """Executes a report run through the 4 phases: plan, discover, converge, render.

    Integrates topic, PR, and diff lenses.
    """
    path = Path(repo_path)

    if lens is None:
        parsed_lens = Lens("full")
    elif isinstance(lens, str):
        parsed_lens = parse_command(lens)
        if target:
            parsed_lens = Lens(parsed_lens.type, target)
    else:
        parsed_lens = lens

    # Enforce git requirements
    if parsed_lens.type in ("pr", "diff"):
        if not is_git_repo(path):
            if parsed_lens.type == "pr":
                raise GitRequiredError("A pull request report needs a git repository")
            raise GitRequiredError("A diff report needs a git repository")

    # PR Lens: executes discovery and rendering inside detached worktree
    if parsed_lens.type == "pr":
        pr_number = parsed_lens.target or "1"
        pr_meta = kwargs.get("pr_metadata") or pr_lens.fetch_pr_metadata(path, pr_number)
        head_oid = pr_meta.get("headRefOid", "HEAD")
        lens_focus = pr_lens.compute_pr_focus(path, pr_number, pr_meta)

        with pr_lens.pr_worktree_context(path, pr_number, head_oid, base_dir=base_dir) as wt_dir:
            return _execute_phases(
                repo_path=path,
                source_root=wt_dir,
                parsed_lens=parsed_lens,
                on_phase=on_phase,
                commit=commit,
                base_dir=base_dir,
                lens_focus=lens_focus,
            )

    # Diff Lens: computes diff focus against merge-base
    if parsed_lens.type == "diff":
        base_ref = parsed_lens.target or "main"
        lens_focus = diff_lens.compute_diff_focus(path, base_ref)
        return _execute_phases(
            repo_path=path,
            source_root=path,
            parsed_lens=parsed_lens,
            on_phase=on_phase,
            commit=commit,
            base_dir=base_dir,
            lens_focus=lens_focus,
        )

    # Full and Topic lenses
    return _execute_phases(
        repo_path=path,
        source_root=path,
        parsed_lens=parsed_lens,
        on_phase=on_phase,
        commit=commit,
        base_dir=base_dir,
    )


make_report = run_report

__all__ = [
    "GitRequiredError",
    "Lens",
    "ReportResult",
    "make_report",
    "parse_command",
    "run_report",
]

