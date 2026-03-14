# Guide: Managing GitHub Project Iterations (CRUD)

This document provides technical instructions for creating, updating, and deleting iterations within a `ProjectV2` iteration field using the GitHub GraphQL API.

## ⚠️ Critical Rule: Full State Replacement
The `updateProjectV2Field` mutation for iterations is a **Complete State Replacement**. You cannot "add" a single iteration. You must provide the complete list of iterations you wish to exist. **Any iteration omitted from the mutation will be deleted along with its item assignments.**

---

## 1. Discovery (GET Current State)
Before any update, you **MUST** fetch the current iteration list, IDs, and start dates.

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
              iterations { title, startDate, duration }
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
To add a new iteration, you must reconstruct the entire list from the discovery step and append your new entry. Provide `title`, `startDate` (YYYY-MM-DD), and `duration` (in days) for every item.

```bash
gh api graphql -f query='
  mutation {
    updateProjectV2Field(input: {
      fieldId: "FIELD_ID",
      iterationConfiguration: {
        startDate: "ORIGINAL_START_DATE",
        duration: 14,
        iterations: [
          { title: "Iteration 1", startDate: "2026-01-01", duration: 14 },
          { title: "Iteration 2", startDate: "2026-01-15", duration: 14 },
          { title: "Iteration 3 (NEW)", startDate: "2026-01-29", duration: 14 }
        ]
      }
    }) {
      projectV2Field {
        ... on ProjectV2IterationField {
          configuration {
            iterations { title, startDate }
          }
        }
      }
    }
  }
'
```

---

## 3. Deletion (REMOVE an Iteration)
To delete an iteration, execute the mutation above but **exclude** the target iteration from the `iterations` array.

---

## Troubleshooting & Best Practices
- **Date Accuracy**: Ensure `startDate` for new iterations follows the existing cadence (usually Iteration N End Date + 1).
- **ID vs Definition**: The mutation **does not** accept iteration IDs. You must use the full definition (`title`, `startDate`, `duration`) for every entry in the list.
- **Permissions**: Requires `write:project` or `project` scope.
