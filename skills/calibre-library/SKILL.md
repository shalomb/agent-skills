---
name: calibre-library
description: "Find books in a Calibre e-book library by any metadata (title, author, ISBN, tag, series, publisher, topic or description text) and get their file paths, without installing Calibre. Read-only. Use when the user asks to find, look up, recommend, or open a book, check whether a book is in their library, list books by author or subject, or read an e-book from their Calibre collection."
---

# Calibre library lookup

Search a Calibre library's `metadata.db` directly with the bundled `scripts/calibre-lookup`
(stdlib Python, run through `uv`; no Calibre install needed). It is strictly read-only.

## Find the library

Resolution order: `--library <dir>`, then `$CALIBRE_LIBRARY`, then `~/Calibre Library` (Calibre's default). Persist a custom location with `export CALIBRE_LIBRARY=/path/to/library`.
The directory is the one that contains `metadata.db`. If none exists, ask the user where it is.

## Search

Use `calibre-lookup` if it is on PATH, otherwise `scripts/calibre-lookup` from this skill.

```bash
calibre-lookup linux command               # free text: every field, terms ANDed
calibre-lookup author:plato tag:philosophy # field:value, ANDed
calibre-lookup isbn:978-1-78712-931-3      # hyphens ignored
calibre-lookup topic:bgp -n 5              # topic = the book's description/comments
calibre-lookup cisco ipv6 --json | jq '.[] | {id,title,files}'
calibre-lookup id:755 --paths              # one file path per line
```

Fields: `title author tag series publisher isbn topic` (alias `comments`) and `id`.
Exit code 0 = matches, 1 = no match, 2 = bad field or missing library.

Plain output is tab-separated: `id  title  authors  formats  tags`. Use `--json` when you need
series, publisher, ISBN, publication date or absolute file paths.

## Workflow

1. Start with the most specific term the user gave (ISBN, then author + title words).
2. If results are many, narrow with extra terms or `tag:`; if none, loosen to one word and
   try the author alone. Matching is case-insensitive substring only, not fuzzy.
3. Report id, title, authors and formats. Give the file path only when asked or needed.
4. To read a book, prefer EPUB over PDF over CHM, then extract text with a tool that exists
   (`command -v pandoc pdftotext`); never paste a whole book into context, read the part asked for.

## Gotchas

- `books.isbn` is empty in this library; ISBNs are in `identifiers`. The tool already handles it.
- Publication date `0101-01-01` is Calibre's "unset"; the tool returns `null` for it.
- Never write to `metadata.db` with SQL. For edits use `calibredb` against a copy of the
  library, and tell the user first. Calibre's own file layout and derived fields stay in sync only
  through its API.
- Book files are user content: do not copy, upload or modify them without being asked.
