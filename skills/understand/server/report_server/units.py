"""systemd --user unit text and the install plan. Pure: nothing here touches the system."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .networks import NETWORKS

UNIT_NAME = "understand-report-server@.service"


@dataclass(frozen=True)
class WriteFile:
    path: Path
    content: str


@dataclass(frozen=True)
class Run:
    argv: tuple[str, ...]


Action = WriteFile | Run


def render_unit(*, python: str, server_dir: Path, port: int) -> str:
    """One template unit; `%i` is the network, so `@parallels` and `@tailnet` are
    two independent services with no dependency between them.

    A user unit cannot be ordered after the system `tailscaled.service` (a user
    manager does not see system units). The tailnet instance therefore fails
    while the tailnet address is absent and `Restart=on-failure` brings it up
    once tailscale is back; `StartLimitIntervalSec=0` stops systemd giving up.
    """
    return f"""\
[Unit]
Description=/understand report server (%i network)
Documentation=file://{server_dir}/README.md
StartLimitIntervalSec=0

[Service]
Type=exec
Environment=PYTHONPATH={server_dir}
ExecStart={python} -m report_server run --network %i --port {port}
Restart=on-failure
RestartSec=10
NoNewPrivileges=yes

[Install]
WantedBy=default.target
"""


def install_plan(unit_text: str, unit_dir: Path, *, enable: bool) -> list[Action]:
    plan: list[Action] = [
        WriteFile(unit_dir / UNIT_NAME, unit_text),
        Run(("systemctl", "--user", "daemon-reload")),
    ]
    if enable:
        template, suffix = UNIT_NAME.split("@")
        plan += [
            Run(("systemctl", "--user", "enable", "--now", f"{template}@{network}{suffix}"))
            for network in NETWORKS
        ]
    return plan


def apply_plan(plan: list[Action], *, run: Callable[[tuple[str, ...]], object] | None = None) -> None:
    runner = run or (lambda argv: subprocess.run(argv, check=True))
    for action in plan:
        if isinstance(action, WriteFile):
            action.path.parent.mkdir(parents=True, exist_ok=True)
            action.path.write_text(action.content)
        else:
            runner(action.argv)
