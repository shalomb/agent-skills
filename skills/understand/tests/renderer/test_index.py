"""Unit tests for the per-repo index of runs (spec unit 3: index.html)."""
import os

from pages import Page
from understand_render.index import write_repo_index


def make_run(repo, lens, run, mtime):
    run_dir = repo / lens / run
    run_dir.mkdir(parents=True)
    report = run_dir / "report.html"
    report.write_text("<html></html>")
    os.utime(report, (mtime, mtime))
    return run_dir


def test_index_lists_each_lens_with_its_runs_newest_first(tmp_path):
    make_run(tmp_path, "full", "abc1234-20260101T000000Z", 100)
    make_run(tmp_path, "full", "def5678-20260102T000000Z", 200)
    make_run(tmp_path, "topic-auth", "abc1234-20260103T000000Z", 300)
    write_repo_index(tmp_path, "my-repo")
    links = Page.read(tmp_path / "index.html").links
    assert links == [
        "full/def5678-20260102T000000Z/report.html",
        "full/abc1234-20260101T000000Z/report.html",
        "topic-auth/abc1234-20260103T000000Z/report.html",
    ]


def test_index_skips_the_latest_link_and_directories_without_a_report(tmp_path):
    run = make_run(tmp_path, "full", "abc1234-20260101T000000Z", 100)
    (tmp_path / "full" / "latest").symlink_to(run.name)
    (tmp_path / "full" / "partial").mkdir()
    write_repo_index(tmp_path, "my-repo")
    assert Page.read(tmp_path / "index.html").links == ["full/abc1234-20260101T000000Z/report.html"]


def test_index_of_a_repo_without_runs_says_so(tmp_path):
    write_repo_index(tmp_path, "my-repo")
    text = (tmp_path / "index.html").read_text()
    assert "No reports yet" in text


def test_index_escapes_the_repo_name_and_loads_nothing_by_address(tmp_path):
    write_repo_index(tmp_path, "<b>x</b>")
    text = (tmp_path / "index.html").read_text()
    page = Page(text)
    assert "<b>x</b>" not in text and page.script_srcs == [] and page.link_hrefs == []
