# Guide: Navigating Issue Hierarchy (Parent/Child)

Standard GitHub CLI commands (`gh issue`) do not currently support exploring parent/child relationships between issues. This guide provides GraphQL queries to discover these hierarchies.

---

## 1. Discover Sub-Issues (Children)
To find all child issues tracked by a specific parent issue:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $number:Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        id
        title
        subIssues(first: 50) {
          nodes {
            id
            number
            title
            state
            repository {
              nameWithOwner
            }
          }
        }
      }
    }
  }
' -f owner="<org>" -f repo="<repo>" -F number=<issue_number>
```

---

## 2. Discover Tracked Issues (Parents)
To find the parent issue(s) that are tracking a specific issue:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $number:Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        id
        title
        trackedIssues(first: 10) {
          nodes {
            id
            number
            title
            state
            repository {
              nameWithOwner
            }
          }
        }
      }
    }
  }
' -f owner="<org>" -f repo="<repo>" -F number=<issue_number>
```

---

## 3. Reverse Parent Search (Robust Fallback)
If `trackedIssues` is empty but you suspect a parent exists, use this scan to find which issue contains the target in its `subIssues` list:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!) {
    repository(owner: $owner, name: $repo) {
      issues(first: 100, states: [OPEN, CLOSED]) {
        nodes {
          number
          title
          subIssues(first: 50) {
            nodes { id }
          }
        }
      }
    }
  }
' -f owner="<org>" -f repo="<repo>" | jq '.data.repository.issues.nodes[] | select(.subIssues.nodes != null and any(.subIssues.nodes[]; .id == "<target_node_id>")) | {number, title}'
```

---

## 4. Usage Nuances
- **Unidirectional Relationships**: GitHub GraphQL sometimes reports a child in `subIssues` but fails to report the parent in `trackedIssues`. Always use the **Reverse Parent Search** if you need high-confidence parent identification.
- **Node IDs**: You must first fetch the `id` (Global Node ID) of your target issue before performing the jq scan.
