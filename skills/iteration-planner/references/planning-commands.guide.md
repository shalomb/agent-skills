# Guide: Iteration Planning Commands

This document provides the technical command and query reference for the `iteration-planner` skill.

---

## 1. Roadmap Discovery (GraphQL)
Used to find empty or upcoming iterations that `gh project item-list` cannot see.

```bash
gh api graphql -f query='
  query($owner:String!, $number:Int!) {
    organization(login: $owner) {
      projectV2(number: $number) {
        field(name: "Iteration") {
          ... on ProjectV2IterationField {
            id
            configuration {
              startDate
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

## 2. Sprint Stocktake (WIP Extraction)
Used to fetch non-completed items from a specific iteration.

> ⚠️ Always use `--limit 200`. The default page size silently truncates results on active projects, causing items to appear missing from the stocktake.

```bash
gh project item-list <number> --owner <org> --limit 200 --format json | \
  jq '.items[] | select(.iteration.title == "Iteration X" and .status != "Done") | \
  {id, title, status, priority, size, issue_number: .content.number, repo: .content.repository}'
```

---

## 3. Bulk Updates (Item Edit via GraphQL)
Used to execute moves confirmed in the planning sheet. Use the GraphQL mutation directly — `gh project item-edit --field Iteration` does not accept iteration IDs reliably.

```bash
# Move item to a specific iteration (iterationId from post-discovery fetch)
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "<project_node_id>",
      itemId: "<item_node_id>",
      fieldId: "<iteration_field_id>",
      value: { iterationId: "<iteration_id>" }
    }) {
      projectV2Item { id }
    }
  }
'

# Move to Backlog (status update)
gh project item-edit --id <item_id> --project-id <project_id> --field-id <status_field_id> --single-select-option-id <backlog_option_id>
```

> ⚠️ After any `updateProjectV2Field` mutation, all iteration IDs are regenerated. Re-fetch IDs before running bulk item assignments.

---

## 4. Metadata Hygiene (Field Discovery)
Used to list valid options for Status, Priority, and Size.

```bash
gh project field-list <number> --owner <org> --format json
```
