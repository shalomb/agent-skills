"""Build the parameters of one server instance (one network). Pure: no I/O."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from report_server.addresses import addresses_in
from report_server.networks import NETWORKS
from report_server.nginx_conf import ServerParams

APP_DIR = "agent-skills/understand-server"


class NoAddressForNetwork(RuntimeError):
    """The VM has no address inside the network, for example tailscale is down."""


def instance_dirs(network: str, env: Mapping[str, str]) -> tuple[Path, Path, Path]:
    """(run_dir, log_dir, temp_dir) for one instance.

    pid, config and temp files go under XDG_RUNTIME_DIR, so they are cleared at
    logout and never sit inside a served tree (the shadow root is under
    XDG_CACHE_HOME). Logs go under XDG_STATE_HOME.
    """
    runtime = env.get("XDG_RUNTIME_DIR")
    if not runtime:
        raise ValueError("XDG_RUNTIME_DIR is not set; run inside a systemd user session")
    state = env.get("XDG_STATE_HOME") or f"{env['HOME']}/.local/state"
    run_dir = Path(runtime) / APP_DIR / network
    return run_dir, Path(state) / APP_DIR / network, run_dir / "tmp"


def build_instance(
    network: str,
    local_addresses: tuple[str, ...],
    *,
    port: int,
    shadow_root: Path,
    src_root: Path,
    env: Mapping[str, str],
) -> ServerParams:
    if network not in NETWORKS:
        raise ValueError(f"unknown network {network!r}; expected one of {sorted(NETWORKS)}")
    listen = addresses_in(NETWORKS[network], local_addresses)
    if not listen:
        raise NoAddressForNetwork(f"this machine has no address in the {network} network")
    run_dir, log_dir, temp_dir = instance_dirs(network, env)
    return ServerParams(
        listen=listen,
        port=port,
        permitted=tuple(r for ranges in NETWORKS.values() for r in ranges),
        shadow_root=shadow_root,
        src_root=src_root,
        run_dir=run_dir,
        log_dir=log_dir,
        temp_dir=temp_dir,
    )
