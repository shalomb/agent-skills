"""Render a user-level nginx.conf for the report server. Pure: no I/O."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path

MIN_UNPRIVILEGED_PORT = 1024


@dataclass(frozen=True)
class ServerParams:
    """Everything the generator needs. Paths must be absolute and already resolved."""

    listen: tuple[str, ...]
    port: int
    permitted: tuple[str, ...]
    shadow_root: Path
    src_root: Path
    run_dir: Path
    log_dir: Path
    temp_dir: Path


def _listen_directive(address: str, port: int) -> str:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        raise ValueError(f"listen address must be a specific IP address, got {address!r}") from None
    if ip.is_unspecified:
        raise ValueError(f"listen address must not be a wildcard, got {address!r}")
    if ip.version == 6:
        return f"listen [{ip}]:{port} ipv6only=on;"
    return f"listen {ip}:{port};"


def _allow_directive(cidr: str) -> str:
    try:
        network = ipaddress.ip_network(cidr, strict=True)
    except ValueError as error:
        raise ValueError(f"permitted range is not a canonical CIDR: {cidr!r} ({error})") from None
    if "/" not in cidr or network.prefixlen == 0:
        raise ValueError(f"permitted range must be a bounded CIDR, got {cidr!r}")
    return f"allow {network};"


def render_nginx_conf(params: ServerParams) -> str:
    if not params.listen:
        raise ValueError("listen needs at least one address")
    if not MIN_UNPRIVILEGED_PORT <= params.port <= 65535:
        raise ValueError(f"port must be {MIN_UNPRIVILEGED_PORT}-65535 (no root needed), got {params.port}")
    listens = "\n".join(f"    {_listen_directive(a, params.port)}" for a in params.listen)
    if not params.permitted:
        raise ValueError("permitted needs at least one range")
    rules = "\n".join(f"    {_allow_directive(r)}" for r in params.permitted)
    return f"http {{\n  server {{\n{listens}\n{rules}\n    deny all;\n\n    location / {{ return 404; }}\n  }}\n}}\n"
