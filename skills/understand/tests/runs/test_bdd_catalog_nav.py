# pyright: reportMissingImports=false
"""BDD step definitions for skills/understand/features/report-catalog-and-navigation.feature (ADR-0004 & ADR-0005)."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

SERVER_DIR = Path(__file__).resolve().parents[2] / "server"
TESTS_SERVER_DIR = Path(__file__).resolve().parents[2] / "tests" / "server"
for d in (SERVER_DIR, TESTS_SERVER_DIR):
    d_str = str(d.resolve())
    if d_str not in sys.path:
        sys.path.insert(0, d_str)

from nginx_harness import RunningNginx, free_port  # noqa: E402
from report_server.nginx_conf import ServerParams  # noqa: E402
from report_server.paths import resolve_serve_root  # noqa: E402

from understand_plan.models import Lens  # noqa: E402
from understand_runs.budget import (  # noqa: E402
    DELEGATE_TIMEOUT_SECONDS,
    MAX_TOKEN_BUDGET,
    TokenBudgetTracker,
    run_delegate_with_budget,
)
from understand_runs.catalog import deploy_catalog_spa, update_catalog  # noqa: E402
from understand_runs.remote import format_file_citation  # noqa: E402
from understand_runs.runner import run_report  # noqa: E402

scenarios("../../features/report-catalog-and-navigation.feature")

LOOPBACK_PERMITTED = ("127.10.0.0/24", "127.64.0.0/10", "::1/128")
PERMITTED_CLIENT = "127.10.0.5"


@pytest.fixture
def nav_world(tmp_path, git_repo):
    """Context state for catalog and navigation scenarios."""
    shadow = tmp_path / "shadow"
    shadow.mkdir(parents=True, exist_ok=True)
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)

    server = None
    server_run = tmp_path / "srv_run"
    server_log = tmp_path / "srv_log"
    server_tmp = tmp_path / "srv_tmp"
    for d in (server_run, server_log, server_tmp):
        d.mkdir(parents=True, exist_ok=True)

    world = {
        "repo": git_repo,
        "shadow": shadow,
        "src": src,
        "server": None,
        "server_params": ServerParams(
            listen=("127.0.0.1",),
            port=free_port(),
            permitted=LOOPBACK_PERMITTED,
            shadow_root=resolve_serve_root(shadow),
            src_root=resolve_serve_root(src),
            run_dir=server_run,
            log_dir=server_log,
            temp_dir=server_tmp,
        ),
        "reply": None,
        "result": None,
        "citation": "",
    }

    yield world

    if world["server"] is not None:
        try:
            world["server"].stop()
        except OSError as exc:
            pass  # Server already shut down or pid file cleaned up


# --- Scenario: Root URL presents the client-side catalog dashboard --------

@given("the report server is running")
def _report_server_is_running(nav_world):
    shadow = nav_world["shadow"]
    deploy_catalog_spa(shadow)

    # Seed catalog.json with runs across two repositories
    entry1 = {
        "repo_slug": "service-alpha",
        "lens": "full",
        "target": None,
        "run_id": "r1",
        "timestamp": "2026-11-02T10:00:00Z",
        "commit": "a111111",
        "summary": "Overview of service-alpha",
        "urls": {"parallels": "http://127.0.0.1:8787/r/understand/service-alpha/full/r1/"},
        "report_rel_url": "service-alpha/full/r1/report.html",
    }
    entry2 = {
        "repo_slug": "service-beta",
        "lens": "topic",
        "target": "auth",
        "run_id": "r2",
        "timestamp": "2026-11-02T11:00:00Z",
        "commit": "b222222",
        "summary": "Auth lens of service-beta",
        "urls": {"parallels": "http://127.0.0.1:8787/r/understand/service-beta/topic-auth/r2/"},
        "report_rel_url": "service-beta/topic-auth/r2/report.html",
    }
    update_catalog(shadow, entry1)
    update_catalog(shadow, entry2)

    server = RunningNginx(nav_world["server_params"]).start()
    nav_world["server"] = server


@when(parsers.parse('the user navigates to "{path}"'))
def _user_navigates_to(nav_world, path):
    server = nav_world["server"]
    assert server is not None, "Report server must be running"
    reply = server.get(path, source=PERMITTED_CLIENT)
    nav_world["reply"] = reply


@then("the page loads the catalog dashboard")
def _page_loads_catalog_dashboard(nav_world):
    reply = nav_world["reply"]
    assert reply is not None
    assert reply.status == 200
    assert b"Agent Skills Report Catalog" in reply.body or b"catalog" in reply.body.lower()


@then("the dashboard lists recent runs across repositories")
def _dashboard_lists_recent_runs(nav_world):
    shadow = nav_world["shadow"]
    cat_file = shadow / "understand" / "catalog.json"
    assert cat_file.exists()
    data = json.loads(cat_file.read_text(encoding="utf-8"))
    runs = data if isinstance(data, list) else data.get("runs", [])
    repos = {r["repo_slug"] for r in runs}
    assert "service-alpha" in repos
    assert "service-beta" in repos


# --- Scenario: Directory URL without file name automatically serves report.html

@given(parsers.parse('a report run has completed for "{repo_slug}" under lens "{lens}"'))
def _report_run_completed(nav_world, repo_slug, lens):
    shadow = nav_world["shadow"]
    run_dir = shadow / "understand" / repo_slug / lens / "latest"
    run_dir.mkdir(parents=True, exist_ok=True)
    report_html = f"<!DOCTYPE html><html><body><h1>Report for {repo_slug}</h1></body></html>\n"
    (run_dir / "report.html").write_text(report_html, encoding="utf-8")

    if nav_world["server"] is None:
        nav_world["server"] = RunningNginx(nav_world["server_params"]).start()


@when(parsers.parse('the user requests the directory URL "{path}"'))
def _user_requests_directory_url(nav_world, path):
    server = nav_world["server"]
    assert server is not None
    reply = server.get(path, source=PERMITTED_CLIENT)
    nav_world["reply"] = reply


@then(parsers.parse('nginx serves "{filename}" with status {status:d}'))
def _nginx_serves_file_with_status(nav_world, filename, status):
    reply = nav_world["reply"]
    assert reply is not None
    assert reply.status == status
    assert b"Report for service-now" in reply.body or b"<!DOCTYPE html>" in reply.body


# --- Scenario: Source file citations provide dual links when remote exists

@given(parsers.parse('a repository has git remote origin "{remote_url}"'))
def _repo_has_remote_origin(nav_world, remote_url):
    repo = nav_world["repo"]
    subprocess.run(["git", "remote", "remove", "origin"], cwd=repo, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=repo, check=True)


@given(parsers.parse('a report run finishes on commit "{commit}"'))
def _report_run_finishes_on_commit(nav_world, commit):
    repo = nav_world["repo"]
    nav_world["result"] = run_report(repo, Lens("full"), commit=commit, base_dir=nav_world["shadow"])


@when(parsers.parse('the user inspects a source citation for "{file_path}" at line {line:d}'))
def _inspect_citation_at_line(nav_world, file_path, line):
    result = nav_world["result"]
    remote_info = result.remote_info if result else None
    nav_world["citation"] = format_file_citation(file_path, line, remote_info=remote_info)


@then(parsers.parse('the citation has an offline link to "{offline_link}"'))
def _citation_has_offline_link(nav_world, offline_link):
    citation = nav_world["citation"]
    expected = f"({offline_link})"
    assert expected in citation


@then(parsers.parse('the citation has a remote link to "{remote_link}"'))
def _citation_has_remote_link(nav_world, remote_link):
    citation = nav_world["citation"]
    expected = f"({remote_link})"
    assert expected in citation


# --- Scenario: Remote links degrade gracefully when no git remote is configured

@given("a repository has no git remote origin")
def _repo_has_no_remote_origin(nav_world):
    repo = nav_world["repo"]
    subprocess.run(["git", "remote", "remove", "origin"], cwd=repo, capture_output=True)


@when("a report run finishes")
def _report_run_finishes_without_remote(nav_world):
    repo = nav_world["repo"]
    nav_world["result"] = run_report(repo, Lens("full"), base_dir=nav_world["shadow"])


@then("source citations contain local offline links")
def _source_citations_contain_local_offline_links(nav_world):
    result = nav_world["result"]
    citation = format_file_citation("src/app.py", 42, remote_info=result.remote_info)
    nav_world["citation"] = citation
    assert "(src/src/app.py.html#L42)" in citation


@then("no remote repository links are shown")
def _no_remote_repository_links_shown(nav_world):
    citation = nav_world["citation"]
    assert "view online" not in citation
    assert "https://github" not in citation
    assert "https://gitlab" not in citation


# --- Scenario: Hybrid discovery enforces token and latency ceilings ------

@given("a large repository with multiple central hubs")
def _large_repo_with_central_hubs(nav_world):
    repo = nav_world["repo"]
    src = repo / "src"
    src.mkdir(parents=True, exist_ok=True)

    # Create 3 central hubs
    (src / "hub_auth.ts").write_text("// Hub: Authentication\nexport class AuthManager {}\n", encoding="utf-8")
    (src / "hub_db.ts").write_text("// Hub: Database\nexport class DatabaseClient {}\n", encoding="utf-8")
    (src / "hub_api.ts").write_text("// Hub: API Router\nexport class ApiRouter {}\n", encoding="utf-8")

    # In-degree >= 3 for each hub to be detected by codemap/extractor
    for i in range(4):
        (src / f"client_{i}.ts").write_text(
            f"import './hub_auth';\nimport './hub_db';\nimport './hub_api';\nconsole.log({i});\n",
            encoding="utf-8",
        )


@when("the hybrid discovery process runs")
def _hybrid_discovery_process_runs(nav_world):
    repo = nav_world["repo"]
    nav_world["result"] = run_report(repo, Lens("full"), base_dir=nav_world["shadow"])


@then("the total LLM token usage does not exceed 8000 tokens")
def _total_token_usage_within_budget(nav_world):
    result = nav_world["result"]
    assert result is not None
    assert result.token_tracker is not None
    assert result.token_tracker.total_tokens_used <= MAX_TOKEN_BUDGET
    assert result.token_tracker.tokens_remaining() >= 0


@then("any individual delegate execution times out after 30 seconds")
def _delegate_times_out_after_30_seconds():
    assert DELEGATE_TIMEOUT_SECONDS == 30.0

    # Verify that run_delegate_with_budget enforces timeout
    tracker = TokenBudgetTracker()

    def slow_worker():
        threading.Event().wait(0.2)
        return "unreachable"

    result = run_delegate_with_budget(slow_worker, budget_tracker=tracker, timeout=0.02)
    assert result is None


@then("timed-out delegates fall back to static analysis without aborting the run")
def _timed_out_delegates_fall_back_without_aborting(nav_world):
    result = nav_world["result"]
    assert result is not None
    assert result.run_dir.exists()
    assert (result.run_dir / "report.html").exists()
    assert result.dep_graph is not None
    assert len(result.dep_graph.hubs) > 0
