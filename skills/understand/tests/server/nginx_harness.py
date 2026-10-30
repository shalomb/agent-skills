"""Run a real nginx as the current user from a generated config, and talk to it.

Used by the scenarios and the integration tests. Nothing here needs root: the
server gets a temporary prefix, a test port, and loopback addresses.
"""

from __future__ import annotations

import http.client
import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from report_server.nginx_conf import ServerParams, render_nginx_conf

NGINX_BIN = "/usr/sbin/nginx"


class ServerStartFailed(RuntimeError):
    """nginx exited before it accepted connections; the message is its stderr."""


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@dataclass(frozen=True)
class Reply:
    status: int
    body: bytes


class RunningNginx:
    """One nginx instance under a private prefix. Always call stop()."""

    def __init__(self, params: ServerParams, extra_env: dict[str, str] | None = None):
        self.params = params
        self.extra_env = extra_env or {}
        self.process: subprocess.Popen[bytes] | None = None
        self.conf_path = params.run_dir / "nginx.conf"
        self.stderr_path = params.log_dir / "stderr.txt"

    def start(self, timeout: float = 5.0) -> "RunningNginx":
        for directory in (self.params.run_dir, self.params.log_dir, self.params.temp_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.conf_path.write_text(render_nginx_conf(self.params))
        env = {**os.environ, **self.extra_env}
        with self.stderr_path.open("wb") as stderr:
            self.process = subprocess.Popen(
                [NGINX_BIN, "-e", "stderr", "-p", str(self.params.run_dir), "-c", str(self.conf_path)],
                stdout=subprocess.DEVNULL,
                stderr=stderr,
                env=env,
            )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise ServerStartFailed(self.stderr_path.read_text())
            if self._accepts_connections():
                return self
            time.sleep(0.02)
        self.stop()
        raise ServerStartFailed("nginx did not accept connections in time")

    def _accepts_connections(self) -> bool:
        host = self.params.listen[0]
        try:
            with socket.create_connection((host, self.params.port), timeout=0.2):
                return True
        except OSError:
            return False

    def stop(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process = None

    def get(self, path: str, *, source: str | None = None, host: str | None = None) -> Reply:
        """GET `path` as a client whose source address is `source`.

        The path is sent exactly as given, so encoded and dot segments reach nginx.
        """
        target = host or self.params.listen[0]
        connection = http.client.HTTPConnection(
            target,
            self.params.port,
            timeout=3,
            source_address=(source, 0) if source else None,
        )
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return Reply(response.status, response.read())
        finally:
            connection.close()

    def process_uids(self) -> set[int]:
        """Real user ids of the nginx master and its workers, read from /proc."""
        assert self.process is not None
        master = str(self.process.pid)
        uids = set()
        for status_path in Path("/proc").glob("[0-9]*/status"):
            try:
                text = status_path.read_text()
            except OSError:  # the process ended while we looked
                continue
            fields = dict(line.split(":\t", 1) for line in text.splitlines() if ":\t" in line)
            if status_path.parent.name == master or fields.get("PPid", "").strip() == master:
                uids.add(int(fields["Uid"].split()[0]))
        return uids
