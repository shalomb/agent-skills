# pyright: reportMissingImports=false
"""Architectural Synthesizer module for /understand (Spec Unit 3).

Synthesizes structured Markdown report sections and C4 Mermaid diagrams
adhering to the Uninformed Reader Test (3-minute onboarding prose).
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .c4 import generate_c4_container, generate_c4_context

# Standard ignore patterns when inspecting files
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".cache", "dist", "build"}


def _extract_readme_intent(root: Path, repo_name: str) -> tuple[str, str]:
    """Extracts project intent and a concise short description from README if available."""
    readme_candidates = [
        root / "README.md",
        root / "readme.md",
        root / "README.rst",
        root / "README.txt",
        root / "README",
    ]

    for candidate in readme_candidates:
        if candidate.is_file():
            try:
                raw_text = candidate.read_text(encoding="utf-8", errors="replace")
                lines = raw_text.splitlines()

                # Filter out badges, HTML comments, and empty lines
                filtered_paras: list[str] = []
                cur_para: list[str] = []

                for line in lines:
                    trimmed = line.strip()
                    if not trimmed:
                        if cur_para:
                            filtered_paras.append(" ".join(cur_para))
                            cur_para = []
                        continue
                    # Skip markdown badges: [![...](...)]
                    if re.match(r"^\[!\[.*\]\(.*\)\]\(.*\)$", trimmed) or re.match(r"^!\[.*\]\(.*\)$", trimmed):
                        continue
                    # Skip HTML comments
                    if trimmed.startswith("<!--") and trimmed.endswith("-->"):
                        continue
                    # Skip main headings
                    if trimmed.startswith("#"):
                        if cur_para:
                            filtered_paras.append(" ".join(cur_para))
                            cur_para = []
                        continue
                    cur_para.append(trimmed)

                if cur_para:
                    filtered_paras.append(" ".join(cur_para))

                if filtered_paras:
                    # Choose up to the first 2 informative paragraphs
                    intent = "\n\n".join(filtered_paras[:2])
                    # Create short description for C4 System macro
                    first_para = filtered_paras[0]
                    first_sentence = first_para.split(". ")[0].strip()
                    if len(first_sentence) > 120:
                        first_sentence = first_sentence[:117] + "..."
                    short_desc = first_sentence if first_sentence else f"Core system for {repo_name}"
                    return intent, short_desc
            except OSError:
                pass

    # Default fallback intent when no README is present
    intent = (
        f"The **{repo_name}** repository provides core application components, domain logic, "
        f"and operational workflows. It organizes capabilities across modular subsystems designed "
        f"for reliability, maintainability, and clear separation of concerns."
    )
    short_desc = f"Core software system for {repo_name}"
    return intent, short_desc


def _detect_tech_stack(root: Path, files: list[str]) -> dict[str, list[str]]:
    """Detects primary languages, frameworks, and tooling from repository files and manifests."""
    ext_counts: dict[str, int] = {}
    files_set = set(files)

    for f in files:
        suffix = Path(f).suffix.lower()
        if suffix:
            ext_counts[suffix] = ext_counts.get(suffix, 0) + 1

    languages: list[str] = []
    if any(ext in ext_counts for ext in (".py", ".pyi")):
        count = ext_counts.get(".py", 0) + ext_counts.get(".pyi", 0)
        languages.append(f"Python ({count} files)")
    if any(ext in ext_counts for ext in (".ts", ".tsx")):
        count = ext_counts.get(".ts", 0) + ext_counts.get(".tsx", 0)
        languages.append(f"TypeScript ({count} files)")
    if any(ext in ext_counts for ext in (".js", ".jsx", ".mjs", ".cjs")):
        count = sum(ext_counts.get(e, 0) for e in (".js", ".jsx", ".mjs", ".cjs"))
        languages.append(f"JavaScript ({count} files)")
    if ".rs" in ext_counts:
        languages.append(f"Rust ({ext_counts['.rs']} files)")
    if ".go" in ext_counts:
        languages.append(f"Go ({ext_counts['.go']} files)")
    if any(ext in ext_counts for ext in (".sh", ".bash")):
        count = ext_counts.get(".sh", 0) + ext_counts.get(".bash", 0)
        languages.append(f"Shell Scripting ({count} files)")
    if any(ext in ext_counts for ext in (".html", ".css")):
        count = ext_counts.get(".html", 0) + ext_counts.get(".css", 0)
        languages.append(f"Web Front-End ({count} files)")
    if not languages:
        languages.append("General Software / Mixed Languages")

    frameworks: list[str] = []
    tooling: list[str] = []

    # Inspect pyproject.toml / requirements.txt
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            content = pyproject_path.read_text(encoding="utf-8", errors="replace").lower()
            if "fastapi" in content:
                frameworks.append("FastAPI")
            if "click" in content:
                frameworks.append("Click")
            if "pydantic" in content:
                frameworks.append("Pydantic")
            if "pytest" in content:
                frameworks.append("Pytest")
            if "pytest-bdd" in content or "bdd" in content:
                frameworks.append("Pytest-BDD")
            if "django" in content:
                frameworks.append("Django")
            if "flask" in content:
                frameworks.append("Flask")
        except OSError:
            pass

    # Inspect package.json
    package_json = root / "package.json"
    if package_json.is_file():
        try:
            p_content = package_json.read_text(encoding="utf-8", errors="replace").lower()
            if "react" in p_content:
                frameworks.append("React")
            if "vue" in p_content:
                frameworks.append("Vue.js")
            if "express" in p_content:
                frameworks.append("Express")
            if "cytoscape" in p_content:
                frameworks.append("Cytoscape.js")
            if "mermaid" in p_content:
                frameworks.append("Mermaid.js")
            if "jest" in p_content or "vitest" in p_content:
                frameworks.append("Vitest/Jest")
        except OSError:
            pass

    # Inspect tooling files
    if any(f.startswith(".github/") for f in files):
        tooling.append("GitHub Actions CI/CD")
    if "Dockerfile" in files_set or "docker-compose.yml" in files_set or "docker-compose.yaml" in files_set:
        tooling.append("Docker")
    if "uv.lock" in files_set or "pyproject.toml" in files_set:
        tooling.append("uv / Python Packaging")
    if "package-lock.json" in files_set or "pnpm-lock.yaml" in files_set or "yarn.lock" in files_set:
        tooling.append("Node.js Package Manager")

    if not frameworks:
        frameworks.append("Standard Language Libraries & Modular APIs")
    if not tooling:
        tooling.append("Git Version Control")

    return {
        "Languages": languages,
        "Frameworks": frameworks,
        "Tooling": tooling,
    }


def _detect_entry_points(root: Path, files: list[str]) -> list[dict[str, str]]:
    """Identifies primary entry points (CLI, API servers, library roots, configurations)."""
    entry_candidates: list[dict[str, str]] = []

    # Priority rules
    for f in sorted(files):
        p = Path(f)
        name_lower = p.name.lower()
        parts = [part.lower() for part in p.parts]

        if name_lower in ("cli.py", "__main__.py", "main.py", "app.py", "run.py") and "test" not in parts:
            entry_candidates.append({
                "path": f,
                "kind": "CLI / Execution Entry Point",
                "description": f"Executable command driver or application launch script ({p.name})",
            })
        elif name_lower in ("server.py", "api.py", "routes.py") and "test" not in parts:
            entry_candidates.append({
                "path": f,
                "kind": "API / Server Entry Point",
                "description": f"HTTP service or request handling endpoint ({p.name})",
            })
        elif name_lower in ("index.ts", "index.js", "main.ts", "main.go", "main.rs") and "test" not in parts:
            entry_candidates.append({
                "path": f,
                "kind": "Primary Application Entry Point",
                "description": f"Root module initializing runtime workflows ({p.name})",
            })
        elif name_lower == "__init__.py" and len(p.parts) == 2 and p.parts[0] in ("src", "lib"):
            entry_candidates.append({
                "path": f,
                "kind": "Package Root API",
                "description": f"Public package boundary exposing core interfaces ({p.parent})",
            })
        elif p.suffix in (".sh", ".bash") and ("scripts" in parts or "bin" in parts):
            entry_candidates.append({
                "path": f,
                "kind": "Automation Script",
                "description": f"Shell script driving operational workflows ({p.name})",
            })

    # Add configuration entry point if present
    for cfg in ("pyproject.toml", "package.json", "Cargo.toml", "go.mod"):
        if cfg in files:
            entry_candidates.append({
                "path": cfg,
                "kind": "Build & Project Configuration",
                "description": f"Primary project manifest and dependency specification ({cfg})",
            })
            break

    return entry_candidates[:8]


def _detect_external_systems(root: Path, folders: list[str], files: list[str]) -> list[tuple[str, str, str]]:
    """Detects external systems and third-party integrations for C4Context."""
    ext_systems: list[tuple[str, str, str]] = []
    seen_names: set[str] = set()

    def add_ext(name: str, desc: str, rel: str):
        if name not in seen_names:
            seen_names.add(name)
            ext_systems.append((name, desc, rel))

    # Check for GitHub / VCS
    if any(f.startswith(".github/") for f in files) or ".github" in folders:
        add_ext("GitHub", "Remote version control, pull requests, and CI/CD automation", "Reads PR metadata and triggers workflows")

    # Check for Storage / Database
    has_db = False
    for f in files:
        f_lower = f.lower()
        if any(db in f_lower for db in ("sqlite", "postgres", "redis", "mysql", "mongo", "database", "storage")):
            has_db = True
            break
    if has_db:
        add_ext("Persistent Storage", "Relational database or persistent file cache", "Reads and writes records")

    # Local runtime and shadow cache
    add_ext("Local File System", "User cache directory and local repository worktrees", "Reads sources and writes report artifacts")

    # Third party services if external calls present
    for f in files:
        f_lower = f.lower()
        if "http" in f_lower or "api" in f_lower or "client" in f_lower:
            add_ext("External Web APIs", "Upstream HTTP services and external network endpoints", "Sends HTTPS requests")
            break

    return ext_systems[:4]


def _detect_subsystems_and_containers(
    repo_name: str, folders: list[str], files: list[str], languages_summary: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extracts major directory subsystems and derives logical C4 containers."""
    top_dirs: dict[str, list[str]] = {}
    for f in files:
        parts = Path(f).parts
        if len(parts) > 1:
            top_dirs.setdefault(parts[0], []).append(f)
        else:
            top_dirs.setdefault(".", []).append(f)

    subsystems: list[dict[str, Any]] = []
    role_map = {
        "src": ("Core Application", "Domain models, analysis engines, and business rules"),
        "lib": ("Core Library", "Reusable modules, data structures, and algorithms"),
        "scripts": ("Automation & CLI", "Command line interfaces, utilities, and build scripts"),
        "server": ("Network & Services", "HTTP server daemons, networking handlers, and web delivery"),
        "tests": ("Verification & Test Suite", "Unit tests, integration scenarios, and fixtures"),
        "docs": ("Documentation & Architecture", "Specifications, architectural decisions, and guides"),
        "assets": ("Static Assets & Vendor Bundles", "Stylesheets, bundled frontend libraries, and icons"),
        "server/report_server": ("Report Server Daemon", "Lightweight HTTP server serving reports and views"),
    }

    for dir_name, dir_files in sorted(top_dirs.items(), key=lambda x: -len(x[1])):
        if dir_name == ".":
            continue
        role_info = role_map.get(dir_name)
        if not role_info:
            role_info = (f"{dir_name.capitalize()} Subsystem", f"Specialized modules under {dir_name}/")

        subsystems.append({
            "path": f"{dir_name}/",
            "name": role_info[0],
            "description": role_info[1],
            "file_count": len(dir_files),
        })

    # Derive logical containers
    containers: list[dict[str, Any]] = []

    # 1. CLI or UI Container
    has_cli = any(
        f.startswith("scripts/") or Path(f).name.lower() in ("cli.py", "main.py", "app.py")
        for f in files
    )
    if has_cli:
        containers.append({
            "name": "CLI Application",
            "alias": "cli",
            "type": "cli",
            "techn": languages_summary,
            "descr": "Command-line interface and workflow execution entry point",
            "entry_point": True,
        })

    # 2. Server or Web Container
    has_server = any(f.startswith("server/") or "server" in f.lower() for f in files)
    if has_server:
        containers.append({
            "name": "Report Server",
            "alias": "server",
            "type": "api",
            "techn": "Python / HTTP Daemon",
            "descr": "Serves interactive reports, source views, and API endpoints",
            "entry_point": True,
        })

    # 3. Core Engine Container
    containers.append({
        "name": "Core Engine",
        "alias": "core",
        "type": "core",
        "techn": languages_summary,
        "descr": "Encapsulates domain logic, analysis pipeline, and synthesis models",
        "entry_point": False,
    })

    # 4. Storage Container
    has_storage = any(
        any(k in f.lower() for k in ("storage", "db", "cache", "sqlite", "model", "records"))
        for f in files
    )
    if has_storage or True:  # Always include persistence/storage layer for C4
        containers.append({
            "name": "Shadow Storage",
            "alias": "storage",
            "type": "database",
            "techn": "File System / Cache",
            "descr": "Persists generated reports, graphs, indices, and session caches",
            "is_db": True,
        })

    # 5. Test Suite Container if tests exist
    if any(f.startswith("tests/") for f in files):
        containers.append({
            "name": "Test Suite & Harness",
            "alias": "tests",
            "type": "service",
            "techn": "Pytest / BDD",
            "descr": "Validates behavioral scenarios and architectural invariants",
            "entry_point": False,
        })

    return subsystems, containers


