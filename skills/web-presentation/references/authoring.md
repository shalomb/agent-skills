# Authoring for web-presentation

Contents:
- [Source conventions](#source-conventions)
- [Choosing a mode](#choosing-a-mode)
- [Writing for deck mode](#writing-for-deck-mode)
- [Theming](#theming)
- [Sharing the output](#sharing-the-output)
- [Troubleshooting](#troubleshooting)

## Source conventions

The renderer reads ordinary GitHub-flavoured Markdown. Five optional conventions unlock
the richer layout — none are required, and content lacking them still renders.

| Convention | Markdown | Result |
|---|---|---|
| Title | `# Some Title` | Masthead / title slide. Removed from the body. Override with `-t`. |
| Preamble fields | A single paragraph of `**Label:** value` lines | Definition-list meta block under the title |
| Lede | `**The ask in one sentence:** …` | Pulled out as an emphasised standfirst |
| Numbered sections | `## 3. Section title` | Number becomes an accent chip; title sits beside it |
| Status markers | `[GAP — no figures yet]` | Inline chip. A paragraph that is *only* a marker becomes a callout block. |

Recognised marker words: `GAP`, `CHECK`, `TODO`, `NOTE`, `RISK`, `OPEN`.

Preamble labels are discovered, not hardcoded — any `**Label:**` at the start of the first
paragraph becomes a row. Adding a new field to the source needs no change to the script.

YAML frontmatter is stripped and ignored, so Obsidian notes work unmodified.

## Choosing a mode

**`--mode doc`** (default) — long-form reading. Sidebar table of contents at ≥1060px,
full text, print stylesheet. Use for documents people will read on their own time:
proposals, discussion notes, ADRs, design write-ups.

**`--mode deck`** — one slide per `##` heading, scroll-snapped, with keyboard navigation.
Use for walking a group through an argument live.

Generating both from the same source is normal and cheap. The document is the artefact of
record; the deck is the version you drive in the room.

## Writing for deck mode

Slides are split at `##`. Inside a section, a `---` rule starts a continuation slide
carrying the same heading marked `cont.` — this is the lever for pacing a long section.

Content that still overflows scrolls within the slide rather than being clipped, and the
renderer shrinks type automatically on dense slides (`data-dense` 1 or 2). That keeps
prose-heavy documents usable, but a slide at density 2 is a wall of text. If a deck is
mostly density 2, the source is a document being projected rather than a deck — either
add `---` breaks or accept it as a scrolling handout.

Keyboard: `→` `space` `n` `j` next · `←` `p` `k` previous · `Home` / `End` · `f` fullscreen.
A `#section-id` fragment in the URL opens directly at that slide.

## Theming

`assets/theme.css` holds the base: typography, tables, callouts, print rules, and a set of
CSS custom properties (`--paper`, `--ink`, `--accent`, `--serif`, …) with automatic
light/dark via `prefers-color-scheme`. `assets/deck.css` layers slide geometry on top and
reuses the same properties, so retheming both modes means editing the properties only.

For a one-off house style, copy the stylesheet, change the `:root` block, and pass
`--theme /path/to/custom.css`. Deck mode always appends `deck.css` on top.

The `--eyebrow` flag sets the small-caps line above the title — use it for the owning
team, programme or classification.

## Sharing the output

Output is a single file with no external requests: no CDN, no fonts, no analytics. It
opens offline, survives being attached to mail, and can be dropped in Teams or a wiki.

For PDF, open and print — both modes have print stylesheets. Doc mode drops the sidebar
and prints as a document; deck mode prints one slide per page.

Because font families are stacks resolved on the reader's machine, expect minor metric
differences across platforms. Nothing reflows structurally.

## Troubleshooting

**Sections missing from the TOC, or the last preamble row absent.** Almost always pandoc's
line wrapping. The script passes `--wrap=none` for exactly this reason: without it pandoc
wraps output at 72 columns and splits long opening tags (`<h2\nid="...">`) and inline
`<strong>` labels across lines, so the regexes miss them silently. If editing the script,
never remove that flag, and match tags with `<h2\s+id=` rather than `<h2 id=`.

**A section did not become a slide.** Deck mode splits on `##` only. `#` is the title and
`###` stays inside its parent slide.

**Preamble rendered as an ordinary paragraph.** The fields must form one paragraph with no
blank lines between them, and the first line must start with `**Label:**`.

**Table too wide.** Tables scroll horizontally inside their container by design. Very wide
tables read better in doc mode than deck mode.

**`pandoc not found`.** Install pandoc; it is the only external dependency.
