# pyright: reportMissingImports=false
"""Unit tests for understand_runs report execution and command parsing."""

import json
import pytest
from understand_deps.extractor import DependencyGraph
from understand_render.bundle import load_bundle
from understand_runs.runner import (
    GitRequiredError,
    Lens,
    _create_bundle,
    make_report,
    parse_command,
)


def test_parse_command_aliases_and_subcommands():
    # Full lens
    assert parse_command("/understand") == Lens("full")
    assert parse_command("/understand ") == Lens("full")

    # Topic lens
    assert parse_command("/understand onboarding") == Lens("topic", "onboarding")

    # PR lens and alias
    assert parse_command("/understand pr 123") == Lens("pr", "123")
    assert parse_command("/understand-pr 123") == Lens("pr", "123")
    assert parse_command("/understand-pr 123") == parse_command("/understand pr 123")

    # Diff lens and alias
    assert parse_command("/understand diff main") == Lens("diff", "main")
    assert parse_command("/understand-diff main") == Lens("diff", "main")
    assert parse_command("/understand-diff main") == parse_command("/understand diff main")


def test_make_report_emits_phases(temp_cache, git_repo):
    phases = []
    result = make_report(git_repo, Lens("full"), on_phase=phases.append)
    assert phases == ["plan", "discover", "converge", "render"]
    assert result.run_dir.exists()
    assert (result.run_dir / "report.html").exists()
    assert "parallels" in result.urls
    assert "tailnet" in result.urls


def test_non_git_dir_pr_and_diff_fail(non_git_dir):
    with pytest.raises(GitRequiredError) as exc_info:
        make_report(non_git_dir, Lens("pr", "1"))
    assert "needs a git repository" in str(exc_info.value).lower()

    with pytest.raises(GitRequiredError) as exc_diff:
        make_report(non_git_dir, Lens("diff", "main"))
    assert "needs a git repository" in str(exc_diff.value).lower()


def test_non_git_dir_full_and_topic_succeed(temp_cache, non_git_dir):
    full_res = make_report(non_git_dir, Lens("full"))
    assert full_res.run_dir.exists()
    report_html = (full_res.run_dir / "report.html").read_text(encoding="utf-8")
    assert "README.md" in report_html or "docs" in report_html

    topic_res = make_report(non_git_dir, Lens("topic", "onboarding"))
    assert topic_res.run_dir.exists()
    topic_html = (topic_res.run_dir / "report.html").read_text(encoding="utf-8")
    assert "onboarding" in topic_html.lower()
    assert "git history" not in topic_html.lower()


def test_run_leaves_uncommitted_work_as_it_was(temp_cache, git_repo):
    app_ts = git_repo / "src" / "app.ts"
    uncommitted_content = "// modified uncommitted content\nconsole.log('in-flight change');\n"
    app_ts.write_text(uncommitted_content)

    make_report(git_repo, Lens("full"))

    assert app_ts.read_text() == uncommitted_content


def test_create_bundle_synthesizes_sections_and_valid_graph_with_hubs(tmp_path):
    """_create_bundle uses synthesize_sections and dep_graph to build schema v1 bundle."""
    bundle_dir = tmp_path / "bundle"
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    (repo_path / "README.md").write_text("# Test Project\n\nAutomated analysis tool.\n", encoding="utf-8")
    src = repo_path / "src"
    src.mkdir()
    (src / "app.py").write_text("from src.core import engine\n", encoding="utf-8")
    (src / "core.py").write_text("from src.storage import save\n", encoding="utf-8")
    (src / "storage.py").write_text("class Storage: pass\n", encoding="utf-8")

    folders = ["src"]
    files = ["README.md", "src/app.py", "src/core.py", "src/storage.py"]
    dep_graph = DependencyGraph(
        edges=[
            ("src/app.py", "src/core.py", "imports"),
            ("src/core.py", "src/storage.py", "depends_on"),
        ],
        hubs=["src/core.py"],
        metrics={
            "src/core.py": {"in_degree": 3, "out_degree": 1, "in": 3, "out": 1},
        },
    )

    summary = _create_bundle(
        bundle_dir=bundle_dir,
        repo_path=repo_path,
        lens=Lens("full"),
        folders=folders,
        files=files,
        dep_graph=dep_graph,
    )

    assert "Full overview of 4 files and 1 folders." in summary

    # Verify sections generated
    sections_dir = bundle_dir / "sections"
    assert (sections_dir / "01-system-context.md").exists()
    assert (sections_dir / "02-architecture-and-containers.md").exists()
    assert (sections_dir / "03-key-flows-and-dependencies.md").exists()

    # Verify graph.json schema and contents
    graph_path = bundle_dir / "graph.json"
    assert graph_path.exists()
    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))
    assert graph_data["schema_version"] == 1

    nodes_by_path = {n["path"]: n for n in graph_data["nodes"]}
    assert nodes_by_path["src/core.py"]["hub"] is True
    assert nodes_by_path["src/app.py"]["hub"] is False
    assert nodes_by_path["src/storage.py"]["hub"] is False

    # Edges have valid kinds
    edges = graph_data["edges"]
    assert len(edges) == 2
    assert {"source": "src/app.py", "target": "src/core.py", "kind": "imports"} in edges
    assert {"source": "src/core.py", "target": "src/storage.py", "kind": "depends_on"} in edges

    # Verify bundle satisfies schema version 1 via load_bundle
    loaded = load_bundle(bundle_dir)
    assert len(loaded.sections) >= 3
    assert len(loaded.nodes) == 4
    assert len(loaded.edges) == 2


