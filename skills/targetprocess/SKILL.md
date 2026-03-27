---
name: targetprocess
description: Query and manage TargetProcess/Apptio entities (user stories, bugs, tasks, features) via tpcli. Supports discovery, filtering, pagination, entity operations, and complex team-based PI planning scenarios. Use when working with TargetProcess work items, managing project entities, or querying issue trackers for team health and status.
---

# TargetProcess (tpcli) Skill

Query and manage TargetProcess/Apptio work items and planning data via `tpcli`.

## Prerequisites

- `tpcli` installed and on `$PATH`
- API authentication configured (token + URL via env, config, or flags)
- Read: `references/targetprocess-quick-ref.md` for command patterns

## Team Scenarios (PI Planning & Health)

Advanced workflows for Lead/Principal Engineers and Agile teams:
- **ART Dashboards**: See ART-wide PI health.
- **Team Deep Dives**: Drill into team capacity and risks.
- **Objective Analysis**: Map dependencies and Jira correlation.
- **Release Reports**: Track PI status and inter-team blockers.

→ Read `references/team-scenarios.md` for detailed command patterns.

## Bundled Resources

### Scripts
- `scripts/describe-team.sh`: Generates a comprehensive team profile (Information, Features, Stories, Bugs, Tasks, and Workload Summary).

Usage:
```bash
TP_TOKEN=xxx TP_URL=yyy ./scripts/describe-team.sh [TEAM_ID]
```

## Quick Commands

### Discover Available Entities

```bash
tpcli discover
```

Lists all entity types and structure in your TargetProcess instance.

### List Entities

```bash
tpcli list UserStories
tpcli list Bugs --take 50
tpcli list Tasks --fields Id,Name,EntityState
```

### Filter Results

```bash
tpcli list UserStories --where "EntityState.Name eq 'Open'"
tpcli list Bugs --where "Project.Id eq 1234"
tpcli list Features --where "Name like '%dashboard%'"
```

### Pagination

```bash
tpcli list UserStories --take 10 --skip 0
tpcli list Tasks --take 50 --skip 50
```

### Get Single Entity

```bash
tpcli get UserStory 12345
tpcli get Bug 67890
```

### Plan Discovery

```bash
tpcli plan --team "MyTeam"
tpcli plan --art "MyART" --release "Release 2024.1"
tpcli plan discover
```

## Configuration

Set API credentials via environment variables or config file:

```bash
export TP_TOKEN="your-api-token"
export TP_URL="https://company.tpondemand.com"
```

Or create `~/.tpcli.yaml`:

```yaml
token: your-api-token
url: https://company.tpondemand.com
```

## Common Queries

| Task | Command |
|------|---------|
| List all open stories | `tpcli list UserStories --where "EntityState.Name eq 'Open'"` |
| Find items in project | `tpcli list UserStories --where "Project.Id eq 1234"` |
| Search by name | `tpcli list Features --where "Name like '%search%'"` |
| Specific fields only | `tpcli list Tasks --fields Id,Name,Priority` |
| Limit results | `tpcli list Bugs --take 10` |

## When to Use This Skill

- Query planning hierarchies (ARTs, teams, releases)
- List and filter work items (stories, bugs, tasks, features)
- Search TargetProcess by name, status, project, etc.
- Discover available entity types and structure
- Integrate TargetProcess data into scripts/reports

## When to Read References

For detailed syntax, patterns, and advanced filtering:
→ Read `references/targetprocess-quick-ref.md`

For API details and entity structure:
→ Read tpcli documentation: `tpcli docs` or the installed package documentation
