"""Command line: render | run | install. The only module here that does I/O."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from .addresses import parse_ip_addr_json
from .instance import NoAddressForNetwork, build_instance
from .networks import NETWORKS
from .nginx_conf import ServerParams, render_nginx_conf
from .paths import resolve_serve_root
from .units import Action, WriteFile, apply_plan, install_plan, render_unit

DEFAULT_PORT = 8787
NGINX_BIN = "/usr/sbin/nginx"
EXIT_NO_ADDRESS = 3  # systemd retries on any non-zero exit


def _params(args: argparse.Namespace, env: Mapping[str, str]) -> ServerParams:
    ip_json = Path(args.ip_json).read_text() if args.ip_json else subprocess.run(
        ["ip", "-j", "addr", "show"], check=True, capture_output=True, text=True
    ).stdout
    shadow = Path(env.get("XDG_CACHE_HOME") or f"{env['HOME']}/.cache") / "agent-skills"
    if args.command == "run":
        shadow.mkdir(parents=True, exist_ok=True)  # no report may exist yet
    return build_instance(
        args.network,
        parse_ip_addr_json(ip_json),
        port=args.port,
        shadow_root=resolve_serve_root(shadow),
        src_root=resolve_serve_root(Path(env["HOME"]) / "projects"),
        env=env,
    )


def _run(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    try:
        params = _params(args, env)
    except NoAddressForNetwork as error:
        print(f"report-server: {error}", file=sys.stderr)
        return EXIT_NO_ADDRESS
    conf = render_nginx_conf(params)
    for directory in (params.run_dir, params.log_dir, params.temp_dir):
        directory.mkdir(parents=True, exist_ok=True)
    conf_path = params.run_dir / "nginx.conf"
    conf_path.write_text(conf)
    os.execv(NGINX_BIN, [NGINX_BIN, "-e", "stderr", "-p", str(params.run_dir), "-c", str(conf_path)])


def _install(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    unit_dir = Path(args.unit_dir or f"{env['HOME']}/.config/systemd/user")
    unit = render_unit(
        python=sys.executable if args.python is None else args.python,
        server_dir=Path(__file__).resolve().parent.parent,
        port=args.port,
    )
    plan: list[Action] = install_plan(unit, unit_dir, enable=args.enable)
    if args.no_systemctl:
        plan = [a for a in plan if isinstance(a, WriteFile)]
    if args.dry_run:
        for action in plan:
            if isinstance(action, WriteFile):
                print(f"would write {action.path}:\n{action.content}")
            else:
                print(f"would run: {' '.join(action.argv)}")
        return 0
    apply_plan(plan)
    return 0


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(prog="report_server", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("render", "run"):
        sub = commands.add_parser(name)
        sub.add_argument("--network", required=True, choices=sorted(NETWORKS))
        sub.add_argument("--port", type=int, default=DEFAULT_PORT)
        sub.add_argument("--ip-json", help="read `ip -j addr show` output from this file (tests)")
    install = commands.add_parser("install", help="write the systemd --user unit")
    install.add_argument("--dry-run", action="store_true", help="print what would be done, change nothing")
    install.add_argument("--enable", action="store_true", help="also enable --now both instances")
    install.add_argument("--no-systemctl", action="store_true", help="write the unit file only")
    install.add_argument("--unit-dir", help="default: ~/.config/systemd/user")
    install.add_argument("--python", help="interpreter for ExecStart (default: this one)")
    install.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)

    if args.command == "render":
        print(render_nginx_conf(_params(args, env)), end="")
        return 0
    if args.command == "run":
        return _run(args, env)
    return _install(args, env)
