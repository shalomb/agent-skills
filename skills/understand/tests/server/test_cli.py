# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
"""Tests for the command line: render, run (failure paths only) and install --dry-run."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[2] / "server"

IP_JSON_TAILSCALE_UP = [
    {"ifname": "enp0s5", "addr_info": [{"local": "10.211.55.3"}]},
    {"ifname": "tailscale0", "addr_info": [{"local": "100.99.83.53"}, {"local": "fd7a:115c:a1e0::6d01:53e4"}]},
]


@pytest.fixture
def cli_env(tmp_path: Path) -> dict[str, str]:
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path / "home"),
        "XDG_RUNTIME_DIR": str(tmp_path / "run"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "PYTHONPATH": str(SERVER_DIR),
    }


@pytest.fixture
def ip_json(tmp_path: Path):
    def write(entries) -> Path:
        path = tmp_path / "ip.json"
        path.write_text(json.dumps(entries))
        return path

    return write


def cli(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "report_server", *args], env=env, capture_output=True, text=True
    )


@pytest.fixture
def roots(tmp_path: Path, cli_env: dict[str, str]) -> dict[str, str]:
    (tmp_path / "cache" / "agent-skills").mkdir(parents=True)
    (tmp_path / "home" / "projects").mkdir(parents=True)
    return cli_env


class TestRender:
    def test_prints_the_config_for_a_network(self, roots, ip_json):
        result = cli(["render", "--network", "tailnet", "--ip-json", str(ip_json(IP_JSON_TAILSCALE_UP))], roots)
        assert result.returncode == 0, result.stderr
        assert "listen 100.99.83.53:8787;" in result.stdout
        assert "listen [fd7a:115c:a1e0::6d01:53e4]:8787 ipv6only=on;" in result.stdout
        assert "10.211.55.3" not in result.stdout.split("server {")[1].split("allow")[0]

    def test_serves_the_cache_root_and_the_resolved_projects_root(self, roots, ip_json, tmp_path):
        (tmp_path / "home" / "projects").rmdir()
        real = tmp_path / "host" / "projects"
        real.mkdir(parents=True)
        (tmp_path / "home" / "projects").symlink_to(real)
        result = cli(["render", "--network", "parallels", "--ip-json", str(ip_json(IP_JSON_TAILSCALE_UP))], roots)
        assert f'alias "{tmp_path}/cache/agent-skills/";' in result.stdout
        assert f'alias "{real}/";' in result.stdout

    def test_a_different_port_can_be_given(self, roots, ip_json):
        result = cli(["render", "--network", "parallels", "--port", "9999", "--ip-json", str(ip_json(IP_JSON_TAILSCALE_UP))], roots)
        assert "listen 10.211.55.3:9999;" in result.stdout


class TestRunWhenTheNetworkIsAbsent:
    def test_the_tailnet_instance_exits_nonzero_so_systemd_retries(self, roots, ip_json):
        no_tailscale = IP_JSON_TAILSCALE_UP[:1]
        result = cli(["run", "--network", "tailnet", "--ip-json", str(ip_json(no_tailscale))], roots)
        assert result.returncode == 3
        assert "no address in the tailnet network" in result.stderr

    def test_it_creates_no_files_when_it_cannot_start(self, roots, ip_json, tmp_path):
        cli(["run", "--network", "tailnet", "--ip-json", str(ip_json(IP_JSON_TAILSCALE_UP[:1]))], roots)
        assert not (tmp_path / "run").exists()

    def test_an_unknown_network_is_a_usage_error(self, roots, ip_json):
        result = cli(["run", "--network", "wifi", "--ip-json", str(ip_json([]))], roots)
        assert result.returncode == 2


class TestInstallDryRun:
    def test_prints_the_plan_and_changes_nothing(self, roots, tmp_path):
        unit_dir = tmp_path / "units"
        result = cli(["install", "--dry-run", "--unit-dir", str(unit_dir), "--enable"], roots)
        assert result.returncode == 0, result.stderr
        assert f"would write {unit_dir / 'understand-report-server@.service'}" in result.stdout
        assert "would run: systemctl --user daemon-reload" in result.stdout
        assert "would run: systemctl --user enable --now understand-report-server@tailnet.service" in result.stdout
        assert "ExecStart=" in result.stdout
        assert not unit_dir.exists()

    def test_the_default_unit_dir_is_the_user_systemd_dir(self, roots):
        result = cli(["install", "--dry-run"], roots)
        assert str(Path(roots["HOME"]) / ".config/systemd/user/understand-report-server@.service") in result.stdout

    def test_without_dry_run_it_writes_the_unit(self, roots, tmp_path):
        unit_dir = tmp_path / "units"
        # --no-reload keeps the test away from the real user manager
        result = cli(["install", "--unit-dir", str(unit_dir), "--no-systemctl"], roots)
        assert result.returncode == 0, result.stderr
        assert (unit_dir / "understand-report-server@.service").is_file()
