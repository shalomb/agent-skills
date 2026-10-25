"""Behavioural tests for scripts/triage.py, driven through its CLI with a fake ogspy."""
import json, os, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "triage.py"
FAKE = HERE / "fake_ogspy.py"
TODAY = "2026-10-25"

GOOD = "https://example.org/good"
NOOG = "https://example.org/plain"
GONE = "https://example.org/gone"
FORB = "https://example.org/forbidden"
DOWN = "https://nowhere.invalid/x"
GIST = "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"

DB = {
    GOOD: {"og": {"title": "A Good Page", "description": "Short and useful.", "site_name": "Example",
                  "type": "article", "image": "https://example.org/i.png", "url": "https://example.org/good/"}},
    NOOG: {"og": {}},
    GONE: {"error": "HTTP 404: 404 Not Found"},
    FORB: {"error": "HTTP 403: 403 Forbidden"},
    GIST: {"og": {"title": "llm-wiki", "description": "A pattern for personal wikis."}},
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.db = self.dir / "db.json"; self.db.write_text(json.dumps(DB))
        self.log = self.dir / "calls.log"
        self.env = {**os.environ, "FAKE_OGSPY_DB": str(self.db), "FAKE_OGSPY_LOG": str(self.log)}

    def tearDown(self): self.tmp.cleanup()

    def note(self, text, name="Incoming.md"):
        p = self.dir / name; p.write_text(textwrap.dedent(text).lstrip("\n")); return p

    def run_cli(self, *args, ogspy=None):
        cmd = [sys.executable, str(SCRIPT), *args]
        if args[0] == "annotate" and "--ogspy" not in args and ogspy is not False:
            cmd += ["--ogspy", str(ogspy or FAKE)]
        return subprocess.run(cmd, capture_output=True, text=True, env=self.env)

    def annotate(self, p, *extra):
        return self.run_cli("annotate", str(p), "--today", TODAY, *extra)

    def calls(self): return self.log.read_text().split() if self.log.exists() else []


class TestDetection(Base):
    def test_finds_link_lines_but_not_prose_code_frontmatter_or_callouts(self):
        p = self.note(f"""
            ---
            link: {GOOD}
            ---
            Plain prose mentioning {NOOG} in the middle.
            [Md link]({GOOD})
            - [Bullet]({NOOG})
            - [ ] [Task]({GONE})
            {FORB}
            ```
            [In code]({DOWN})
            ```
            > [!note] quoted
            > [Quoted]({DOWN})
        """)
        r = self.run_cli("cards", str(p), "--json", "--all")
        self.assertEqual(r.returncode, 0, r.stderr)
        urls = [c["url"] for c in json.loads(r.stdout)]
        self.assertEqual(urls, [GOOD, NOOG, GONE, FORB])


class TestAnnotate(Base):
    def test_ok_card_follows_the_link_line_with_all_fact_fields(self):
        p = self.note(f"# Inbox\n\n[A Good Page]({GOOD})\n\nafter\n")
        r = self.annotate(p); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(p.read_text(), textwrap.dedent(f"""\
            # Inbox

            [A Good Page]({GOOD})
            > [!link-card]- A Good Page
            > status:: ok
            > title:: A Good Page
            > description:: Short and useful.
            > site:: Example
            > type:: article
            > image:: https://example.org/i.png
            > canonical:: https://example.org/good/
            > checked:: {TODAY}

            after
        """))

    def test_bullets_keep_the_card_inside_the_list_item(self):
        p = self.note(f"- [Task]({GIST})\n- [x] [Done]({NOOG})\n")
        self.annotate(p)
        lines = p.read_text().split("\n")
        self.assertEqual(lines[0], f"- [Task]({GIST})")
        self.assertEqual(lines[1], "  > [!link-card]- llm-wiki")
        card = [l for l in lines if l.lstrip().startswith(">")]
        self.assertTrue(card and all(l.startswith("  > ") for l in card), lines)
        self.assertEqual([l for l in lines if l and not l.lstrip().startswith(">")],
                         [f"- [Task]({GIST})", f"- [x] [Done]({NOOG})"])

    def test_no_og_tags_is_recorded_not_dropped(self):
        p = self.note(f"{NOOG}\n"); self.annotate(p)
        t = p.read_text()
        self.assertIn("> [!link-card]- no Open Graph tags", t)
        self.assertIn("> status:: no-og", t)
        self.assertNotIn("title::", t)

    def test_dead_blocked_and_unreachable_are_distinguished(self):
        p = self.note(f"{GONE}\n{FORB}\n{DOWN}\n"); r = self.annotate(p)
        self.assertEqual(r.returncode, 0, "dead links are data, not a failure")
        t = p.read_text()
        self.assertRegex(t, r"status:: dead\n> http:: 404")
        self.assertRegex(t, r"status:: blocked\n> http:: 403")
        self.assertRegex(t, r"status:: error\n> error:: .*no such host")

    def test_second_run_changes_nothing_and_skips_the_network(self):
        p = self.note(f"[a]({GOOD})\n[b]({GONE})\n"); self.annotate(p)
        first, n = p.read_text(), len(self.calls())
        self.annotate(p)
        self.assertEqual(p.read_text(), first)
        self.assertEqual(len(self.calls()), n, "settled cards must not be re-fetched")

    def test_error_cards_are_retried_by_default(self):
        p = self.note(f"{DOWN}\n"); self.annotate(p)
        DB2 = {**DB, DOWN: {"og": {"title": "Back Up"}}}; self.db.write_text(json.dumps(DB2))
        self.annotate(p)
        self.assertIn("status:: ok", p.read_text()); self.assertNotIn("status:: error", p.read_text())

    def test_refresh_updates_facts_but_keeps_the_classifiers_fields(self):
        p = self.note(f"[a]({GOOD})\n"); self.annotate(p)
        text = p.read_text().replace(f"> checked:: {TODAY}", f"> checked:: {TODAY}\n> priority:: high\n> tags:: wiki, llm")
        p.write_text(text)
        self.db.write_text(json.dumps({**DB, GOOD: {"og": {"title": "Renamed", "description": "New."}}}))
        r = self.run_cli("annotate", str(p), "--today", "2026-11-01", "--refresh")
        self.assertEqual(r.returncode, 0, r.stderr)
        t = p.read_text()
        self.assertIn("> title:: Renamed", t); self.assertIn("> checked:: 2026-11-01", t)
        self.assertNotIn("site::", t, "facts absent from the new fetch are dropped")
        self.assertIn("> priority:: high", t); self.assertIn("> tags:: wiki, llm", t)
        self.assertEqual(t.count("[!link-card]"), 1)

    def test_dry_run_reports_and_writes_nothing(self):
        p = self.note(f"[a]({GOOD})\n"); before = p.read_text()
        r = self.annotate(p, "--dry-run")
        self.assertEqual(p.read_text(), before); self.assertEqual(self.calls(), [])
        self.assertIn("1", r.stdout); self.assertIn(GOOD, r.stdout)

    def test_one_fetch_per_distinct_url_but_every_occurrence_gets_a_card(self):
        p = self.note(f"[a]({GOOD})\n\n[again]({GOOD})\n"); self.annotate(p)
        self.assertEqual(self.calls(), [GOOD]); self.assertEqual(p.read_text().count("[!link-card]"), 2)

    def test_values_stay_on_one_line_and_long_descriptions_are_truncated(self):
        long = "word " * 200
        self.db.write_text(json.dumps({GOOD: {"og": {"title": "Two\nlines", "description": long}}}))
        p = self.note(f"[a]({GOOD})\n"); self.annotate(p)
        t = p.read_text()
        self.assertIn("> title:: Two lines", t)
        desc = next(l for l in t.split("\n") if l.startswith("> description::"))
        self.assertLessEqual(len(desc), 430); self.assertTrue(desc.endswith("…"))

    def test_untouched_when_there_is_nothing_to_do(self):
        p = self.note("---\nid: x\n---\n\nNo links here.\n"); before = p.read_text()
        r = self.annotate(p)
        self.assertEqual(r.returncode, 0); self.assertEqual(p.read_text(), before); self.assertEqual(self.calls(), [])


class TestCards(Base):
    def test_cards_json_exposes_facts_and_classifier_fields_for_later_stages(self):
        p = self.note(f"- [LLMWiki]({GIST})\n- [x]({GONE})\n"); self.annotate(p)
        p.write_text(p.read_text().replace(f"> checked:: {TODAY}\n", f"> checked:: {TODAY}\n  > priority:: high\n", 1))
        r = self.run_cli("cards", str(p), "--json"); self.assertEqual(r.returncode, 0, r.stderr)
        cards = json.loads(r.stdout)
        self.assertEqual([c["url"] for c in cards], [GIST, GONE])
        self.assertEqual(cards[0]["text"], "LLMWiki")
        self.assertEqual(cards[0]["fields"]["title"], "llm-wiki")
        self.assertEqual(cards[0]["fields"]["priority"], "high")
        self.assertEqual(cards[1]["fields"]["status"], "dead")
        self.assertEqual(cards[0]["line"], 1)

    def test_status_filter(self):
        p = self.note(f"{GOOD}\n{GONE}\n"); self.annotate(p)
        r = self.run_cli("cards", str(p), "--json", "--status", "dead")
        self.assertEqual([c["url"] for c in json.loads(r.stdout)], [GONE])

    def test_cards_without_all_lists_only_annotated_links(self):
        p = self.note(f"{GOOD}\n{GONE}\n"); self.annotate(p)
        p.write_text(p.read_text() + f"{NOOG}\n")
        listed = [c["url"] for c in json.loads(self.run_cli("cards", str(p), "--json").stdout)]
        self.assertEqual(listed, [GOOD, GONE])


class TestFailureModes(Base):
    def test_missing_ogspy_is_a_clear_error_and_leaves_the_file_alone(self):
        p = self.note(f"{GOOD}\n"); before = p.read_text()
        r = self.run_cli("annotate", str(p), "--ogspy", "/nonexistent/ogspy", "--today", TODAY)
        self.assertEqual(r.returncode, 2); self.assertIn("ogspy", r.stderr); self.assertEqual(p.read_text(), before)

    def test_unusable_ogspy_output_aborts_without_writing(self):
        bad = self.dir / "bad"; bad.write_text("#!/bin/sh\necho 'not json at all'\n"); bad.chmod(0o755)
        p = self.note(f"{GOOD}\n"); before = p.read_text()
        r = self.run_cli("annotate", str(p), "--ogspy", str(bad), "--today", TODAY)
        self.assertEqual(r.returncode, 2); self.assertEqual(p.read_text(), before)


if __name__ == "__main__":
    unittest.main()
