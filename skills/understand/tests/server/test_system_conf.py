"""System nginx deployment (ADR 0007): the one-time /etc/nginx/conf.d snippet and sudoers rule.

The user-level package (report_server) keeps its guarantees: no wildcard, no sudo,
no /etc. This sibling package is the explicit, separate privileged path.
"""

# pyright: reportMissingImports=false
from __future__ import annotations

import http.client
import re
import socket
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))

from report_server_system.conf import SystemParams, render_sudoers, render_system_conf  # noqa: E402

NGINX_BIN = "/usr/sbin/nginx"
PERMITTED = ("127.0.0.0/8", "::1/128", "10.211.55.0/24", "100.64.0.0/10", "fd7a:115c:a1e0::/48")
PARAMS = SystemParams(
    port=80,
    permitted=PERMITTED,
    shadow_root=Path("/home/u/.cache/agent-skills"),
    src_root=Path("/mnt/host/projects"),
    snippet_dir=Path("/etc/nginx/agent-skills.d"),
    access_log=Path("/var/log/nginx/agent-skills.access.log"),
)


def render(**changes) -> str:
    return render_system_conf(replace(PARAMS, **changes))


class TestIsAnHttpContextSnippet:
    def test_has_no_main_or_events_level_directives(self):
        conf = render()
        assert not re.search(r"^\s*(events|http|pid|daemon|worker_processes|user|error_log)\b", conf, re.MULTILINE)

    def test_is_exactly_one_server_block(self):
        assert len(re.findall(r"^\s*server\s*\{", render(), re.MULTILINE)) == 1


class TestListen:
    def test_default_server_on_the_port_for_both_families(self):
        listens = re.findall(r"^\s*listen\s+(.*?);", render(port=80), re.MULTILINE)
        assert listens == ["80 default_server", "[::]:80 ipv6only=on default_server"]

    def test_port_is_a_parameter_so_tests_need_no_root(self):
        assert "listen 8123 default_server;" in render(port=8123)

    @pytest.mark.parametrize("port", [0, 65536])
    def test_rejects_out_of_range_port(self, port):
        with pytest.raises(ValueError, match="port"):
            render(port=port)


class TestAccessControl:
    def test_allows_loopback_parallels_and_tailnet_then_denies_all(self):
        conf = render()
        allows = re.findall(r"^\s*allow\s+(\S+);", conf, re.MULTILINE)
        assert allows == list(PERMITTED)
        assert conf.index("deny all;") > conf.rindex("allow ")

    def test_refuses_an_empty_allow_list(self):
        with pytest.raises(ValueError, match="permitted"):
            render(permitted=())

    @pytest.mark.parametrize("bad", ["0.0.0.0/0", "10.0.0.5", "::/0", "not-a-range"])
    def test_refuses_unbounded_or_malformed_ranges(self, bad):
        with pytest.raises(ValueError):
            render(permitted=(bad,))

    def test_every_refusal_reads_as_not_found(self):
        conf = render()
        assert "error_page 403 =404 @not_found;" in conf

    def test_dot_segments_are_hidden(self):
        assert re.search(r'location ~ "\(\^\|/\)\\\."\s*\{\s*return 404;', render())


class TestServeRoots:
    def test_both_roots_refuse_symlinks_from_the_root(self):
        conf = render()
        for prefix, root in (("/r/", "/home/u/.cache/agent-skills/"), ("/src/", "/mnt/host/projects/")):
            assert f'location {prefix} {{' in conf
            assert f'alias "{root}";' in conf
            assert f'disable_symlinks on from="{root}";' in conf

    def test_everything_else_is_not_found(self):
        assert re.search(r"location / \{\s*return 404;", render())

    @pytest.mark.parametrize("field", ["shadow_root", "src_root", "snippet_dir", "access_log"])
    def test_paths_must_be_absolute_and_free_of_quote_characters(self, field):
        for bad in (Path("relative/dir"), Path('/tmp/a"b'), Path("/tmp/a;b"), Path("/tmp/a$b")):
            with pytest.raises(ValueError):
                render(**{field: bad})


class TestUserDeployedSnippets:
    def test_includes_the_snippet_dir_inside_the_server_block_before_the_catch_all(self):
        conf = render()
        include = "include /etc/nginx/agent-skills.d/*.conf;"
        assert include in conf
        assert conf.index(include) < conf.index("location / {")

    def test_types_make_markdown_plain_text_not_a_download(self):
        conf = render()
        assert re.search(r"text/plain[^;]*\bmd\b", conf) and "default_type text/plain;" in conf


class TestSudoers:
    def test_allows_exactly_a_config_test_and_a_reload_without_a_password(self):
        text = render_sudoers("unop")
        rules = [l for l in text.splitlines() if l and not l.startswith("#")]
        assert rules == [
            "unop ALL=(root) NOPASSWD: /usr/sbin/nginx -t, /usr/bin/systemctl reload nginx",
        ]

    @pytest.mark.parametrize("bad", ["", "a b", "root;", "u,v", "ALL", "%wheel", "a\nb"])
    def test_refuses_names_that_could_widen_the_rule(self, bad):
        with pytest.raises(ValueError):
            render_sudoers(bad)

    def test_has_no_wildcards_and_no_shells(self):
        text = render_sudoers("unop")
        assert "*" not in text and not re.search(r"\b(sh|bash|ALL)\b\s*$", text, re.MULTILINE)


