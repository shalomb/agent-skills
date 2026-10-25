---
name: link-triage
description: Annotates links in a markdown note (typically Incoming.md in an Obsidian vault) with Open Graph "link cards" - title, description, site, type, and whether the link is dead or blocked - using the ogspy CLI, without downloading the pages. Idempotent, safe to re-run, and emits parseable cards for later prioritising, tagging and ingest stages. Use when the user adds URLs to an inbox or reading list, asks to triage, classify, prioritise or sanity-check links before a full scrape, wants dead links found, or mentions ogspy or Open Graph.
license: MIT
compatibility: Requires python3 (stdlib only) and the ogspy CLI (go install github.com/vincenzomaritato/ogspy@main). Needs network access to the linked sites.
metadata:
  version: "1.0"
---

# Link triage

Cheap first pass over a pile of links. For each link line it asks the site for its Open Graph
tags (a few hundred bytes, no page download) and writes the answer as a **link card** under the
line. Later stages read the cards to decide what is worth a full capture, where it belongs and
how to tag it. This skill only records facts; it never judges, fetches content, or moves links.

## Run it

```bash
scripts/triage.py annotate Incoming.md            # new links and previously errored ones
scripts/triage.py annotate Incoming.md --dry-run  # list what would be fetched, write nothing
scripts/triage.py annotate Incoming.md --refresh  # re-fetch every link, keep other fields
scripts/triage.py cards Incoming.md --json        # read the cards back as data
scripts/triage.py cards Incoming.md --status dead # only dead links
```

Paths are relative to this skill's directory. Several files may be given; they share one batch.
Exit code 0 means done (dead links are data, not failure); 2 means ogspy is missing or unusable.

## What counts as a link line

A line that, after an optional list marker and checkbox, **starts with** a markdown link
`[text](https://...)` or a bare `https://...` URL. Links in the middle of prose, inside code
fences, front matter or callouts are ignored. The card goes directly under the line, indented to
stay inside a list item.

## Reading a card

```markdown
- [LLMWiki](https://gist.github.com/karpathy/442a...)
  > [!link-card]- llm-wiki
  > status:: ok
  > title:: llm-wiki
  > description:: A pattern for building personal knowledge bases using LLMs.
  > checked:: 2026-10-25
```

| status | meaning | what to do next |
|---|---|---|
| `ok` | Has a title (usually description too) | Enough to classify and prioritise |
| `no-og` | Page loads but has no Open Graph tags | Needs a real fetch to learn anything (about 1 in 5 links) |
| `dead` | HTTP 404 or 410 | Flag as link rot; do not ingest |
| `blocked` | HTTP 401, 403 or 429 | Fetch tools will usually fail too; ask the user to paste the text |
| `error` | Network or other failure | Retried automatically on the next run |

Full field list, ownership rules and parsing notes: [references/CARD.md](references/CARD.md).

## Rules

- **Do not edit fact fields by hand** (`status`, `title`, `description`, `site`, `type`, `image`,
  `canonical`, `http`, `error`, `checked`); a refresh overwrites them. Add your own judgement
  fields (`priority::`, `ingest::`, `tags::`, `place::`) in the same card; they are preserved.
- Do not treat `ok` as "read": a title and a description are a signal, not the content.
- Keep it separate from full capture. Use a fetch tool (for example `web_fetch`) only for links the
  user or a later stage has chosen to ingest.
- Tell the user the status counts after a run, and name any `dead` or `blocked` links.

## Known limits

- Open Graph only: sites without the tags give `no-og` even when the page has a fine `<title>`.
- Sites that block scripted clients (some news sites) give `blocked`.
- ogspy prints per-URL errors on stdout mixed into its JSON; the script handles this, so call
  `triage.py` rather than `ogspy` directly when you need a batch.