def _format_hub_narrative(hubs: list[str], metrics: dict[str, dict[str, int]]) -> str:
    """Produces clear, professional onboarding prose analyzing central hub files."""
    if not hubs:
        return (
            "The dependency topology demonstrates low architectural coupling. "
            "No single file exceeds the centrality threshold, indicating modular separation "
            "and shallow dependency hierarchies across subsystems."
        )

    rows: list[str] = [
        "| Hub File | In-Degree (Fan-In) | Out-Degree (Fan-Out) | Centrality Role & Coupling Impact |",
        "|---|---|---|---|",
    ]

    for hub in hubs:
        m = metrics.get(hub, {})
        in_deg = m.get("in_degree", m.get("in", 0))
        out_deg = m.get("out_degree", m.get("out", 0))
        role = "Shared utility / core abstraction"
        if "model" in hub.lower():
            role = "Data contracts & domain entities"
        elif "storage" in hub.lower() or "db" in hub.lower():
            role = "Persistence contract & storage engine"
        elif "app" in hub.lower() or "core" in hub.lower():
            role = "Central orchestration hub"

        rows.append(
            f"| `{hub}` | **{in_deg}** dependents | {out_deg} dependencies | {role} |"
        )

    table_md = "\n".join(rows)

    prose = (
        f"{table_md}\n\n"
        f"### Hub Architectural Impact\n"
        f"Files with high fan-in (`in-degree >= 3`) represent central coordination points. "
        f"Because numerous downstream components depend directly on their interfaces, modifications "
        f"to these hub modules carry significant blast radius and require thorough test coverage."
    )
    return prose


