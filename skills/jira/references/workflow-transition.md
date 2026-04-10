# Jira Workflow Transitions — Gotchas and Patterns

## The Silent Rollback Problem

Jira projects can have automation rules that validate required fields on transition.
When a field is missing:

1. The CLI (`jira issue move`) reports **success** and exits 1
2. The automation rolls back the transition within seconds
3. The issue returns to its original state
4. A rejection email is sent to the user

**You cannot trust the CLI exit code or success message.** Always verify via REST after transitioning.

```bash
# Transition
jira issue move PROJ-123 "Backlog"

# Verify — do not trust the CLI output above
curl -s --netrc "https://your-instance.atlassian.net/rest/api/3/issue/PROJ-123?fields=status" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['fields']['status']['name'])"
```

---

## Finding Required Fields

Before transitioning, identify which fields the target state requires.

### Option 1 — Read from a working issue

Find an issue already in the target state and inspect its fields:

```bash
# Get all non-null fields from a working issue
curl -s --netrc "https://your-instance.atlassian.net/rest/api/3/issue/PROJ-123" \
  | python3 -c "
import json,sys
f = json.load(sys.stdin)['fields']
for k,v in sorted(f.items()):
    if v and v != [] and v != {}:
        print(k, ':', str(v)[:80])
"
```

**Always prefer reading values from a working issue over guessing.** Field IDs, allowed
values, and object shapes vary by project and Jira instance.

### Option 2 — Inspect the rejection email

The Jira automation email lists exactly which fields are missing by name.
Map the human-readable name to the field ID using:

```bash
curl -s --netrc "https://your-instance.atlassian.net/rest/api/3/field" \
  | python3 -c "
import json,sys
for f in json.load(sys.stdin):
    if 'acceptance' in f['name'].lower() or 'team' in f['name'].lower():
        print(f['id'], f['name'], f.get('schema',{}).get('type',''))
"
```

---

## Setting Fields via REST API

The Jira CLI cannot set most custom fields. Use REST PUT:

```bash
curl -s --netrc -X PUT \
  "https://your-instance.atlassian.net/rest/api/3/issue/PROJ-123" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"duedate": "2026-06-30"}}'
# Empty response = success; any JSON = error
```

### Known Field Format Gotchas

| Field type | Wrong | Right |
|-----------|-------|-------|
| Team (Atlassian Teams) | `{"customfield_XXXXX": {"id": "uuid"}}` | `{"customfield_XXXXX": "uuid"}` — plain string |
| Parent issue | `{"update": {"parent": [{"set": {"id": "NNN"}}]}}` | `{"fields": {"parent": {"id": "NNN"}}}` |
| Acceptance Criteria (ADF) | `{"type":"doc","content":[{"type":"paragraph",...}]}` | Must be `bulletList` not `paragraph` — validators check structure |
| Component | `{"components": "PI-1/26"}` | `{"components": [{"id": "NNNNN"}]}` — array of id objects |
| Assignee | `{"assignee": "display name"}` | `{"assignee": {"accountId": "..."}}` — accountId only |

### ADF bulletList (required for Acceptance Criteria validators)

```python
def ac_bulletlist(items: list[str]) -> dict:
    return {
        "type": "doc", "version": 1,
        "content": [{"type": "bulletList", "content": [
            {"type": "listItem", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": item}]}
            ]} for item in items
        ]}]
    }
```

---

## Bulk Field Update + Transition Pattern

When setting the same fields on multiple issues before transition:

```python
import subprocess, json

JIRA_BASE = "https://your-instance.atlassian.net"

def put_fields(key: str, fields: dict) -> bool:
    result = subprocess.run(
        ["curl", "-s", "--netrc", "-X", "PUT",
         f"{JIRA_BASE}/rest/api/3/issue/{key}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"fields": fields})],
        capture_output=True, text=True
    )
    resp = result.stdout.strip()
    return not resp or resp == "null"

def transition(key: str, state: str) -> None:
    subprocess.run(["jira", "issue", "move", key, state], capture_output=True)

def verify(keys: list[str], fields: list[str]) -> None:
    payload = {"jql": f"key in ({','.join(keys)})", "fields": fields}
    result = subprocess.run(
        ["curl", "-s", "--netrc", "-X", "POST",
         f"{JIRA_BASE}/rest/api/3/search/jql",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True
    )
    for i in json.loads(result.stdout).get("issues", []):
        f = i["fields"]
        print(i["key"], f["status"]["name"])

# Usage
for key in ["PROJ-1", "PROJ-2", "PROJ-3"]:
    ok = put_fields(key, {
        "duedate": "2026-06-30",
        "assignee": {"accountId": "..."},
        # ... other required fields
    })
    if ok:
        transition(key, "Backlog")

verify(["PROJ-1", "PROJ-2", "PROJ-3"], ["status", "assignee", "duedate"])
```

---

## search/jql API Version Note

Jira Cloud has migrated to a new search endpoint. Use POST:

```bash
# Old (removed) — returns 410
GET /rest/api/3/search?jql=...

# Current — use this
POST /rest/api/3/search/jql
Content-Type: application/json
{"jql": "project = PROJ AND ...", "fields": ["summary", "status"]}
```
