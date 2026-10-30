# pyright: reportMissingImports=false
"""BDD step definitions for skills/understand/features/report-glossary.feature (Step 6)."""

from __future__ import annotations

import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from understand_plan.models import Lens
from understand_runs.runner import make_report

scenarios("../../features/report-glossary.feature")


class SimpleLinkParser(HTMLParser):
    """Parses HTML to extract href links and elements with IDs."""

    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []  # (href, text)
        self.elements_by_id: dict[str, str] = {}
        self._current_tag: str | None = None
        self._current_id: str | None = None
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        elem_id = attrs_dict.get("id")
        href = attrs_dict.get("href")

        if href:
            self._current_href = href
            self._current_text = []

        if elem_id:
            self._current_id = elem_id
            self.elements_by_id[elem_id] = ""

    def handle_data(self, data):
        if self._current_href:
            self._current_text.append(data)
        if self._current_id:
            self.elements_by_id[self._current_id] += " " + data.strip()

    def handle_endtag(self, tag):
        if self._current_href:
            self.links.append((self._current_href, " ".join(self._current_text).strip()))
            self._current_href = None
            self._current_text = []
        if self._current_id:
            self._current_id = None


@pytest.fixture
def glossary_world(git_repo, temp_cache):
    """World fixture tracking state for report-glossary scenarios."""
    return {
        "repo": git_repo,
        "cache": temp_cache,
        "result": None,
        "definitions": [],
        "areas": [],
    }


# --- Scenario: Contexts come from the repository glossary map -------------

@given(parsers.parse('the repository has a glossary map with the contexts "{c1}" and "{c2}"'))
def _repo_has_glossary_map(glossary_world, c1, c2):
    repo = glossary_world["repo"]
    map_content = (
        f"# Glossary Map\n\n"
        f"## {c1}\n"
        f"**Invoice**: Bill sent to customer.\n"
        f"**Account**: Payer of invoices.\n\n"
        f"## {c2}\n"
        f"**User**: Authenticated person.\n"
        f"**Session**: Login state.\n"
    )
    (repo / "GLOSSARY-MAP.md").write_text(map_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add glossary map"], cwd=repo, check=True)


@when("a report is made")
def _make_report(glossary_world):
    repo = glossary_world["repo"]
    glossary_world["result"] = make_report(repo, Lens("full"))


@then(parsers.parse('the glossary groups its terms under "{c1}" and "{c2}"'))
def _glossary_groups_under_contexts(glossary_world, c1, c2):
    result = glossary_world["result"]
    assert result is not None, "Report result is missing"
    assert (result.run_dir / "report.html").exists()

    report_html = (result.run_dir / "report.html").read_text(encoding="utf-8")
    assert 'id="glossary"' in report_html

    glossary_section = report_html.split('id="glossary"', 1)[1].split("</section>", 1)[0]
    assert c1 in glossary_section, f"Expected context {c1} in glossary section"
    assert c2 in glossary_section, f"Expected context {c2} in glossary section"

    # Also check glossary.json in run_dir
    glossary_json_path = result.run_dir / "glossary.json"
    assert glossary_json_path.exists()
    data = json.loads(glossary_json_path.read_text(encoding="utf-8"))
    context_names = {ctx["name"] for ctx in data.get("contexts", [])}
    assert {c1, c2} <= context_names


# --- Scenario: Contexts are found when the repository has no glossary map -

@given("the repository has no glossary map")
def _repo_has_no_glossary_map(glossary_world):
    repo = glossary_world["repo"]
    for candidate in ["GLOSSARY-MAP.md", "GLOSSARY.md", "glossary-map.md", "glossary.md"]:
        f = repo / candidate
        if f.exists():
            f.unlink()
    docs = repo / "docs"
    if docs.exists():
        for candidate in ["GLOSSARY-MAP.md", "GLOSSARY.md"]:
            f = docs / candidate
            if f.exists():
                f.unlink()


@given(parsers.parse('the areas "{area1}" and "{area2}" use different terms'))
def _areas_use_different_terms(glossary_world, area1, area2):
    repo = glossary_world["repo"]
    glossary_world["areas"] = [area1, area2]

    # Create area 1
    d1 = repo / area1
    d1.mkdir(parents=True, exist_ok=True)
    (d1 / "billing.ts").write_text(
        "// Invoice: bill sent to customer\n"
        "export class Invoice { id: string; }\n"
        "// Account: payer of invoices\n"
        "export class Account { balance: number; }\n",
        encoding="utf-8",
    )

    # Create area 2
    d2 = repo / area2
    d2.mkdir(parents=True, exist_ok=True)
    (d2 / "identity.ts").write_text(
        "// User: login principal\n"
        "export class User { username: string; }\n"
        "// Session: authenticated session token\n"
        "export class Session { token: string; }\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add area source files"], cwd=repo, check=True)