def _synthesize_lens_section(
    repo_name: str,
    files: list[str],
    dep_graph: Any,
    lens: Any,
    focus_set: set[str] | None = None,
    seed_nodes: set[str] | None = None,
) -> tuple[str, str] | None:
    """Generates tailored focus section (04-topic-focus.md, 04-diff-focus.md, 04-pr-focus.md)."""
    if lens is None:
        return None

    # Extract lens type and target
    lens_type: str = "full"
    lens_target: str = ""
    cur_seed_nodes: set[str] = set(seed_nodes) if seed_nodes is not None else set()
    cur_focus_set: set[str] = set(focus_set) if focus_set is not None else set()
    metadata: dict[str, Any] = {}

    if hasattr(lens, "lens_type"):
        lens_type = str(lens.lens_type).lower()
        if not cur_seed_nodes:
            cur_seed_nodes = set(getattr(lens, "seed_nodes", set()))
        if not cur_focus_set:
            cur_focus_set = set(getattr(lens, "focus_set", set()))
        metadata = dict(getattr(lens, "metadata", {}))
        lens_target = str(metadata.get("target") or metadata.get("base_ref") or metadata.get("pr_number") or "")
    elif hasattr(lens, "type"):
        lens_type = str(lens.type).lower()
        lens_target = str(getattr(lens, "target", "") or "")
    elif isinstance(lens, str):
        lens_type = lens.lower()
    elif isinstance(lens, dict):
        lens_type = str(lens.get("lens_type") or lens.get("type") or "full").lower()
        lens_target = str(lens.get("target") or "")
        if not cur_seed_nodes:
            cur_seed_nodes = set(lens.get("seed_nodes", set()))
        if not cur_focus_set:
            cur_focus_set = set(lens.get("focus_set", set()))
        metadata = dict(lens.get("metadata", {}))

    if lens_type in ("full", "", "none"):
        return None

    # Infer seed nodes if empty
    if not cur_seed_nodes and lens_target:
        clean_target = lens_target.lower()
        for f in files:
            if clean_target in f.lower():
                cur_seed_nodes.add(f)
        if not cur_seed_nodes and files:
            cur_seed_nodes.add(files[0])

    # Infer 1-hop neighbours from graph edges
    edges: list[tuple[str, str, str]] = []
    if hasattr(dep_graph, "edges"):
        edges = list(getattr(dep_graph, "edges"))
    elif isinstance(dep_graph, dict):
        raw_edges = dep_graph.get("edges", [])
        for e in raw_edges:
            if isinstance(e, dict):
                edges.append((e.get("source", ""), e.get("target", ""), e.get("kind", "imports")))
            elif isinstance(e, (tuple, list)) and len(e) >= 2:
                edges.append((e[0], e[1], e[2] if len(e) > 2 else "imports"))

    one_hop_neighbours: set[str] = set()
    if cur_focus_set and cur_seed_nodes and cur_focus_set != cur_seed_nodes:
        one_hop_neighbours = cur_focus_set - cur_seed_nodes
    else:
        for s, t, _ in edges:
            if s in cur_seed_nodes and t not in cur_seed_nodes:
                one_hop_neighbours.add(t)
            if t in cur_seed_nodes and s not in cur_seed_nodes:
                one_hop_neighbours.add(s)

    combined_focus = cur_seed_nodes | one_hop_neighbours
    if not cur_focus_set:
        cur_focus_set = combined_focus

    filename = f"04-{lens_type}-focus.md"

    if lens_type == "topic":
        title = f"Topic Focus: {lens_target or 'Target Subsystem'}"
        seeds_list = "\n".join(f"- `{s}`" for s in sorted(cur_seed_nodes)) if cur_seed_nodes else "- (none discovered)"
        neighbours_list = "\n".join(f"- `{n}`" for n in sorted(one_hop_neighbours)) if one_hop_neighbours else "- (no external 1-hop neighbours)"

        content = (
            f"# {title}\n\n"
            f"## Exploration Scope\n"
            f"This focused section isolates the architectural footprint relevant to **{lens_target}**. "
            f"Peripheral components outside this scope are dimmed in graph visualisations.\n\n"
            f"### Seed Nodes\n"
            f"Files directly matching the topic query through symbols, paths, or module definitions:\n\n"
            f"{seeds_list}\n\n"
            f"### 1-Hop Neighbours\n"
            f"Directly connected callers and callees linked to the seed nodes:\n\n"
            f"{neighbours_list}\n\n"
            f"## Impact Analysis\n"
            f"The identified topic subsystem touches **{len(combined_focus)}** files out of **{len(files)}** total files "
            f"in `{repo_name}`. Key interactions occur along the dependency boundaries listed above.\n\n"
            f"> **Reviewer Guide**: Begin by examining the seed nodes for primary business logic, "
            f"then inspect 1-hop neighbours to verify boundary contract adherence.\n"
        )
    elif lens_type == "diff":
        title = f"Diff Focus: Changes against {lens_target or 'Base'}"
        changed_list = "\n".join(f"- `{s}`" for s in sorted(cur_seed_nodes)) if cur_seed_nodes else "- (working tree clean)"
        impact_list = "\n".join(f"- `{n}`" for n in sorted(one_hop_neighbours)) if one_hop_neighbours else "- (no direct downstream dependents)"

        content = (
            f"# {title}\n\n"
            f"## Diff Inspection Scope\n"
            f"This section analyzes working tree modifications against **{lens_target or 'base branch'}**. "
            f"It captures local uncommitted work and branch commits while ignoring base drift.\n\n"
            f"### Changed Files in Focus Set\n"
            f"{changed_list}\n\n"
            f"### 1-Hop Impacted Dependents\n"
            f"Directly connected modules potentially impacted by these changes:\n\n"
            f"{impact_list}\n\n"
            f"## Impact & Risk Assessment\n"
            f"A total of **{len(cur_seed_nodes)}** files have been modified. Reviewers should verify that "
            f"the 1-hop dependents maintain compatibility with updated interfaces.\n\n"
            f"> **Verification Checklist**: Run targeted unit tests covering both the changed files "
            f"and their immediate 1-hop dependents before merging.\n"
        )
    elif lens_type == "pr":
        pr_id = metadata.get("pr_number") or lens_target or "Active"
        pr_title = metadata.get("title", f"Pull Request #{pr_id}")
        title = f"Pull Request Focus: #{pr_id} - {pr_title}"
        changed_list = "\n".join(f"- `{s}`" for s in sorted(cur_seed_nodes)) if cur_seed_nodes else "- (none)"
        impact_list = "\n".join(f"- `{n}`" for n in sorted(one_hop_neighbours)) if one_hop_neighbours else "- (no direct downstream callers)"

        content = (
            f"# {title}\n\n"
            f"## Pull Request Review Scope\n"
            f"This section analyzes PR **#{pr_id}** evaluated in a detached shadow worktree. "
            f"Working directory and local branch state remain completely unaffected.\n\n"
            f"### Changed Files Under Review\n"
            f"{changed_list}\n\n"
            f"### Downstream 1-Hop Impact\n"
            f"{impact_list}\n\n"
            f"## Reviewer Guidance & Architectural Impact\n"
            f"Reviewers should verify that modified domain models preserve existing contracts "
            f"and that downstream dependents compile and pass automated tests.\n"
        )
    else:
        title = f"Lens Focus: {lens_type.capitalize()}"
        content = (
            f"# {title}\n\n"
            f"Tailored analysis for lens `{lens_type}`.\n\n"
            f"### Focus Set Files\n"
            + "\n".join(f"- `{f}`" for f in sorted(cur_seed_nodes or files[:15]))
            + "\n"
        )

    return filename, content


