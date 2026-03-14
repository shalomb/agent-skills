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

```bash
gh project item-list <number> --owner <org> --format json | \
  jq '.items[] | select(.iteration.title == "Iteration X" and .status != "Done") | \
  {id, title, status, priority, size, issue_number: .content.number, repo: .content.repository}'
```

---

## 3. Bulk Updates (Item Edit)
Used to execute moves and metadata updates confirmed in the planning sheet.

```bash
# Update Iteration and Size
gh project item-edit --id <item_id> --field Iteration --value "Iteration Y"
gh project item-edit --id <item_id> --field Size --value "M"

# Move to Backlog
gh project item-edit --id <item_id> --field Status --value "Backlog"
```

---

## 4. Metadata Hygiene (Field Discovery)
Used to list valid options for Status, Priority, and Size.

```bash
gh project field-list <number> --owner <org> --format json
```
