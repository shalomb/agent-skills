# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
"""End to end on this VM's real addresses, through the real CLI and a real nginx.

Binds the VM's Parallels and tailnet addresses on a random high port (never 8787),
as the current user, with temp XDG dirs. Each test skips when the address is absent,
so the suite also runs on a machine without Parallels or tailscale.

Not covered here, because it needs another machine: a client whose source address
is outside the ranges. That is covered by the loopback scenarios and the range edge tests.
"""

from __future__ import annotations

import http.client
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from nginx_harness import free_port
from report_server.addresses import parse_ip_addr_json

pytestmark = pytest.mark.integration

SERVER_DIR = Path(__file__).resolve().parents[2] / "server"


def vm_addresses() -> tuple[str, ...]:
    try:
        out = subprocess.run(["ip", "-j", "addr", "show"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return ()
    return parse_ip_addr_json(out)


def start_cli_server(network: str, tmp_path: Path, port: int) -> subprocess.Popen[bytes]:
    home = tmp_path / "home"
    (home / ".cache" / "agent-skills" / "understand").mkdir(parents=True)
    (home / ".cache" / "agent-skills" / "understand" / "index.html").write_text("index")
    (home / "projects").mkdir()
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "XDG_RUNTIME_DIR": str(tmp_path / "run"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
        "PYTHONPATH": str(SERVER_DIR),
    }
    return subprocess.Popen(
        [sys.executable, "-m", "report_server", "run", "--network", network, "--port", str(port)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def get_when_up(address: str, port: int, process: subprocess.Popen[bytes]) -> int:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        assert process.poll() is None, process.stderr.read().decode()
        try:
            connection = http.client.HTTPConnection(address, port, timeout=2, source_address=(address, 0))
            connection.request("GET", "/r/understand/")
            return connection.getresponse().status
        except OSError:
            time.sleep(0.05)
    raise AssertionError("server did not come up")


@pytest.mark.parametrize(
    "network, address",
    [("parallels", "10.211.55.3"), ("tailnet", "100.99.83.53"), ("tailnet", "fd7a:115c:a1e0::6d01:53e4")],
)
def test_the_instance_serves_its_own_address_as_the_user(network, address, tmp_path):
    if address not in vm_addresses():
        pytest.skip(f"{address} is not an address of this machine")
    port = free_port()
    process = start_cli_server(network, tmp_path, port)
    try:
        assert get_when_up(address, port, process) == 200
        assert (Path("/proc") / str(process.pid) / "status").read_text().split("Uid:")[1].split()[0] == str(os.getuid())
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_the_parallels_instance_is_not_reachable_on_loopback(tmp_path):
    if "10.211.55.3" not in vm_addresses():
        pytest.skip("no Parallels address")
    port = free_port()
    process = start_cli_server("parallels", tmp_path, port)
    try:
        get_when_up("10.211.55.3", port, process)
        with pytest.raises(ConnectionRefusedError):
            http.client.HTTPConnection("127.0.0.1", port, timeout=2).request("GET", "/")
    finally:
        process.terminate()
        process.wait(timeout=5)
