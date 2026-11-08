"""Command line: render | sudoers. Prints text; the installer script does the privileged work."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from report_server.networks import PARALLELS_RANGES, TAILNET_RANGES
from report_server.paths import resolve_serve_root

from .conf import SystemParams, render_sudoers, render_system_conf

LOOPBACK_RANGES = ("127.0.0.0/8", "::1/128")
DEFAULT_PORT = 80


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(prog="report_server_system", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="print the conf.d snippet")
    render.add_argument("--port", type=int, default=DEFAULT_PORT)
    sudoers = commands.add_parser("sudoers", help="print the sudoers.d rule")
    sudoers.add_argument("--user", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "sudoers":
            print(render_sudoers(args.user), end="")
            return 0
        home = Path(env["HOME"])
        shadow = Path(env.get("XDG_CACHE_HOME") or home / ".cache") / "agent-skills"
        params = SystemParams(
            port=args.port,
            permitted=LOOPBACK_RANGES + PARALLELS_RANGES + TAILNET_RANGES,
            shadow_root=resolve_serve_root(shadow),
            src_root=resolve_serve_root(home / "projects"),
        )
        print(render_system_conf(params), end="")
        return 0
    except ValueError as error:
        print(f"report_server_system: {error}", file=sys.stderr)
        return 2
