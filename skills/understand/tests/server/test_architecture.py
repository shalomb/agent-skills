# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
"""Architecture tests for the report server (spec: Architecture tests, ADR 0002/0003).

These check structure, not behaviour: what the generated config and the code
are allowed to contain, whatever the parameters.
"""

from __future__ import annotations

import ast
import ipaddress
import re
from pathlib import Path

import pytest

from report_server.instance import build_instance
from report_server.networks import NETWORKS
from report_server.nginx_conf import render_nginx_conf
from report_server.units import render_unit

PACKAGE = Path(__file__).resolve().parents[2] / "server" / "report_server"
VM = ("127.0.0.1", "10.211.55.3", "100.99.83.53", "fd7a:115c:a1e0::6d01:53e4")
ENV = {"XDG_RUNTIME_DIR": "/run/user/1000", "XDG_STATE_HOME": "/home/u/.local/state", "HOME": "/home/u"}


def real_configs() -> dict[str, str]:
    """The configs the service would run on this VM, one per network."""
    return {
        network: render_nginx_conf(
            build_instance(
                network, VM, port=8787, env=ENV,
                shadow_root=Path("/home/u/.cache/agent-skills"), src_root=Path("/mnt/host/projects"),
            )
        )
        for network in NETWORKS
    }


def listen_address(listen: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """The IP address named by a `listen` value such as `1.2.3.4:8787` or `[::1]:8787 ipv6only=on`."""
    match = re.match(r"\[([^\]]+)\]:\d+|([^:\s]+):\d+", listen)
    assert match is not None, f"listen without an explicit address: {listen!r}"
    return ipaddress.ip_address(match.group(1) or match.group(2))


@pytest.mark.parametrize("network", sorted(NETWORKS))
class TestNoWildcardListen:
    def test_every_listen_names_one_specific_address_and_a_port(self, network):
        listens = re.findall(r"^\s*listen\s+(.*?);", real_configs()[network], re.MULTILINE)
        assert listens, "a server block without listen would bind *:80"
        for listen in listens:
            ip = listen_address(listen)
            assert not ip.is_unspecified and not ip.is_loopback

    def test_every_listen_address_lies_inside_the_networks_of_the_adr(self, network):
        allowed = [ipaddress.ip_network(r) for ranges in NETWORKS.values() for r in ranges]
        for listen in re.findall(r"^\s*listen\s+(.*?);", real_configs()[network], re.MULTILINE):
            ip = listen_address(listen)
            assert any(ip in n for n in allowed), listen

    def test_there_is_exactly_one_server_block(self, network):
        assert len(re.findall(r"^\s*server\s*\{", real_configs()[network], re.MULTILINE)) == 1


@pytest.mark.parametrize("network", sorted(NETWORKS))
class TestRunsAsTheUser:
    def test_config_sets_no_user_directive_and_includes_nothing_from_etc(self, network):
        conf = real_configs()[network]
        assert not re.search(r"^\s*user\s", conf, re.MULTILINE)
        assert "/etc/" not in conf and not re.search(r"^\s*include\s", conf, re.MULTILINE)

    def test_every_path_in_the_config_is_under_the_user_or_the_serve_roots(self, network):
        for path in re.findall(r'"(/[^"]*)"', real_configs()[network]):
            assert path.startswith(("/run/user/1000/", "/home/u/", "/mnt/host/projects/")), path

    def test_the_port_needs_no_privilege(self, network):
        for port in re.findall(r":(\d+)\b", real_configs()[network]):
            assert int(port) >= 1024


class TestNoPrivilegeEscalation:
    def test_unit_has_no_user_switch_and_forbids_new_privileges(self):
        unit = render_unit(python="/usr/bin/python3", server_dir=Path("/x"), port=8787)
        assert not re.search(r"^(User|Group|PermissionsStartOnly|AmbientCapabilities)=", unit, re.MULTILINE)
        assert "NoNewPrivileges=yes" in unit

    @pytest.mark.parametrize("source", sorted(PACKAGE.glob("*.py")), ids=lambda p: p.name)
    def test_package_code_never_names_sudo_or_the_system_nginx(self, source):
        # String literals only: docstrings and comments may explain what is avoided.
        tree = ast.parse(source.read_text())
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
        }
        literals = [
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
        ]
        for text in literals:
            assert not re.search(r"\bsudo\b|/etc/nginx|nginx\.service|--system", text), text

    def test_every_systemctl_call_is_for_the_user_manager(self):
        text = (PACKAGE / "units.py").read_text()
        calls = re.findall(r'Run\(\("systemctl",([^)]*)\)', text)
        assert calls and all(call.strip().startswith('"--user"') for call in calls)
