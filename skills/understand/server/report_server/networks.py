"""The networks that may read reports (ADR 0003)."""

PARALLELS_RANGES = ("10.211.55.0/24",)
TAILNET_RANGES = ("100.64.0.0/10", "fd7a:115c:a1e0::/48")

# One server instance per key. Each listens only on the VM's own addresses that
# lie inside its ranges, so one can fail to start (tailscale down) without
# touching the other.
NETWORKS = {"parallels": PARALLELS_RANGES, "tailnet": TAILNET_RANGES}
