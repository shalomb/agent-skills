# Jira Cloud ADF — Description Rendering

## The Problem with `jira` CLI for Descriptions

Jira Cloud stores descriptions as **Atlassian Document Format (ADF)** JSON, not
wiki markup. The `jira` CLI (v1.7) accepts wiki markup input but converts it to
ADF incorrectly for hyperlinks:

- `[text|url]` → two separate ADF nodes: label as *italic* text + bare URL as a
  separate hyperlink node
- In the browser this renders as: `text` (italic, no link) followed by the raw URL

**Effect**: any description written via `jira issue create -b` or `jira issue edit -b`
with links will render broken in the Jira UI.

## Correct Approach: REST API v3 with ADF JSON

For descriptions containing hyperlinks (or any rich formatting you need to be
sure about), bypass the CLI and PUT ADF JSON directly:

```bash
# Auth: use ~/.netrc credentials (email + Atlassian API token)
# or inline: -u "user@example.com:ATATT3x..."

JIRA_TOKEN=$(awk '/machine onetakeda.atlassian.net/{getline; print $2}' ~/.netrc)

curl -s -X PUT \
  "https://onetakeda.atlassian.net/rest/api/3/issue/PROJ-123" \
  -u "user@example.com:${JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @/tmp/issue_body.json
# → 204 on success
```

## ADF JSON Structure

```json
{
  "fields": {
    "description": {
      "version": 1,
      "type": "doc",
      "content": [ ...nodes... ]
    }
  }
}
```

## Python ADF Builder

Use these helper functions to construct ADF programmatically:

```python
import json

def text(t):      return {"type": "text", "text": t}
def strong(t):    return {"type": "text", "text": t, "marks": [{"type": "strong"}]}
def em(t):        return {"type": "text", "text": t, "marks": [{"type": "em"}]}
def link(label, url):
    return {"type": "text", "text": label,
            "marks": [{"type": "link", "attrs": {"href": url}}]}

def para(*nodes):
    return {"type": "paragraph", "content": list(nodes)}

def heading(level, t):
    return {"type": "heading", "attrs": {"level": level}, "content": [text(t)]}

def rule():
    return {"type": "rule"}

def bullet(*items):
    return {"type": "bulletList", "content": [
        {"type": "listItem", "content": [para(text(i) if isinstance(i, str) else i)]}
        for i in items
    ]}

def table(header_row, *data_rows):
    def th(c): return {"type": "tableHeader", "attrs": {}, "content": [para(strong(c) if isinstance(c, str) else c)]}
    def td(c): return {"type": "tableCell",   "attrs": {}, "content": [para(text(c)   if isinstance(c, str) else c)]}
    def row(cells, is_header=False):
        fn = th if is_header else td
        return {"type": "tableRow", "content": [fn(c) for c in cells]}
    return {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
        "content": [row(header_row, True)] + [row(r) for r in data_rows]
    }

# Build the document
doc = {
    "fields": {
        "description": {
            "version": 1, "type": "doc",
            "content": [
                heading(2, "Problem Statement"),
                para(text("Description with a "), link("GitHub issue", "https://github.com/org/repo/issues/1"), text(".")),
                rule(),
                heading(2, "Acceptance Criteria"),
                bullet("Criterion one", "Criterion two"),
                heading(2, "Dependencies"),
                table(
                    ["Type", "Ref", "Status", "Notes"],
                    ["depends-on", "DAD-3439", "open", "PrivateLink must be resolved"],
                ),
            ]
        }
    }
}

with open("/tmp/issue_body.json", "w") as f:
    json.dump(doc, f, indent=2)
```

## Valid ADF Node Types (Jira Cloud)

These are confirmed to work. Others (e.g. `blockquote`, `panel`) return
`INVALID_INPUT` on this Jira instance:

| Node type | Notes |
|-----------|-------|
| `paragraph` | Inline text container |
| `heading` | `attrs.level` 1–6 |
| `bulletList` + `listItem` | Bullet list |
| `orderedList` + `listItem` | Numbered list |
| `table` + `tableRow` + `tableHeader` + `tableCell` | Tables |
| `rule` | Horizontal divider |
| `text` | Leaf node; accepts `marks` |

Valid `marks` on `text` nodes: `strong`, `em`, `link` (with `attrs.href`),
`code`, `strike`.

**Do NOT use**: `blockquote`, `panel` — both return `INVALID_INPUT` on this instance.

## When to Use CLI vs REST API

| Case | Use |
|------|-----|
| Description has no links | `jira` CLI is fine |
| Description has hyperlinks | REST API v3 + ADF JSON |
| Description has tables | Either works; CLI table syntax is fiddly — ADF is safer |
| Viewing/transitioning/commenting | `jira` CLI always fine |

## Auth Note

The `jira` CLI token and the REST API token are the same Atlassian API token.
Read it from `~/.netrc`:

```bash
JIRA_TOKEN=$(awk '/machine onetakeda.atlassian.net/{getline; print $2}' ~/.netrc)
```

Or from the jira CLI config:
```bash
JIRA_TOKEN=$(grep "token:" ~/.config/jira/.config.yml | awk '{print $2}')
```
