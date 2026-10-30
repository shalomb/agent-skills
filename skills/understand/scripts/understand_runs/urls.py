# pyright: reportMissingImports=false
"""Report URL construction for Parallels and Tailnet networks (ADR 0002, ADR 0003)."""

from __future__ import annotations

import ipaddress
import json
import subprocess
from collections.abc import Sequence

DEFAULT_PORT = 8787
DEFAULT_PARALLELS_IP = "10.211.55.3"
DEFAULT_TAILNET_IP = "100.99.83.53"

PARALLELS_NETWORKS = [ipaddress.ip_network("10.211.55.0/24")]
TAILNET_NETWORKS = [
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("fd7a:115c:a1e0::/48"),
]


def _discover_local_ips() -> list[str]:
    """Queries `ip -j addr show` to find local IP addresses."""
    try:
        res = subprocess.run(
            ["ip", "-j", "addr", "show"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            interfaces = json.loads(res.stdout)
            return [
                info["local"]
                for iface in interfaces
                for info in iface.get("addr_info", [])
                if "local" in info
            ]
    except (subprocess.SubprocessError, OSError, ValueError):
        return []
    return []


def _find_matching_ip(ips: Sequence[str], networks: Sequence[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> str | None:
    for ip_str in ips:
        try:
            addr = ipaddress.ip_address(ip_str)
            if any(addr in net for net in networks):
                return ip_str
        except ValueError:
            continue
    return None


def get_network_ips() -> tuple[str, str]:
    """Returns (parallels_ip, tailnet_ip) by inspecting interfaces or falling back to defaults."""
    discovered = _discover_local_ips()
    parallels_ip = _find_matching_ip(discovered, PARALLELS_NETWORKS) or DEFAULT_PARALLELS_IP
    tailnet_ip = _find_matching_ip(discovered, TAILNET_NETWORKS) or DEFAULT_TAILNET_IP
    return parallels_ip, tailnet_ip


def get_report_urls(
    repo_slug: str,
    lens_id: str,
    run_id: str,
    port: int = DEFAULT_PORT,
    parallels_ip: str | None = None,
    tailnet_ip: str | None = None,
) -> dict[str, str]:
    """Builds the report URLs for Parallels network and Tailnet."""
    p_ip = parallels_ip
    t_ip = tailnet_ip
    if not p_ip or not t_ip:
        disc_p, disc_t = get_network_ips()
        p_ip = p_ip or disc_p
        t_ip = t_ip or disc_t

    path = f"/r/understand/{repo_slug}/{lens_id}/{run_id}/"
    return {
        "parallels": f"http://{p_ip}:{port}{path}",
        "tailnet": f"http://{t_ip}:{port}{path}",
    }


def format_end_message(
    repo_slug: str,
    lens_id: str,
    urls: dict[str, str],
    summary: str = "Report generated successfully.",
) -> str:
    """Formats a concise completion message with URLs and summary in 5 lines or less."""
    first_line_summary = summary.strip().splitlines()[0] if summary.strip() else "Report generated."
    return (
        f"Report ready: {repo_slug} ({lens_id})\n"
        f"Parallels: {urls['parallels']}\n"
        f"Tailnet:   {urls['tailnet']}\n"
        f"Summary:   {first_line_summary}"
    )