def test_create_bundle_with_topic_lens_generates_topic_section(tmp_path):
    """_create_bundle with topic lens generates 04-topic-focus.md and applies dimming."""
    bundle_dir = tmp_path / "bundle_topic"
    repo_path = tmp_path / "project_topic"
    repo_path.mkdir()

    src = repo_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass\n", encoding="utf-8")
    (src / "other.py").write_text("def unrelated(): pass\n", encoding="utf-8")

    folders = ["src"]
    files = ["src/auth.py", "src/other.py"]
    dep_graph = DependencyGraph(edges=[], hubs=[], metrics={})

    _create_bundle(
        bundle_dir=bundle_dir,
        repo_path=repo_path,
        lens=Lens("topic", "auth"),
        folders=folders,
        files=files,
        dep_graph=dep_graph,
        focus_set={"src/auth.py"},
        seed_nodes={"src/auth.py"},
    )

    sections_dir = bundle_dir / "sections"
    assert (sections_dir / "04-topic-focus.md").exists()

    graph_data = json.loads((bundle_dir / "graph.json").read_text(encoding="utf-8"))
    nodes_by_path = {n["path"]: n for n in graph_data["nodes"]}
    assert nodes_by_path["src/auth.py"]["dimmed"] is False
    assert nodes_by_path["src/other.py"]["dimmed"] is True


def test_make_report_extracts_dependencies_in_phase_2(temp_cache, git_repo):
    """make_report calls extract_dependencies during Phase 2 and includes dep_graph in ReportResult."""
    (git_repo / "src" / "utils.ts").write_text("export function help() {}\n", encoding="utf-8")
    (git_repo / "src" / "app.ts").write_text("import './utils';\nconsole.log('started');\n", encoding="utf-8")

    result = make_report(git_repo, Lens("full"))
    assert result.dep_graph is not None
    assert isinstance(result.dep_graph, DependencyGraph)
    assert (result.run_dir / "report.html").exists()


def test_create_bundle_with_remote_info_attaches_dual_links(tmp_path):
    """_create_bundle passes remote_info to synthesize_sections to emit dual navigation badges."""
    from understand_runs.remote import RemoteInfo

    bundle_dir = tmp_path / "bundle_remote"
    repo_path = tmp_path / "project_remote"
    repo_path.mkdir()
    (repo_path / "README.md").write_text("# Remote App\n", encoding="utf-8")
    src = repo_path / "src"
    src.mkdir()
    (src / "app.py").write_text("import sys\n", encoding="utf-8")

    remote = RemoteInfo(web_base="https://github.com/example-org/my-repo", commit="c0mm1t", host="github")

    _create_bundle(
        bundle_dir=bundle_dir,
        repo_path=repo_path,
        lens=Lens("full"),
        folders=["src"],
        files=["README.md", "src/app.py"],
        remote_info=remote,
    )

    sec1 = (bundle_dir / "sections" / "01-system-context.md").read_text(encoding="utf-8")
    assert "[view online ↗](https://github.com/example-org/my-repo/blob/c0mm1t/src/app.py)" in sec1


def test_make_report_resolves_remote_info_in_report_result(temp_cache, git_repo):
    """make_report resolves remote_info and passes it through ReportResult."""
    import subprocess
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:example-org/my-repo.git"], cwd=git_repo, check=True)
    result = make_report(git_repo, Lens("full"))
    assert result.remote_info is not None
    assert result.remote_info.web_base == "https://github.com/example-org/my-repo"
    assert result.remote_info.host == "github"


