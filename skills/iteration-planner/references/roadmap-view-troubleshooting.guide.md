# Guide: Troubleshooting ProjectV2 Roadmap Views ("Epics" Grouping)

Many GitHub Projects set up a `ROADMAP_LAYOUT` view (commonly named "Epics") to surface
parent issues with their child work grouped underneath. This guide covers what actually
gates an item's visibility in such a view — confirmed empirically, not just from docs.

---

## ⚠️ Confirmed Root Cause: Missing Child (Sub-)Issues

**An issue with zero sub-issues does not reliably render in a Roadmap/"Epics" view**,
even when every other field looks correct:

- It is a project item (confirmed via `content.projectItems`)
- `isArchived: false`
- Not filtered out by the view's saved `filter` string (which may be `""`/empty)
- Has no `Parent issue` set (i.e., it is itself top-level)
- Has a `Status`, `Title`, etc. populated

**Fix**: create actual GitHub sub-issues (not just markdown checkboxes or "See #123" text
references) and link them via the `addSubIssue` mutation. Once `subIssuesSummary.total > 0`,
the item appears in the Roadmap "Epics" view.

```bash
# 1. Create the child issue
gh issue create --repo <owner>/<repo> --title "S1 — ..." --body "Part of #<parent>..."

# 2. Get node IDs for parent and child
gh api graphql -f query='
  query($n:Int!) {
    repository(owner:"<owner>", name:"<repo>") {
      issue(number:$n) { id number title }
    }
  }
' -F n=<number> --jq '.data.repository.issue.id'

# 3. Link as a real sub-issue (not a text reference)
gh api graphql -f query='
  mutation($parent:ID!, $child:ID!) {
    addSubIssue(input: { issueId: $parent, subIssueId: $child }) {
      issue { number }
      subIssue { number }
    }
  }
' -f parent="<parent_node_id>" -f child="<child_node_id>"

# 4. Verify
gh api graphql -f query='
  query($n:Int!) {
    repository(owner:"<owner>", name:"<repo>") {
      issue(number:$n) { subIssuesSummary { total completed } }
    }
  }
' -F n=<parent_number>
```

**Note**: `subIssuesSummary.total` can lag by a few seconds after `addSubIssue` — re-query
after a short pause if it still reads 0 immediately after linking.

---

## Ruled Out — Do NOT Waste Time Re-checking These

During live troubleshooting the following were tested and **confirmed NOT to gate
visibility** in a Roadmap "Epics" view:

| Hypothesis | Verdict | Evidence |
|---|---|---|
| `issueType` field (Epic/Feature/Task) | ❌ Not the cause | All items — visible and hidden — had `issueType: NONE` |
| `Parent issue` set (top-level only) | ❌ Not the cause | Confirmed-visible items included ones **with** a parent set (nested children rendering fine) |
| `Start date` / `Target date` populated | ❌ Not the cause | Several confirmed-visible epics had no dates at all — Roadmap views bucket undated items rather than hiding them |
| View's saved `filter` string | ❌ Not the cause | Was `""` (empty) at the API level in the confirmed case |
| Item not added to project | ✅ Real, but separate issue | Always check `issue.projectItems` first — an issue can look "fine" on paper but never have been added to the board at all |

If an issue still doesn't appear after confirming project membership AND adding child
issues, the remaining suspects are outside API visibility and require the user to check
the browser directly:
- A **local, unsaved filter** typed into the view's search box (check the URL for
  `?filterQuery=` when on that view — this persists in the URL/session, not the saved
  view definition returned by GraphQL).
- The Roadmap's date-range **zoom** level (e.g. "This quarter") — usually buckets undated
  items visibly, but worth ruling out via a hard browser refresh / incognito window first.

---

## Best Practice: Set Project, Start Date, and Target Date on Epics Anyway

Even though `Start date` / `Target date` were confirmed **not** to gate Roadmap view
rendering, they should still be set correctly on every epic-level issue:

1. **Correct Project**: confirm the issue is added to the intended `ProjectV2` (number),
   not left dangling in a personal/default project. Check with:
   ```bash
   gh api graphql -f query='
     query($n:Int!) {
       repository(owner:"<owner>", name:"<repo>") {
         issue(number:$n) { projectItems(first:10) { nodes { project { number title } } } }
       }
     }
   ' -F n=<number>
   ```
   An empty `projectItems.nodes` means the issue was never added — add it with
   `addProjectV2ItemById` before doing anything else.

2. **Start date / Target date**: populate these on every epic so the Roadmap view's
   timeline bars render meaningfully (rather than falling into an "undated" bucket).
   This is a data-quality / planning-accuracy concern, independent of the sub-issue
   rendering bug above — do both.

```bash
gh api graphql -f query='
  mutation($project:ID!, $item:ID!, $field:ID!, $date:Date!) {
    updateProjectV2ItemFieldValue(input: {
      projectId: $project, itemId: $item, fieldId: $field,
      value: { date: $date }
    }) { projectV2Item { id } }
  }
' -f project="<project_node_id>" -f item="<item_id>" -f field="<start_date_field_id>" -f date="2026-07-08"
```

---

## Summary Checklist for "Epic doesn't show in Roadmap view"

1. Confirm the issue is actually a project item (`projectItems` non-empty).
2. Confirm it has **at least one real sub-issue** (`addSubIssue`, not a text reference).
3. Set `Start date` and `Target date` fields regardless — good practice, not a rendering fix.
4. If still missing: ask the user to check the view's URL for a stray `filterQuery=` param
   and to hard-refresh / try incognito before assuming a data problem.