# --- real nginx, as the current user, on a test port -------------------------------

def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _get(port: int, path: str) -> tuple[int, dict[str, str], bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    conn.request("GET", path)
    reply = conn.getresponse()
    return reply.status, {k.lower(): v for k, v in reply.getheaders()}, reply.read()


@pytest.fixture
def system_nginx(tmp_path: Path):
    shadow = tmp_path / "cache" / "agent-skills"
    (shadow / "teach" / "t" / "lessons").mkdir(parents=True)
    (shadow / "teach" / "t" / "mission.md").write_text("# Mission\n")
    (shadow / "teach" / "t" / "lessons" / "a.html").write_text("<h1>lesson</h1>")
    (shadow / ".hidden").mkdir()
    (shadow / ".hidden" / "x.html").write_text("hidden")
    (shadow / "teach" / "link.html").symlink_to(shadow / "teach" / "t" / "lessons" / "a.html")
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    (snippets / "10-extra.conf").write_text('location /extra/ { return 200 "extra"; }\n')
    started: list[subprocess.Popen] = []

    def start(permitted=PERMITTED) -> int:
        port = _free_port()
        snippet = render_system_conf(SystemParams(
            port=port, permitted=permitted, shadow_root=shadow, src_root=tmp_path,
            snippet_dir=snippets, access_log=tmp_path / "access.log"))
        (tmp_path / "agent-skills.conf").write_text(snippet)
        main = tmp_path / "nginx.conf"
        main.write_text(f"""pid {tmp_path}/nginx.pid;
error_log {tmp_path}/error.log;
daemon off;
events {{ worker_connections 16; }}
http {{
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  access_log off;
  client_body_temp_path {tmp_path}/b; proxy_temp_path {tmp_path}/p;
  fastcgi_temp_path {tmp_path}/f; uwsgi_temp_path {tmp_path}/u; scgi_temp_path {tmp_path}/s;
  include {tmp_path}/agent-skills.conf;
}}
""")
        proc = subprocess.Popen([NGINX_BIN, "-e", "stderr", "-p", str(tmp_path), "-c", str(main)],
                                stderr=subprocess.PIPE)
        started.append(proc)
        for _ in range(50):
            if proc.poll() is not None:
                raise AssertionError(proc.stderr.read().decode())
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                return port
            except OSError:
                time.sleep(0.1)
        raise AssertionError("nginx did not start")

    yield start
    for proc in started:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.mark.integration
class TestRealNginx:
    def test_serves_a_lesson_and_a_markdown_file_as_text(self, system_nginx):
        port = system_nginx()
        status, headers, body = _get(port, "/r/teach/t/lessons/a.html")
        assert (status, body) == (200, b"<h1>lesson</h1>")
        status, headers, _ = _get(port, "/r/teach/t/mission.md")
        assert status == 200 and headers["content-type"].startswith("text/plain")

    def test_dot_paths_and_symlinks_and_unknown_paths_are_not_found(self, system_nginx):
        port = system_nginx()
        for path in ("/r/.hidden/x.html", "/r/teach/link.html", "/etc/passwd", "/"):
            assert _get(port, path)[0] == 404, path

    def test_a_snippet_dropped_in_the_snippet_dir_is_served_after_a_restart(self, system_nginx):
        port = system_nginx()
        assert _get(port, "/extra/")[:1] == (200,) and _get(port, "/extra/")[2] == b"extra"

    def test_a_client_outside_the_allow_list_reads_not_found(self, system_nginx):
        port = system_nginx(permitted=("10.211.55.0/24",))
        assert _get(port, "/r/teach/t/lessons/a.html")[0] == 404


# --- CLI ---------------------------------------------------------------------------

from report_server_system.cli import main  # noqa: E402


class TestCli:
    def test_render_uses_the_homes_shadow_root_and_all_three_networks(self, tmp_path, capsys):
        (tmp_path / ".cache" / "agent-skills").mkdir(parents=True)
        (tmp_path / "projects").mkdir()
        assert main(["render"], {"HOME": str(tmp_path)}) == 0
        out = capsys.readouterr().out
        assert f'alias "{tmp_path.resolve()}/.cache/agent-skills/";' in out
        for cidr in ("127.0.0.0/8", "::1/128", "10.211.55.0/24", "100.64.0.0/10", "fd7a:115c:a1e0::/48"):
            assert f"allow {cidr};" in out
        assert "listen 80 default_server;" in out

    def test_render_honours_xdg_cache_home(self, tmp_path, capsys):
        cache = tmp_path / "xdg"
        (cache / "agent-skills").mkdir(parents=True)
        (tmp_path / "projects").mkdir()
        main(["render"], {"HOME": str(tmp_path), "XDG_CACHE_HOME": str(cache)})
        assert f'alias "{cache.resolve()}/agent-skills/";' in capsys.readouterr().out

    def test_sudoers_prints_the_rule_for_the_named_user(self, capsys):
        assert main(["sudoers", "--user", "unop"], {"HOME": "/h"}) == 0
        assert "unop ALL=(root) NOPASSWD:" in capsys.readouterr().out

    def test_sudoers_rejects_a_bad_user_with_exit_2(self, capsys):
        assert main(["sudoers", "--user", "a b"], {"HOME": "/h"}) == 2
