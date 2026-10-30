"""Find the VM's own addresses that lie inside given networks. Pure parsing, no I/O."""

from __future__ import annotations

import ipaddress
import json


def parse_ip_addr_json(text: str) -> tuple[str, ...]:
    """All local addresses from the output of `ip -j addr show`."""
    try:
        interfaces = json.loads(text)
        return tuple(info["local"] for interface in interfaces for info in interface["addr_info"])
    except (ValueError, KeyError, TypeError):
        raise ValueError("cannot read the output of `ip -j addr show`") from None


def addresses_in(ranges: tuple[str, ...], addresses: tuple[str, ...]) -> tuple[str, ...]:
    """The addresses inside any of `ranges`, in input order."""
    networks = [ipaddress.ip_network(r) for r in ranges]
    return tuple(a for a in addresses if any(ipaddress.ip_address(a) in n for n in networks))