@then("the glossary groups its terms under a context for each of the two areas")
def _glossary_groups_under_two_areas(glossary_world):
    result = glossary_world["result"]
    assert result is not None

    report_html = (result.run_dir / "report.html").read_text(encoding="utf-8")
    glossary_section = report_html.split('id="glossary"', 1)[1].split("</section>", 1)[0]

    areas = glossary_world["areas"]
    for area in areas:
        # Context can be either the area base name ("billing") or the relative path ("src/billing")
        base = Path(area).name
        assert base in glossary_section or area in glossary_section, (
            f"Expected context for area {area} in glossary section"
        )


# --- Scenario: A term with two meanings is flagged as a collision ---------

@given(parsers.parse('"{term}" means "{meaning}" in the context "{context}"'))
def _term_means_in_context(glossary_world, term, meaning, context):
    glossary_world["definitions"].append((term, meaning, context))

    # Write or update GLOSSARY-MAP.md
    repo = glossary_world["repo"]
    lines = ["# Glossary Map\n"]
    contexts_map: dict[str, list[tuple[str, str]]] = {}
    for t, m, c in glossary_world["definitions"]:
        contexts_map.setdefault(c, []).append((t, m))

    for c, terms in contexts_map.items():
        lines.append(f"## {c}\n")
        for t, m in terms:
            lines.append(f"**{t}**: {m}\n")

    (repo / "GLOSSARY-MAP.md").write_text("\n".join(lines), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "update terms"], cwd=repo, check=True)


@then(parsers.parse('the glossary flags "{term}" as a collision with a link to each meaning'))
def _glossary_flags_collision_with_links(glossary_world, term):
    result = glossary_world["result"]
    assert result is not None

    report_html = (result.run_dir / "report.html").read_text(encoding="utf-8")
    glossary_section = report_html.split('id="glossary"', 1)[1].split("</section>", 1)[0]

    # Verify collision is flagged
    assert "collision" in glossary_section.lower()
    assert term in glossary_section

    # Verify links exist to each meaning
    parser = SimpleLinkParser()
    parser.feed(glossary_section)

    collision_links = [
        href for href, _ in parser.links if href.startswith("#") and term.lower() in href.lower()
    ]
    assert len(collision_links) >= 2, (
        f"Expected at least 2 collision links for {term}, found: {collision_links}"
    )

    # Verify each anchor target exists in report_html and contains the expected meaning
    for href in collision_links:
        anchor_id = href.lstrip("#")
        assert f'id="{anchor_id}"' in report_html, f"Anchor id {anchor_id} not found in report"

    # Both definitions are present in the glossary
    for t, m, _ in glossary_world["definitions"]:
        if t == term:
            assert m in glossary_section, f"Meaning '{m}' not found in glossary section"


# --- Scenario: The report offers a glossary draft for the repository ------

@given("the repository has no glossary")
def _repo_has_no_glossary(glossary_world):
    repo = glossary_world["repo"]
    for name in ["GLOSSARY.md", "GLOSSARY-MAP.md", "glossary.md", "glossary-map.md"]:
        p = repo / name
        if p.exists():
            p.unlink()
    docs = repo / "docs"
    if docs.exists():
        for name in ["GLOSSARY.md", "GLOSSARY-MAP.md"]:
            p = docs / name
            if p.exists():
                p.unlink()


@then("the report offers a glossary draft that the user can apply")
def _report_offers_glossary_draft(glossary_world):
    result = glossary_world["result"]
    assert result is not None

    # Check shadow storage bundle contains glossary-draft.md
    draft_file = result.run_dir / "glossary-draft.md"
    assert draft_file.exists(), "glossary-draft.md missing from run_dir in shadow storage"
    draft_text = draft_file.read_text(encoding="utf-8")
    assert "# Glossary" in draft_text

    # Check report.html includes the draft
    report_html = (result.run_dir / "report.html").read_text(encoding="utf-8")
    glossary_section = report_html.split('id="glossary"', 1)[1].split("</section>", 1)[0]
    assert "draft" in glossary_section.lower()
    assert "# Glossary" in glossary_section or "GLOSSARY.md" in glossary_section


# --- Scenario: A report never writes the glossary draft to the repository -

@then("the repository has no new or changed glossary file")
def _repo_has_no_glossary_files_written(glossary_world):
    repo = glossary_world["repo"]

    for name in ["GLOSSARY.md", "glossary.md", "glossary-draft.md", "GLOSSARY-DRAFT.md"]:
        assert not (repo / name).exists(), f"Found mutated file in repo: {name}"

    # Check git working tree has no uncommitted/untracked files
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=repo, text=True
    ).strip()
    assert status == "", f"Repository was mutated: {status}"
