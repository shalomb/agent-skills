"""Unit tests for finding the VM's own addresses inside a network (pure)."""

# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
from __future__ import annotations

import json

import pytest

from report_server.addresses import addresses_in, parse_ip_addr_json
from report_server.networks import PARALLELS_RANGES, TAILNET_RANGES

# Shape of `ip -j addr show`, trimmed to what matters.
VM_WITH_TAILSCALE = json.dumps(
    [
        {"ifname": "lo", "addr_info": [{"local": "127.0.0.1"}, {"local": "::1"}]},
        {
            "ifname": "enp0s5",
            "addr_info": [
                {"local": "10.211.55.3"},
                {"local": "fdb2:2c26:f4e4:0:d983:6684:5e7e:7f19"},
                {"local": "fe80::21c:42ff:fecb:cfe2"},
            ],
        },
        {
            "ifname": "tailscale0",
            "addr_info": [
                {"local": "100.99.83.53"},
                {"local": "fd7a:115c:a1e0::6d01:53e4"},
                {"local": "fe80::d82f:5805:6e5b:6a83"},
            ],
        },
    ]
)
VM_TAILSCALE_DOWN = json.dumps([entry for entry in json.loads(VM_WITH_TAILSCALE) if entry["ifname"] != "tailscale0"])


def test_parse_lists_every_local_address():
    assert "100.99.83.53" in parse_ip_addr_json(VM_WITH_TAILSCALE)
    assert "10.211.55.3" in parse_ip_addr_json(VM_WITH_TAILSCALE)


def test_parallels_address_is_the_one_inside_the_parallels_range():
    assert addresses_in(PARALLELS_RANGES, parse_ip_addr_json(VM_WITH_TAILSCALE)) == ("10.211.55.3",)


def test_tailnet_addresses_are_both_families_in_the_tailnet_ranges():
    assert addresses_in(TAILNET_RANGES, parse_ip_addr_json(VM_WITH_TAILSCALE)) == (
        "100.99.83.53",
        "fd7a:115c:a1e0::6d01:53e4",
    )


def test_with_tailscale_down_there_is_no_tailnet_address_and_parallels_is_unchanged():
    addresses = parse_ip_addr_json(VM_TAILSCALE_DOWN)
    assert addresses_in(TAILNET_RANGES, addresses) == ()
    assert addresses_in(PARALLELS_RANGES, addresses) == ("10.211.55.3",)


def test_other_interfaces_never_match():
    assert addresses_in(PARALLELS_RANGES + TAILNET_RANGES, ("127.0.0.1", "::1", "192.168.1.9", "fe80::1")) == ()


def test_unparseable_output_is_an_error_not_an_empty_list():
    with pytest.raises(ValueError, match="ip -j addr"):
        parse_ip_addr_json("not json")
