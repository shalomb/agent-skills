"""Shared fixtures for the report server tests.

The world is a fake home directory laid out like the real one: `projects` is a
symlink to the directory that holds the repositories, as on the real VM.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[2] / "server"
sys.path.insert(0, str(SERVER_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nginx_harness import RunningNginx, free_port  # noqa: E402
from report_server.nginx_conf import ServerParams  # noqa: E402
from report_server.paths import resolve_serve_root  # noqa: E402

# Loopback stand-ins for the real networks, same shape and same prefix lengths
# except the IPv6 range (the loopback has one IPv6 address, ::1):
#   10.211.55.0/24        -> 127.10.0.0/24
#   100.64.0.0/10         -> 127.64.0.0/10
#   fd7a:115c:a1e0::/48   -> ::1/128
LOOPBACK_PERMITTED = ("127.10.0.0/24", "127.64.0.0/10", "::1/128")
LOOPBACK_LISTEN = ("127.0.0.1", "::1")

INDEX_BODY = b"<h1>Report index</h1>"


@pytest.fixture
def fake_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    real_projects = tmp_path / "host" / "projects"
    (real_projects / "shalomb" / "repo" / ".git").mkdir(parents=True)
    (real_projects / "shalomb" / "repo" / ".env").write_text("SECRET=1\n")
    (real_projects / "shalomb" / "repo" / ".git" / "config").write_text("[core]\n")
    (real_projects / "shalomb" / "repo" / "README.md").write_text("# repo\n")
    (real_projects / "demo").mkdir()
    (real_projects / "demo" / "notes.txt").write_text("notes\n")
    (home / ".aws").mkdir(parents=True)
    (home / ".aws" / "credentials").write_text("aws_secret_access_key = x\n")
    (home / ".ssh").mkdir()
    (home / ".ssh" / "id_ed25519").write_text("PRIVATE KEY\n")
    (home / "projects").symlink_to(real_projects)

    shadow = home / ".cache" / "agent-skills"
    run = shadow / "understand" / "repo-1" / "full" / "abc1234-20260101T000000Z"
    run.mkdir(parents=True)
    (run / "report.html").write_text("<h1>run</h1>")
    (shadow / "understand" / "repo-1" / "full" / "latest").symlink_to(run.name)
    (shadow / "understand" / "index.html").write_bytes(INDEX_BODY)
    (shadow / ".hidden").mkdir()
    (shadow / ".hidden" / "report.html").write_text("hidden")
    return home


@pytest.fixture
def server_params(fake_home: Path, tmp_path: Path) -> ServerParams:
    return ServerParams(
        listen=LOOPBACK_LISTEN,
        port=free_port(),
        permitted=LOOPBACK_PERMITTED,
        shadow_root=resolve_serve_root(fake_home / ".cache" / "agent-skills"),
        src_root=resolve_serve_root(fake_home / "projects"),
        run_dir=tmp_path / "run",
        log_dir=tmp_path / "log",
        temp_dir=tmp_path / "tmp",
    )


@pytest.fixture
def nginx(server_params: ServerParams):
    server = RunningNginx(server_params).start()
    yield server
    server.stop()


@pytest.fixture
def started_servers():
    """Servers a scenario starts itself; every one is stopped at teardown."""
    servers: list[RunningNginx] = []
    yield servers
    for server in servers:
        server.stop()
