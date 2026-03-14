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

## 3. Usage Nuances
- **Cross-Repository**: Sub-issues can live in different repositories than the parent. The `repository.nameWithOwner` field helps identify their location.
- **Limits**: The queries above return the first 50 sub-issues. Use pagination (cursors) if an issue has more children.
- **Terminology**:
  - `subIssues`: The list of issues "nested" under the target issue.
  - `trackedIssues`: The list of parent issues that "contain" the target issue.
