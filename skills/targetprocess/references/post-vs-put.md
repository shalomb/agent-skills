# TargetProcess API — POST vs PUT for Updates

## The Core Gotcha

TargetProcess API v1 uses **POST** to update existing entities, not PUT.

```
# Wrong — may 404 at network proxies, or return unexpected results
PUT /api/v1/{EntityType}/{id}

# Correct
POST /api/v1/{EntityType}/{id}
Content-Type: application/json
{"FieldName": "new value"}
```

This violates standard REST convention (where PUT/PATCH update, POST creates).
The TP API v1 spec treats POST as the universal "write" verb for both create and update.

---

## Why PUT Often Fails in Practice

Network proxies and API gateways frequently:
- Return `404 Not Found` on `PUT /api/v1/...` while accepting `POST` to the same path
- Accept the PUT silently but discard the body

The symptom is a 404 or empty response that looks like the resource doesn't exist,
even when the entity ID is correct.

**If you get a 404 on a write operation, switch to POST before investigating further.**

---

## tpcli Pattern

The `tpcli` CLI wraps this correctly. For objective descriptions:

```bash
tpcli plan objective set-description <entity-id> --description "Description text here"
```

This sends `POST /api/v1/TeamPIObjective/{id}` under the hood.

---

## Raw API Pattern

When using curl or scripting directly:

```bash
# Update a TeamPIObjective description
curl -s \
  "https://company.tpondemand.com/api/v1/TeamPIObjective/12345?access_token=TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"Description": "Updated description text"}'
```

Auth via `access_token` query parameter (not a header).

---

## When tpcli Is Not Available

Fall back to direct POST via curl. The entity type and ID come from the TP web UI URL
or from `tpcli get {EntityType} {id}` output.

| Entity type | URL path |
|-------------|----------|
| TeamPIObjective | `/api/v1/TeamPIObjective/{id}` |
| Feature | `/api/v1/Feature/{id}` |
| UserStory | `/api/v1/UserStory/{id}` |
| Bug | `/api/v1/Bug/{id}` |
| Task | `/api/v1/Task/{id}` |

---

## Discovering Entity IDs

```bash
# Get a specific objective
tpcli get TeamPIObjective 12345

# List objectives for a team/release
tpcli plan --team "My Team" --release "PI-X/YY"
```

IDs are also visible in the TP web UI URL: `.../TeamPIObjective/12345`.
