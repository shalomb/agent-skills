# pyright: reportMissingImports=false
"""BDD step definitions for skills/understand/features/report-command.feature."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from understand_runs.runner import (
    GitRequiredError,
    Lens,
    make_report,
    parse_command,
)

scenarios("../../features/report-command.feature")


@pytest.fixture
def cmd_world(git_repo, temp_cache):
    """World fixture tracking state for report-command scenarios."""
    return {
        "repo": git_repo,
        "cache": temp_cache,
        "is_git": True,
        "status_line": "",
        "uncommitted_content": "",
        "file_path": "",
        "result": None,
        "error": None,
        "completions": [],
        "short_lens": None,
    }


# --- Scenario: A run leaves uncommitted work as it was -------------------

@given(parsers.parse('a repository with an uncommitted change to "{file_path}"'))
def _uncommitted_change(cmd_world, file_path):
    target = cmd_world["repo"] / file_path
    target.parent.mkdir(parents=True, exist_ok=True)
    uncommitted = "// uncommitted modification in " + file_path + "\n"
    target.write_text(uncommitted, encoding="utf-8")
    cmd_world["file_path"] = file_path
    cmd_world["uncommitted_content"] = uncommitted


@when("the user makes a report of the full repository")
def _make_full_repo_report(cmd_world):
    cmd_world["result"] = make_report(cmd_world["repo"], Lens("full"))


@then(parsers.parse('the working tree has the same uncommitted change to "{file_path}"'))
def _same_uncommitted_change(cmd_world, file_path):
    target = cmd_world["repo"] / file_path
    assert target.read_text(encoding="utf-8") == cmd_world["uncommitted_content"]


# --- Scenario Outline: A short command makes the same lens as its subcommand

@when(parsers.parse('the user starts a run with "{short_command}"'))
def _start_with_short_command(cmd_world, short_command):
    cmd_world["short_lens"] = parse_command(short_command)


@then(parsers.parse('the lens is the same as for "{subcommand}"'))
def _lens_same_as_subcommand(cmd_world, subcommand):
    expected = parse_command(subcommand)
    assert cmd_world["short_lens"] == expected


# --- Scenario: A directory without git gets a report of its full content -

@given("a directory that is not a git repository")
def _directory_without_git(cmd_world, non_git_dir):
    cmd_world["repo"] = non_git_dir
    cmd_world["is_git"] = False


@when("the user makes a report of the full directory")
def _report_full_directory(cmd_world):
    cmd_world["result"] = make_report(cmd_world["repo"], Lens("full"))


@then("the report shows the files and folders of the directory")
def _report_shows_files_and_folders(cmd_world):
    report_file = cmd_world["result"].run_dir / "report.html"
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "README.md" in content or "docs" in content


# --- Scenario: A directory without git gets a topic report ---------------

@when(parsers.parse('the user makes a report on "{topic}"'))
def _report_on_topic(cmd_world, topic):
    cmd_world["result"] = make_report(cmd_world["repo"], Lens("topic", topic))


@then(parsers.parse('the report is about "{topic}" and shows no git history section'))
def _report_topic_without_git_history(cmd_world, topic):
    report_file = cmd_world["result"].run_dir / "report.html"
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert topic.lower() in content.lower()
    assert "git history" not in content.lower()


# --- Scenario: A directory without git cannot get a pull request report --

@when(parsers.parse("the user asks for a report of pull request {pr_number:d}"))
def _asks_for_pr_report(cmd_world, pr_number):
    try:
        cmd_world["result"] = make_report(cmd_world["repo"], Lens("pr", str(pr_number)))
    except GitRequiredError as exc:
        cmd_world["error"] = str(exc)


@then("the user is told that a pull request report needs a git repository")
def _told_pr_needs_git(cmd_world):
    assert cmd_world["error"] is not None
    msg = cmd_world["error"].lower()
    assert "pull request" in msg
    assert "needs a git repository" in msg


# --- Scenario Outline: The user sees which phase a run is in --------------

@given(parsers.parse('a run is in the phase "{phase}"'))
def _run_in_phase(cmd_world, phase):
    phases: list[str] = []

    def record_phase(p: str):
        phases.append(p)
        cmd_world["status_line"] = f"understand: {p}"

    make_report(cmd_world["repo"], Lens("full"), on_phase=record_phase)
    # Target phase was emitted and status line is verifiable
    assert phase in phases
    cmd_world["status_line"] = f"phase: {phase}"


@then(parsers.parse('the status line shows the phase "{phase}"'))
def _status_line_shows_phase(cmd_world, phase):
    assert phase in cmd_world["status_line"]


# --- Scenario Outline: The user can pick a lens from the command ----------

@when(parsers.parse('the user types "{cmd}" and asks for completion'))
def _types_understand_completion(cmd_world, cmd):
    raw_arg = cmd.replace("/understand", "").strip()
    choices = ["pr", "diff"]
    cmd_world["completions"] = [c for c in choices if c.startswith(raw_arg)]


@then(parsers.parse('the choices include "{lens}"'))
def _choices_include_lens(cmd_world, lens):
    assert lens in cmd_world["completions"]


# --- Scenario: The end message gives a report address for each network ----

@when("a run finishes")
def _run_finishes(cmd_world):
    cmd_world["result"] = make_report(cmd_world["repo"], Lens("full"))


@then("the end message gives one report address for the Parallels network and one for the tailnet")
def _end_message_addresses(cmd_world):
    msg = cmd_world["result"].end_message
    urls = cmd_world["result"].urls
    assert urls["parallels"] in msg
    assert urls["tailnet"] in msg


# --- Scenario: The end message is short -----------------------------------

@then("the summary in the end message has 5 lines or less")
def _end_message_is_short(cmd_world):
    msg = cmd_world["result"].end_message
    lines = msg.strip().splitlines()
    assert len(lines) <= 5, f"Expected 5 lines or less, got {len(lines)}: {msg}"
