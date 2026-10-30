"""Integration tests: a real nginx, run as the current user, from a generated config.

These go beyond the feature file: path tricks, listings, and the `latest` link.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import INDEX_BODY

pytestmark = pytest.mark.integration

PERMITTED = "127.10.0.5"


class TestDotSegments:
    @pytest.mark.parametrize(
        "path",
        [
            "/src/shalomb/repo/.env",
            "/src/shalomb/repo/%2eenv",
            "/src/shalomb/repo/%2Eenv",
            "/src/shalomb/repo/.git/config",
            "/src/shalomb/repo/%2egit/config",
            "/src/shalomb/repo/.git/",
            "/src/shalomb/repo/./.env",
            "/r/.hidden/report.html",
            "/r/understand/../.hidden/report.html",
            "/r/%2e%2e/.hidden/report.html",
            "/.ssh/id_ed25519",
        ],
    )
    def test_is_not_found(self, nginx, path):
        assert nginx.get(path, source=PERMITTED).status == 404

    def test_an_ordinary_file_is_served(self, nginx):
        reply = nginx.get("/src/shalomb/repo/README.md", source=PERMITTED)
        assert (reply.status, reply.body) == (200, b"# repo\n")

    def test_a_dot_inside_a_name_is_not_a_dot_segment(self, nginx, fake_home: Path):
        (fake_home / "projects" / "demo" / "v1.2").mkdir()
        (fake_home / "projects" / "demo" / "v1.2" / "a.b.txt").write_text("ok\n")
        assert nginx.get("/src/demo/v1.2/a.b.txt", source=PERMITTED).status == 200


class TestSymlinks:
    def test_a_link_leaving_the_source_root_is_not_followed(self, nginx, fake_home: Path):
        (fake_home / "projects" / "demo" / "keys").symlink_to(fake_home / ".aws")
        assert nginx.get("/src/demo/keys/credentials", source=PERMITTED).status == 404

    def test_a_link_to_a_file_outside_the_root_is_not_followed(self, nginx, fake_home: Path):
        (fake_home / "projects" / "demo" / "k").symlink_to(fake_home / ".aws" / "credentials")
        assert nginx.get("/src/demo/k", source=PERMITTED).status == 404

    def test_a_link_leaving_the_shadow_root_is_not_followed(self, nginx, fake_home: Path):
        (fake_home / ".cache" / "agent-skills" / "keys").symlink_to(fake_home / ".aws")
        assert nginx.get("/r/keys/credentials", source=PERMITTED).status == 404

    def test_a_symlinked_projects_dir_is_served_through_its_resolved_root(self, nginx):
        assert nginx.get("/src/demo/notes.txt", source=PERMITTED).status == 200


class TestLatestLink:
    """Spec unit 4 gives each lens a `latest` link to its newest run. nginx cannot
    check where a link points, only that one exists, so with disable_symlinks on
    the link is refused and readers use the run directory URL (see README)."""

    RUN = "/r/understand/repo-1/full/abc1234-20260101T000000Z/report.html"
    LATEST = "/r/understand/repo-1/full/latest/report.html"

    def test_the_run_is_served_directly(self, nginx):
        assert nginx.get(self.RUN, source=PERMITTED).body == b"<h1>run</h1>"

    def test_the_latest_link_is_not_followed(self, nginx):
        assert nginx.get(self.LATEST, source=PERMITTED).status == 404


class TestListings:
    def test_a_directory_with_an_index_html_serves_it(self, nginx):
        reply = nginx.get("/r/understand/", source=PERMITTED)
        assert (reply.status, reply.body) == (200, INDEX_BODY)

    def test_a_directory_without_an_index_lists_its_entries(self, nginx):
        reply = nginx.get("/src/demo/", source=PERMITTED)
        assert reply.status == 200 and b"notes.txt" in reply.body


class TestOtherPaths:
    @pytest.mark.parametrize("path", ["/", "/etc/passwd", "/robots.txt", "/rr/x", "/src", "/r"])
    def test_outside_the_serve_roots_is_not_found(self, nginx, path):
        reply = nginx.get(path, source=PERMITTED)
        assert reply.status in (404, 301)
        if reply.status == 301:  # /src and /r redirect to their slash form, which is a root
            assert path in ("/src", "/r")


class TestDenial:
    DENIED = "127.1.2.3"

    @pytest.mark.parametrize("path", ["/r/understand/", "/src/demo/notes.txt", "/src/shalomb/repo/.env", "/nothing"])
    def test_a_denied_client_gets_not_found_for_every_path(self, nginx, path):
        # One answer for every path: a denied client learns nothing about what exists.
        assert nginx.get(path, source=self.DENIED).status == 404

    def test_a_denial_is_logged_as_forbidden_by_rule(self, nginx):
        nginx.get("/r/understand/", source=self.DENIED)
        assert "access forbidden by rule" in (nginx.params.log_dir / "error.log").read_text()

    def test_a_permitted_client_is_not_logged_as_forbidden(self, nginx):
        nginx.get("/r/understand/", source=PERMITTED)
        assert "access forbidden" not in (nginx.params.log_dir / "error.log").read_text()

    @pytest.mark.parametrize("source", ["127.10.0.0", "127.10.0.255", "127.64.0.0", "127.127.255.255"])
    def test_loopback_range_edges_inside_are_admitted(self, nginx, source):
        assert nginx.get("/r/understand/", source=source).status == 200

    @pytest.mark.parametrize("source", ["127.9.255.255", "127.10.1.0", "127.63.255.255", "127.128.0.0"])
    def test_loopback_range_edges_outside_are_denied(self, nginx, source):
        assert nginx.get("/r/understand/", source=source).status == 404

    def test_ipv6_client_in_range_is_admitted(self, nginx):
        assert nginx.get("/r/understand/", source="::1", host="::1").status == 200
