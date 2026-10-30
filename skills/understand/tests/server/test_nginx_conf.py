"""Unit tests for the nginx.conf generator (pure: text in, text out)."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from report_server.nginx_conf import ServerParams, render_nginx_conf

PARAMS = ServerParams(
    listen=("10.211.55.3",),
    port=8787,
    permitted=("10.211.55.0/24", "100.64.0.0/10", "fd7a:115c:a1e0::/48"),
    shadow_root=Path("/home/u/.cache/agent-skills"),
    src_root=Path("/mnt/host/projects"),
    run_dir=Path("/run/user/1000/agent-skills/understand-server/parallels"),
    log_dir=Path("/home/u/.local/state/agent-skills/understand-server/parallels"),
    temp_dir=Path("/home/u/.cache/agent-skills/understand-server/parallels/tmp"),
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
