"""Step definitions for skills/understand/features/report-server.feature.

Every scenario runs against a real nginx started as the current user from a
generated config. Client networks are simulated on the loopback with source
addresses (see LOOPBACK_PERMITTED in conftest.py for the mapping).
"""

# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import INDEX_BODY
from nginx_harness import Reply, RunningNginx, ServerStartFailed

pytestmark = pytest.mark.integration

scenarios("../../features/report-server.feature")

REPORT_INDEX = "/r/understand/"

# device description -> (client source address, address the client connects to)
DEVICES = {
    "the host Mac on the Parallels network": ("127.10.0.5", "127.0.0.1"),
    "a laptop on the tailnet with an old-style address": ("127.100.1.1", "127.0.0.1"),
    "a phone on the tailnet with a new-style address": ("::1", "::1"),
    "a device in the next network after the Parallels network": ("127.10.1.5", "127.0.0.1"),
    "a device in the first address after the tailnet range": ("127.128.0.0", "127.0.0.1"),
    "a device on a home network": ("127.1.2.3", "127.0.0.1"),
}
PERMITTED_DEVICE = DEVICES["the host Mac on the Parallels network"]
# A VM address on which the server is not bound (it binds 127.0.0.1 and ::1 only).
OTHER_INTERFACE_ADDRESS = "127.0.0.2"


@dataclass
class World:
    server: RunningNginx
    device: tuple[str | None, str] = PERMITTED_DEVICE
    reply: Reply | None = None
    refused: bool = False
    extra: dict = field(default_factory=dict)

    def ask(self, path: str) -> None:
        source, target = self.device
        try:
            self.reply = self.server.get(path, source=source, host=target)
        except ConnectionRefusedError:
            self.refused = True


@pytest.fixture
def world(nginx: RunningNginx) -> World:
    return World(server=nginx)


@given(parsers.re("(?P<device>" + "|".join(map(re.escape, DEVICES)) + ")"))
def device_on_network(world: World, device: str):
    world.device = DEVICES[device]


@when("the device asks for the report index")
def device_asks_for_index(world: World):
    world.ask(REPORT_INDEX)


@then("the device gets the report index")
def device_gets_index(world: World):
    assert world.reply is not None
    assert (world.reply.status, world.reply.body) == (200, INDEX_BODY)


@then("no report is served to the device")
def no_report_served(world: World):
    if world.refused:
        return
    assert world.reply is not None
    assert world.reply.status == 404  # a denied client is told nothing exists
    assert INDEX_BODY not in world.reply.body
    assert "access forbidden by rule" in (world.server.params.log_dir / "error.log").read_text()


@given(
    "a device that reaches the VM on an interface that is not the Parallels network or the tailnet"
)
def device_on_other_interface(world: World):
    world.device = (None, OTHER_INTERFACE_ADDRESS)


@given("tailscale is down")
def tailscale_is_down(world: World, started_servers: list, server_params, tmp_path: Path):
    # With tailscale down the tailnet address does not exist on the VM. 192.0.2.1
    # (TEST-NET-1) is never a local address, so nginx cannot bind it.
    tailnet_params = replace(
        server_params,
        listen=("192.0.2.1",),
        run_dir=tmp_path / "run-tailnet",
        log_dir=tmp_path / "log-tailnet",
        temp_dir=tmp_path / "tmp-tailnet",
    )
    with pytest.raises(ServerStartFailed, match="Cannot assign requested address"):
        RunningNginx(tailnet_params).start()


@when("the host Mac asks for the report index")
def host_mac_asks_for_index(world: World):
    world.device = DEVICES["the host Mac on the Parallels network"]
    world.ask(REPORT_INDEX)


@then("the host Mac gets the report index")
def host_mac_gets_index(world: World):
    device_gets_index(world)


@when(parsers.parse('a permitted device asks for "{path}"'))
def permitted_device_asks_for(world: World, path: str):
    world.device = PERMITTED_DEVICE
    world.ask(path)


@then("the device is told that the file is not found")
def file_not_found(world: World):
    assert world.reply is not None
    assert world.reply.status == 404


@given(parsers.parse('"~/projects/{link}" links to "~/{target}"'))
def link_leaves_serve_root(fake_home: Path, link: str, target: str):
    # The link and its target belong to the same user, as in real life.
    (fake_home / "projects" / link).symlink_to(fake_home / target)


@given("the user has no administrator rights")
def user_has_no_admin_rights(world: World, tmp_path: Path):
    assert os.geteuid() != 0
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    sudo_log = tmp_path / "sudo-calls"
    stub = bin_dir / "sudo"
    stub.write_text(f"#!/bin/sh\necho \"$@\" >> {sudo_log}\nexit 1\n")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    world.extra["sudo_log"] = sudo_log
    world.extra["path"] = f"{bin_dir}:{os.environ['PATH']}"


@when("the user starts the report server")
def user_starts_server(world: World, server_params, started_servers: list):
    world.server.stop()
    server = RunningNginx(server_params, extra_env={"PATH": world.extra["path"]}).start()
    started_servers.append(server)
    world.server = server


@then("the report server accepts requests")
def server_accepts_requests(world: World):
    source, target = PERMITTED_DEVICE
    reply = world.server.get(REPORT_INDEX, source=source, host=target)
    assert reply.status == 200
    assert world.server.process_uids() == {os.getuid()}
    assert not world.extra["sudo_log"].exists()