def synthesize_sections(
    root: Path,
    repo_name: str,
    folders: list[str],
    files: list[str],
    dep_graph: Any = None,
    lens: Any = None,
    focus_set: set[str] | None = None,
    seed_nodes: set[str] | None = None,
) -> dict[str, str]:
    """Synthesizes structured Markdown report sections and C4 Mermaid diagrams.

    Adheres strictly to the Uninformed Reader Test (clear 3-minute onboarding prose).

    Args:
        root: Target repository root path.
        repo_name: Clean repository name.
        folders: List of repository-relative directory paths.
        files: List of repository-relative file paths.
        dep_graph: Optional DependencyGraph or dict with edges, hubs, and metrics.
        lens: Optional Lens specification (Lens, LensFocus, or dict).
        focus_set: Optional precomputed set of file paths in lens focus.
        seed_nodes: Optional precomputed set of seed file paths.

    Returns:
        Mapping of section filename (e.g. "01-system-context.md") to Markdown content.
    """
    sections: dict[str, str] = {}

    # Extract intent and tech stack
    intent, short_desc = _extract_readme_intent(root, repo_name)
    tech_stack = _detect_tech_stack(root, files)
    entry_points = _detect_entry_points(root, files)
    ext_systems = _detect_external_systems(root, folders, files)

    # -------------------------------------------------------------
    # 01-system-context.md
    # -------------------------------------------------------------
    c4_context_diagram = generate_c4_context(repo_name, short_desc, ext_systems)

    tech_table = [
        "| Category | Detected Technologies & Frameworks | Evidence & File Manifest |",
        "|---|---|---|",
        f"| **Languages** | {', '.join(tech_stack['Languages'])} | Discovered in repository files |",
        f"| **Frameworks** | {', '.join(tech_stack['Frameworks'])} | Configured dependencies |",
        f"| **Tooling & CI** | {', '.join(tech_stack['Tooling'])} | Infrastructure manifests |",
    ]
    tech_table_md = "\n".join(tech_table)

    entry_points_md = "\n".join(
        f"- `{ep['path']}` (**{ep['kind']}**): {ep['description']}"
        for ep in entry_points
    ) if entry_points else "- *(No dedicated CLI or server entry points identified; modular library structure)*"

    sec1_content = (
        f"# System Context: {repo_name}\n\n"
        f"## Purpose & System Intent\n"
        f"{intent}\n\n"
        f"## Detected Technology Stack\n"
        f"{tech_table_md}\n\n"
        f"## System Context Architecture\n"
        f"The following C4 System Context diagram illustrates the system boundaries, users, and external integrations:\n\n"
        f"```mermaid\n"
        f"{c4_context_diagram}\n"
        f"```\n\n"
        f"## Primary Entry Points\n"
        f"The codebase exposes the following primary entry points for invocation, execution, and integration:\n\n"
        f"{entry_points_md}\n\n"
        f"> **Onboarding Note**: When exploring this repository for the first time, start with the primary entry "
        f"points above to follow the execution flow into internal domain logic.\n"
    )
    sections["01-system-context.md"] = sec1_content

    # -------------------------------------------------------------
    # 02-architecture-and-containers.md
    # -------------------------------------------------------------
    primary_lang = tech_stack["Languages"][0].split()[0] if tech_stack["Languages"] else "Software"
    subsystems, containers = _detect_subsystems_and_containers(repo_name, folders, files, primary_lang)
    c4_container_diagram = generate_c4_container(repo_name, containers)

    subsystems_table = [
        "| Subsystem Directory | Architectural Role | File Count | Responsibilities |",
        "|---|---|---|---|",
    ]
    for sub in subsystems:
        subsystems_table.append(
            f"| `{sub['path']}` | **{sub['name']}** | {sub['file_count']} files | {sub['description']} |"
        )
    subsystems_table_md = "\n".join(subsystems_table) if subsystems else "- *(Single root directory structure)*"

    container_breakdown = "\n".join(
        f"- **{c['name']}** (`{c['techn']}`): {c['descr']}"
        for c in containers
    )

    sec2_content = (
        f"# Architecture & Containers: {repo_name}\n\n"
        f"## Architectural Overview\n"
        f"The `{repo_name}` system is decomposed into modular, isolated containers with clean interface contracts. "
        f"Incoming requests flow through entry adapters, delegate to domain orchestration engines, and interact with "
        f"persistent storage caches.\n\n"
        f"## Major Subsystems\n"
        f"The codebase is partitioned into the following major top-level directory modules:\n\n"
        f"{subsystems_table_md}\n\n"
        f"## Container Breakdown\n"
        f"The system architecture is structured around the following core logical building blocks:\n\n"
        f"{container_breakdown}\n\n"
        f"### C4 Container Architecture Diagram\n\n"
        f"```mermaid\n"
        f"{c4_container_diagram}\n"
        f"```\n\n"
        f"> **Architectural Boundary Rule**: Application containers communicate strictly through public APIs "
        f"and structured models. State persistence is isolated to storage containers to preserve modularity.\n"
    )
    sections["02-architecture-and-containers.md"] = sec2_content

    # -------------------------------------------------------------
    # 03-key-flows-and-dependencies.md
    # -------------------------------------------------------------
    hubs: list[str] = []
    metrics: dict[str, dict[str, int]] = {}
    edges_count: int = 0

    if hasattr(dep_graph, "hubs"):
        hubs = list(getattr(dep_graph, "hubs"))
    elif isinstance(dep_graph, dict):
        hubs = list(dep_graph.get("hubs", []))

    if hasattr(dep_graph, "metrics"):
        metrics = dict(getattr(dep_graph, "metrics"))
    elif isinstance(dep_graph, dict):
        metrics = dict(dep_graph.get("metrics", {}))

    if hasattr(dep_graph, "edges"):
        edges_count = len(getattr(dep_graph, "edges"))
    elif isinstance(dep_graph, dict):
        edges_count = len(dep_graph.get("edges", []))

    hub_analysis_prose = _format_hub_narrative(hubs, metrics)

    sec3_content = (
        f"# Key Flows & Dependencies\n\n"
        f"## Dependency Flow Narrative\n"
        f"The repository topology contains **{edges_count}** static dependency relationships across "
        f"**{len(files)}** files. Execution control typically flows from external CLI drivers or HTTP "
        f"controllers down through core processing modules and out to persistent storage adapters.\n\n"
        f"## Central Hub Analysis\n"
        f"{hub_analysis_prose}\n\n"
        f"## Critical Paths & Architectural Invariants\n"
        f"The primary execution path traverses entry interfaces directly into central domain models. "
        f"Because these pathways coordinate state transformations, they represent the critical path for "
        f"both performance and regression risks.\n\n"
        f"> **Critical Path Callout**: Ensure that modifications to hub modules are accompanied by unit "
        f"and integration tests to prevent cascading regressions across downstream consumers.\n"
    )
    sections["03-key-flows-and-dependencies.md"] = sec3_content

    # -------------------------------------------------------------
    # Lens Focus Section (if topic, diff, or pr lens)
    # -------------------------------------------------------------
    lens_result = _synthesize_lens_section(
        repo_name, files, dep_graph, lens, focus_set=focus_set, seed_nodes=seed_nodes
    )
    if lens_result:
        filename, content = lens_result
        sections[filename] = content

    return sections
