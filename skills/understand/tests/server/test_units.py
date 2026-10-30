# pyright: reportMissingImports=false
# (pytest comes from `uv run --with`; conftest.py puts report_server on sys.path)
"""Unit tests for the systemd --user unit file and the install plan (pure)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from report_server.units import (
    UNIT_NAME,
    Run,
    WriteFile,
    apply_plan,
    install_plan,
    render_unit,
)

SERVER_DIR = Path("/home/u/projects/agent-skills/skills/understand/server")
UNIT = render_unit(python="/usr/bin/python3", server_dir=SERVER_DIR, port=8787)


def setting(name: str, text: str = UNIT) -> list[str]:
    return re.findall(rf"^{name}=(.*)$", text, re.MULTILINE)


class TestUnitFile:
    def test_one_template_unit_gives_one_independent_instance_per_network(self):
        assert UNIT_NAME == "understand-report-server@.service"
        assert setting("ExecStart") == [
            "/usr/bin/python3 -m report_server run --network %i --port 8787"
        ]

    def test_the_instances_do_not_depend_on_each_other(self):
        for coupling in ("Requires", "Wants", "BindsTo", "PartOf", "Requisite", "Conflicts", "Before", "After"):
            assert setting(coupling) == [], coupling

    def test_a_failed_start_is_retried_without_giving_up(self):
        # The tailnet instance fails while tailscale is down and must come up
        # by itself when it returns. A user unit cannot order after the system
        # tailscaled.service, so retrying is the mechanism.
        assert setting("Restart") == ["on-failure"]
        assert setting("RestartSec") == ["10"]
        assert setting("StartLimitIntervalSec") == ["0"]

    def test_runs_as_the_user_with_no_privilege_escalation(self):
        assert setting("User") == []
        assert setting("NoNewPrivileges") == ["yes"]
        assert "sudo" not in UNIT

    def test_starts_with_the_user_session(self):
        assert setting("WantedBy") == ["default.target"]

    def test_finds_the_package_without_installing_it(self):
        assert setting("Environment") == [f"PYTHONPATH={SERVER_DIR}"]

    def test_system_tools_are_not_touched(self):
        assert "/etc/nginx" not in UNIT and "nginx.service" not in UNIT

    @pytest.mark.skipif(shutil.which("systemd-analyze") is None, reason="systemd-analyze missing")
    def test_systemd_accepts_the_unit(self, tmp_path: Path):
        unit_path = tmp_path / "understand-report-server@parallels.service"
        unit_path.write_text(render_unit(python="/usr/bin/python3", server_dir=SERVER_DIR, port=8787))
        result = subprocess.run(
            ["systemd-analyze", "--user", "verify", str(unit_path)],
            capture_output=True,
            text=True,
        )
        problems = [l for l in result.stderr.splitlines() if "understand-report-server" in l]
        assert problems == []


class TestInstallPlan:
    UNIT_DIR = Path("/home/u/.config/systemd/user")

    def plan(self, enable=False):
        return install_plan(UNIT, self.UNIT_DIR, enable=enable)

    def test_writes_only_the_unit_file_into_the_unit_dir(self):
        writes = [a for a in self.plan() if isinstance(a, WriteFile)]
        assert [w.path for w in writes] == [self.UNIT_DIR / UNIT_NAME]
        assert writes[0].content == UNIT

    def test_without_enable_it_only_reloads_the_user_manager(self):
        runs = [a.argv for a in self.plan() if isinstance(a, Run)]
        assert runs == [("systemctl", "--user", "daemon-reload")]

    def test_enable_starts_both_instances_independently(self):
        runs = [a.argv for a in self.plan(enable=True) if isinstance(a, Run)]
        assert runs[1:] == [
            ("systemctl", "--user", "enable", "--now", "understand-report-server@parallels.service"),
            ("systemctl", "--user", "enable", "--now", "understand-report-server@tailnet.service"),
        ]

    def test_nothing_in_the_plan_needs_root(self):
        for action in self.plan(enable=True):
            text = str(action)
            assert "sudo" not in text and "/etc/" not in text and "--system" not in text

    def test_apply_writes_files_and_runs_commands_in_order(self, tmp_path: Path):
        calls: list[tuple[str, ...]] = []
        plan = install_plan(UNIT, tmp_path / "units", enable=True)
        apply_plan(plan, run=lambda argv: calls.append(argv))
        assert (tmp_path / "units" / UNIT_NAME).read_text() == UNIT
        assert [c[2] for c in calls] == ["daemon-reload", "enable", "enable"]

    def test_apply_stops_at_the_first_failing_command(self, tmp_path: Path):
        def failing(argv):
            raise subprocess.CalledProcessError(1, argv)

        with pytest.raises(subprocess.CalledProcessError):
            apply_plan(install_plan(UNIT, tmp_path, enable=True), run=failing)
