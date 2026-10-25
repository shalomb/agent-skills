# Link card format

A link card is an Obsidian callout of Dataview inline fields, placed on the lines directly
below a link line. It is human-readable (folded to one line in Obsidian), queryable with
Dataview, and parseable with one regex per line.

```markdown
[Title](https://example.org/post)
> [!link-card]- Title shown when folded
> status:: ok
> title:: Title
> description:: One line, at most 400 characters.
> site:: Example
> type:: article
> image:: https://example.org/og.png
> canonical:: https://example.org/post/
> checked:: 2026-10-25
> priority:: high          <- written by a later stage, not by triage
```

Inside a list item the whole card is indented to the content column:

```markdown
- [ ] [Title](https://example.org/post)
  > [!link-card]- Title
  > status:: ok
```

## Grammar

- Header: `> [!link-card]- <text>`; the card is that line plus all directly following lines that
  start with `>` (after indentation).
- Field: `> <key>:: <value>`; key matches `[A-Za-z][\w-]*`, value is one line (newlines are
  collapsed to spaces). A card ends at the first line that does not start with `>`.
- Parse with: `^>\s*(?P<key>[A-Za-z][\w-]*)::\s*(?P<val>.*)$`

## Fact fields (owned by triage)

| field | source | present when |
|---|---|---|
| `status` | derived | always: `ok`, `no-og`, `dead`, `blocked`, `error` |
| `title` | og:title | `ok` |
| `description` | og:description (max 400 chars, ends with `…` if cut) | when the site gives one |
| `site` | og:site_name | when given |
| `type` | og:type | when given |
| `image` | og:image | when given |
| `canonical` | og:url | when given |
| `http` | status code | `dead`, `blocked`, and HTTP errors |
| `error` | message (max 160 chars) | `error` without an HTTP code |
| `checked` | run date, `YYYY-MM-DD` | always |

`dead` is HTTP 404 or 410; `blocked` is 401, 403 or 429; `ok` needs a title, otherwise a
reachable page is `no-og`.

## Ownership

`annotate` rewrites only the fact fields, in the fixed order above. Any other field is kept as is
and written after them. Classification stages should add fields such as `priority`, `ingest`
(`full`, `bookmark`, `skip`), `tags` and `place`, and may set them freely.

## Idempotence

A link whose card has status `ok`, `no-og`, `dead` or `blocked` is skipped on later runs;
`error` cards are retried; `--refresh` re-fetches everything. A run that has nothing to do does
not touch the file.
