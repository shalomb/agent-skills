# Guide: Managing GitHub Project Iterations (CRUD)

This document provides technical instructions for creating, updating, and deleting iterations within a `ProjectV2` iteration field using the GitHub GraphQL API.

## ⚠️ Critical Rules

### 1. Full State Replacement
The `updateProjectV2Field` mutation for iterations is a **Complete State Replacement**. You cannot "add" a single iteration. You must provide the complete list of iterations you wish to exist. **Any iteration omitted from the mutation will be deleted along with its item assignments.**

### 2. Always Include Past Iterations — or `@current` Views Break
Every mutation **must include all past iterations** (even completed ones) in the `iterations[]` payload alongside future/active ones. GitHub automatically promotes past-dated entries to `completedIterations` based on date — but if they are omitted entirely they are **permanently deleted from the configuration**.

When `completedIterations` is empty, GitHub cannot resolve `iteration:@current` in project views — any view using that filter will show **no items** until the config is restored.

> **Root cause discovered**: Running `updateProjectV2Field` with only active iterations silently wipes `completedIterations`. The `iteration:@current` filter requires at least one completed iteration as a cadence anchor.

### 3. Every Mutation Regenerates Iteration IDs
Every call to `updateProjectV2Field` regenerates **all** iteration IDs (both active and completed), even for iterations whose title/startDate/duration are unchanged. After any mutation you **must** re-fetch iteration IDs and re-assign all affected project items — their previous iteration field values are orphaned.

**Safe mutation sequence:**
1. Fetch current full state (IDs, titles, dates) — including `completedIterations`
2. Run mutation with ALL iterations (past + active + new)
3. Re-fetch to get new IDs
4. Re-assign all items that were in any affected iteration

---

## 1. Discovery (GET Current State)
Before any update, you **MUST** fetch the current iteration list, IDs, and start dates — including `completedIterations`.

> ⚠️ Note: `startDate` does not exist on `ProjectV2IterationFieldConfiguration` as a readable field — omit it from the query response selection or you will get a GraphQL error.

```bash
gh api graphql -f query='
  query($owner:String!, $number:Int!) {
    organization(login: $owner) {
      projectV2(number: $number) {
        field(name: "Iteration") {
          ... on ProjectV2IterationField {
            id
            configuration {
              duration
              iterations { id, title, startDate, duration }
              completedIterations { id, title, startDate, duration }
            }
          }
        }
      }
    }
  }
' -f owner="<org>" -F number=<project_number>
```

---

## 2. Creation (ADD a New Iteration)
To add a new iteration, reconstruct the **full list** from the discovery step — past iterations included — and append your new entry. GitHub will auto-promote past-dated entries to `completedIterations`.

The `startDate` at the top of `iterationConfiguration` is the **cadence origin** (the earliest iteration start date in your history). It is **required as input** but **cannot be read back** in the response.

```bash
gh api graphql -f query='
  mutation {
    updateProjectV2Field(input: {
      fieldId: "FIELD_ID",
      iterationConfiguration: {
        startDate: "CADENCE_ORIGIN_DATE",   # earliest iteration startDate in history
        duration: 14,
        iterations: [
          { title: "Iteration 1", startDate: "2026-01-01", duration: 14 },  # past → becomes completedIteration
          { title: "Iteration 2", startDate: "2026-01-15", duration: 14 },  # past → becomes completedIteration
          { title: "Iteration 3", startDate: "2026-01-29", duration: 14 },  # current
          { title: "Iteration 4 (NEW)", startDate: "2026-02-12", duration: 14 }  # new upcoming
        ]
      }
    }) {
      projectV2Field {
        ... on ProjectV2IterationField {
          configuration {
            iterations { id, title, startDate }
            completedIterations { id, title, startDate }
          }
        }
      }
    }
  }
'
```

**After this mutation**: re-fetch all iteration IDs and re-assign any items that were previously assigned to iterations whose IDs were regenerated.

---

## 3. Deletion (REMOVE an Iteration)
To delete an iteration, execute the mutation above but **exclude** the target iteration from the `iterations` array. Apply the same rule — include all other past iterations to preserve `completedIterations`.

---

## 4. Re-assigning Items After a Mutation
Because every mutation regenerates IDs, use this pattern to bulk re-assign items to the new iteration ID:

```bash
PROJECT="<project_node_id>"
FIELD="<iteration_field_id>"
NEW_ITER_ID="<new_iteration_id>"   # from post-mutation re-fetch

for item_id in PVTI_xxx PVTI_yyy; do
  gh api graphql -f query="
    mutation {
      updateProjectV2ItemFieldValue(input: {
        projectId: \"$PROJECT\",
        itemId: \"$item_id\",
        fieldId: \"$FIELD\",
        value: { iterationId: \"$NEW_ITER_ID\" }
      }) { projectV2Item { id } }
    }
  "
done
```

---

## Troubleshooting & Best Practices
- **Date Accuracy**: Ensure `startDate` for new iterations follows the existing cadence (usually Iteration N End Date + 1).
- **ID vs Definition**: The mutation **does not** accept iteration IDs as input. You must use the full definition (`title`, `startDate`, `duration`) for every entry.
- **`completedIterations` is read-only input**: You cannot pass `completedIterations` in the mutation input — GitHub derives them automatically from past-dated entries in the `iterations[]` list.
- **`@current` views go blank**: If a view using `iteration:@current` shows no items after a mutation, the cause is always missing `completedIterations`. Fix by re-running the mutation with all past iterations included.
- **Permissions**: Requires `write:project` or `project` scope.
- **Cache lag**: After a mutation, `@current` filter resolution in the UI may take several minutes to catch up even when the API data is correct. A hard browser refresh usually resolves it; if not, wait ~5 minutes.
