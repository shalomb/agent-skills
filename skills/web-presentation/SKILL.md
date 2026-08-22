---
name: web-presentation
description: |
  Render a Markdown document into a self-contained, themed HTML page or slide
  deck for sharing with a team — no external assets, opens offline, attachable
  to mail or Teams. Use when asked to share a document as a web page, publish
  or present notes, turn a proposal or ADR into slides, make a markdown file
  presentable, or produce something readable for colleagues who will not open
  a repo. Triggers on "share this as a webpage", "make slides from this",
  "present this", "publish these notes", "turn this into a deck".
metadata:
  version: 1.0.0
---

# Web Presentation

Turn a Markdown file into something a team can actually read: a typeset single-page
document, or a slide deck driven live. One script, both modes, one self-contained file.

## Quick usage

```bash
# themed document (default) -> ~/Downloads/<name>.html
scripts/build.py notes.md

# slide deck, one slide per `##`
scripts/build.py notes.md --mode deck

# explicit destination and owning-team label
scripts/build.py notes.md -o ~/Downloads/proposal.html -e "Platform Engineering · Draft"
```

Options: `-m/--mode doc|deck` · `-o/--out` · `-t/--title` (override the H1) ·
`-e/--eyebrow` (small-caps line above the title) · `--theme` (alternative stylesheet).

Requires `pandoc` on PATH. No other dependencies, no network at build or view time.

## Workflow

1. **Pick the mode.** `doc` for something people read alone; `deck` for something walked
   through live. Producing both from one source is normal — offer it.
2. **Render.** Run the script.
3. **Verify before handing it over.** Do not assume the transform worked — the regexes
   fail silently on unexpected input. Check the counts match the source:

   ```bash
   python3 - <<'PY'
   import re; t=open('/path/to/out.html').read()
   print('sections', len(re.findall(r'<span class="num">', t)),
         '| toc', len(re.findall(r'<li><a href="#', t)),
         '| meta', re.findall(r'<dt>(.*?)</dt>', t),
         '| tables', len(re.findall(r'<div class="tw">', t)))
   PY
   ```

   A section count below the number of `##` headings in the source means a transform
   missed — see the troubleshooting section of `references/authoring.md`.
4. **Report the path and what to do with it** (open in a browser, print to PDF, attach).

## What the renderer does with the Markdown

Beyond pandoc's defaults it recognises a few conventions and styles them:

- `# Title` becomes the masthead or title slide
- a leading paragraph of `**Label:** value` lines becomes a definition-list meta block,
  with labels discovered rather than hardcoded
- `**The ask in one sentence:** …` becomes an emphasised standfirst
- `## 3. Section` splits the number into an accent chip
- `[GAP — …]`, `[CHECK — …]`, `[TODO …]`, `[NOTE …]`, `[RISK …]`, `[OPEN …]` become
  status chips, or callout blocks when they stand alone
- tables get scrollable containers; YAML frontmatter is stripped

None of these are required — plain Markdown renders fine. In deck mode `---` inside a
section starts a continuation slide, which is the main tool for pacing.

**Read `references/authoring.md`** for the full conventions table, deck pacing and density
guidance, keyboard shortcuts, theming via CSS custom properties, and troubleshooting.

## Editing the script

If modifying `scripts/build.py`, two constraints are load-bearing:

- **Keep `--wrap=none` on the pandoc call.** Pandoc otherwise wraps output at 72 columns,
  splitting long opening tags and inline `<strong>` labels across lines. Every downstream
  regex then misses those elements *silently* — sections vanish from the deck and the TOC
  with no error.
- **Match tags as `<h2\s+id=`**, never `<h2 id=`, for the same reason.

Theme changes belong in `assets/theme.css` (shared) and `assets/deck.css` (slide geometry
only); both are driven by the `:root` custom properties, so recolouring means editing
those properties rather than the rules.
