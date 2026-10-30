"""Unit tests for the nginx.conf generator (pure: text in, text out)."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import replace
from pathlib import Path

import pytest

from report_server.networks import PARALLELS_RANGES, TAILNET_RANGES
from report_server.nginx_conf import ServerParams, render_nginx_conf

PARAMS = ServerParams(
    listen=("10.211.55.3",),
    port=8787,
    permitted=("10.211.55.0/24", "100.64.0.0/10", "fd7a:115c:a1e0::/48"),
    shadow_root=Path("/home/u/.cache/agent-skills"),
    src_root=Path("/mnt/host/projects"),
    run_dir=Path("/run/user/1000/agent-skills/understand-server/parallels"),
    log_dir=Path("/home/u/.local/state/agent-skills/understand-server/parallels"),
    temp_dir=Path("/run/user/1000/agent-skills/understand-server/parallels/tmp"),
)


def render(**changes) -> str:
    return render_nginx_conf(replace(PARAMS, **changes))


def directives(conf: str, name: str) -> list[str]:
    return re.findall(rf"^\s*{name}\s+(.*?);", conf, re.MULTILINE)


class TestListen:
    def test_listens_on_each_given_address_and_the_port_only(self):
        conf = render(listen=("100.99.83.53", "fd7a:115c:a1e0::6d01:53e4"))
        assert directives(conf, "listen") == [
            "100.99.83.53:8787",
            "[fd7a:115c:a1e0::6d01:53e4]:8787 ipv6only=on",
        ]

    @pytest.mark.parametrize(
        "wildcard", ["0.0.0.0", "::", "[::]", "*", "", "localhost", "8787", "0"]
    )
    def test_refuses_a_wildcard_or_non_address_listen(self, wildcard):
        with pytest.raises(ValueError, match="listen"):
            render(listen=(wildcard,))

    def test_refuses_an_empty_listen_list(self):
        with pytest.raises(ValueError, match="listen"):
            render(listen=())

    @pytest.mark.parametrize("port", [0, 80, 1023, 65536])
    def test_refuses_a_port_that_needs_root_or_is_not_a_port(self, port):
        with pytest.raises(ValueError, match="port"):
            render(port=port)


PARALLELS = "10.211.55.0/24"
TAILNET_V4 = "100.64.0.0/10"
TAILNET_V6 = "fd7a:115c:a1e0::/48"


class TestAccessControl:
    def test_allows_each_permitted_range_then_denies_all(self):
        conf = render()
        assert directives(conf, "allow") == [PARALLELS, TAILNET_V4, TAILNET_V6]
        assert directives(conf, "deny") == ["all"]

    def test_deny_all_comes_after_every_allow(self):
        conf = render()
        lines = [l.strip() for l in conf.splitlines() if re.match(r"\s*(allow|deny)\s", l)]
        assert lines[-1] == "deny all;"
        assert all(l.startswith("allow ") for l in lines[:-1])

    def test_access_rules_sit_at_server_level_so_every_location_inherits_them(self):
        conf = render()
        server_block = conf[conf.index("server {") :]
        first_location = server_block.index("location ")
        assert server_block.index("deny all;") < first_location

    def test_no_permitted_range_means_nothing_is_served(self):
        with pytest.raises(ValueError, match="permitted"):
            render(permitted=())

    @pytest.mark.parametrize(
        "bad", ["all", "10.211.55.5/24", "0.0.0.0/0", "::/0", "100.64.0.0/9", "nonsense"]
    )
    def test_refuses_ranges_that_are_not_canonical_or_that_admit_everyone(self, bad):
        with pytest.raises(ValueError, match="permitted"):
            render(permitted=(bad,))


class TestNetworkBoundaries:
    """The real ranges cannot be exercised from this VM (no source address on
    10.211.55.0/24 other than the VM's own, no tailnet peer), so the edges are
    checked here with the same CIDR semantics nginx's allow uses."""

    @staticmethod
    def admitted(address: str, ranges: tuple[str, ...]) -> bool:
        ip = ipaddress.ip_address(address)
        return any(ip in ipaddress.ip_network(r) for r in ranges)

    @pytest.mark.parametrize(
        "address, expected",
        [
            ("10.211.55.0", True),
            ("10.211.55.255", True),
            ("10.211.54.255", False),
            ("10.211.56.0", False),
        ],
    )
    def test_parallels_edges(self, address, expected):
        assert self.admitted(address, PARALLELS_RANGES) is expected

    @pytest.mark.parametrize(
        "address, expected",
        [
            ("100.64.0.0", True),
            ("100.99.83.53", True),
            ("100.127.255.255", True),
            ("100.63.255.255", False),
            ("100.128.0.0", False),
            ("fd7a:115c:a1e0::", True),
            ("fd7a:115c:a1e0::6d01:53e4", True),
            ("fd7a:115c:a1e0:ffff:ffff:ffff:ffff:ffff", True),
            ("fd7a:115c:a1df:ffff:ffff:ffff:ffff:ffff", False),
            ("fd7a:115c:a1e1::", False),
            ("fdb2:2c26:f4e4:0:d983:6684:5e7e:7f19", False),
        ],
    )
    def test_tailnet_edges(self, address, expected):
        assert self.admitted(address, TAILNET_RANGES) is expected

    def test_ranges_match_adr_0003(self):
        assert PARALLELS_RANGES + TAILNET_RANGES == (PARALLELS, TAILNET_V4, TAILNET_V6)


class TestServeRoots:
    def test_serves_the_shadow_root_at_r_and_the_source_root_at_src(self):
        conf = render()
        assert re.search(r'location /r/ \{[^}]*alias "/home/u/.cache/agent-skills/";', conf)
        assert re.search(r'location /src/ \{[^}]*alias "/mnt/host/projects/";', conf)

    def test_everything_else_is_not_found(self):
        assert re.search(r"location / \{\s*return 404;\s*\}", render())

    def test_any_path_segment_starting_with_a_dot_is_not_found(self):
        conf = render()
        match = re.search(r'location ~ "([^"]+)" \{\s*return 404;\s*\}', conf)
        assert match is not None
        pattern = re.compile(match.group(1))
        for hidden in ["/src/a/.env", "/src/a/.git/config", "/r/.hidden/report.html", "/.ssh/id_ed25519", "/r/x/.", "/src/.a/b"]:
            assert pattern.search(hidden), hidden
        for visible in ["/src/a/env", "/r/a.b/c.html", "/r/understand/index.html"]:
            assert not pattern.search(visible), visible

    def test_dot_rule_is_a_regex_location_so_it_wins_over_the_prefix_locations(self):
        conf = render()
        assert "^~" not in conf  # a ^~ prefix location would beat the regex location

    @pytest.mark.parametrize("root", ["/home/u/.cache/agent-skills", "/mnt/host/projects"])
    def test_symlinks_below_each_root_are_refused(self, root):
        # `on`, not `if_not_owner`: the link and its target usually have the same
        # owner (the user), so if_not_owner would follow ~/projects/x/keys -> ~/.aws.
        assert f'disable_symlinks on from="{root}/";' in render()

    def test_directories_list_unless_they_hold_an_index_html(self):
        conf = render()
        assert directives(conf, "autoindex") == ["on", "on"]
        assert directives(conf, "index") == ["index.html", "index.html"]

    def test_runs_as_the_invoking_user(self):
        assert directives(render(), "user") == []


class TestPrivateDirectoriesStayOutOfServeRoots:
    """pid, log and temp files must never be readable through /r/ or /src/."""

    @pytest.mark.parametrize("field", ["run_dir", "log_dir", "temp_dir"])
    @pytest.mark.parametrize("inside", ["/home/u/.cache/agent-skills/x", "/mnt/host/projects/x", "/home/u/.cache/agent-skills", "/mnt/host/projects"])
    def test_refuses_a_private_dir_inside_a_serve_root(self, field, inside):
        with pytest.raises(ValueError, match=field):
            render(**{field: Path(inside)})
