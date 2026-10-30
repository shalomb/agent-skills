"""Unit tests for building one server instance (one network) from the VM's addresses."""

# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
from __future__ import annotations

from pathlib import Path

import pytest

from report_server.instance import NoAddressForNetwork, instance_dirs, build_instance
from report_server.networks import NETWORKS, PARALLELS_RANGES, TAILNET_RANGES

ALL_PERMITTED = PARALLELS_RANGES + TAILNET_RANGES
VM = ("127.0.0.1", "10.211.55.3", "100.99.83.53", "fd7a:115c:a1e0::6d01:53e4")
VM_TAILSCALE_DOWN = ("127.0.0.1", "10.211.55.3")
ROOTS = dict(shadow_root=Path("/home/u/.cache/agent-skills"), src_root=Path("/mnt/host/projects"))
XDG = {
    "XDG_RUNTIME_DIR": "/run/user/1000",
    "XDG_STATE_HOME": "/home/u/.local/state",
    "HOME": "/home/u",
}


def build(network, addresses=VM, port=8787, env=XDG):
    return build_instance(network, addresses, port=port, env=env, **ROOTS)


def test_parallels_instance_listens_only_on_the_parallels_address():
    assert build("parallels").listen == ("10.211.55.3",)


def test_tailnet_instance_listens_on_both_tailnet_addresses():
    assert build("tailnet").listen == ("100.99.83.53", "fd7a:115c:a1e0::6d01:53e4")


def test_both_instances_accept_clients_from_both_networks():
    assert build("parallels").permitted == ALL_PERMITTED
    assert build("tailnet").permitted == ALL_PERMITTED


def test_the_two_instances_share_no_directory():
    parallels, tailnet = build("parallels"), build("tailnet")
    for field in ("run_dir", "log_dir", "temp_dir"):
        assert getattr(parallels, field) != getattr(tailnet, field)


def test_with_tailscale_down_the_tailnet_instance_cannot_be_built():
    with pytest.raises(NoAddressForNetwork, match="tailnet"):
        build("tailnet", VM_TAILSCALE_DOWN)


def test_with_tailscale_down_the_parallels_instance_is_unchanged():
    assert build("parallels", VM_TAILSCALE_DOWN) == build("parallels", VM)


def test_an_unknown_network_is_refused():
    with pytest.raises(ValueError, match="network"):
        build("wifi")


def test_networks_are_the_two_adr_0003_groups():
    assert NETWORKS == {"parallels": PARALLELS_RANGES, "tailnet": TAILNET_RANGES}


class TestDirectories:
    def test_pid_and_config_live_in_the_runtime_dir_and_logs_in_the_state_dir(self):
        parallels = build("parallels")
        assert parallels.run_dir == Path("/run/user/1000/agent-skills/understand-server/parallels")
        assert parallels.temp_dir == Path("/run/user/1000/agent-skills/understand-server/parallels/tmp")
        assert parallels.log_dir == Path("/home/u/.local/state/agent-skills/understand-server/parallels")

    def test_state_home_defaults_to_dot_local_state(self):
        _, log_dir, _ = instance_dirs("tailnet", {"XDG_RUNTIME_DIR": "/run/user/1000", "HOME": "/home/u"})
        assert log_dir == Path("/home/u/.local/state/agent-skills/understand-server/tailnet")

    def test_a_missing_runtime_dir_is_an_error_not_a_guess(self):
        with pytest.raises(ValueError, match="XDG_RUNTIME_DIR"):
            instance_dirs("tailnet", {"HOME": "/home/u"})
