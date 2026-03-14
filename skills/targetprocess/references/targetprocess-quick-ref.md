# TargetProcess (tpcli) — Quick Reference

Fast lookup for `tpcli` command patterns and common workflows.

## Command Structure

```
tpcli [global-flags] <command> [command-flags] [args]
```

### Global Flags

```bash
--token string      # API token (env: TP_TOKEN)
--url string        # Base URL (env: TP_URL)
--config string     # Config file path
--verbose, -v       # Verbose output
```

## Core Commands

### discover — Explore TargetProcess Structure

```bash
tpcli discover
tpcli discover --verbose
```

**Output**: Available entity types and their relationships.

**Use when**: You need to understand what data is available.

---

### list — Query Entities

```bash
tpcli list <entity-type> [flags]
```

**Flags**:
- `--where EXPRESSION` — Filter expression (OData-style)
- `--fields FIELD1,FIELD2` — Select specific fields only
- `--take N` — Limit results (default: 25)
- `--skip N` — Offset for pagination (default: 0)

**Examples**:

```bash
# All user stories
tpcli list UserStories

# Open stories only
tpcli list UserStories --where "EntityState.Name eq 'Open'"

# Specific project
tpcli list Bugs --where "Project.Id eq 1234"

# Search by name (partial match)
tpcli list Features --where "Name like '%dashboard%'"

# Select specific fields
tpcli list Tasks --fields Id,Name,Priority,Owner

# Paginate results
tpcli list UserStories --take 10 --skip 20
```

**Where Expression Syntax** (OData v4):

| Operator | Example |
|----------|---------|
| `eq` | `EntityState.Name eq 'Open'` |
| `ne` | `Status ne 'Closed'` |
| `like` | `Name like '%dashboard%'` |
| `and` | `Status eq 'Open' and Priority gt 1` |
| `or` | `Project.Id eq 1 or Project.Id eq 2` |
| `startswith` | `Name startswith 'Feature'` |
| `endswith` | `Name endswith 'API'` |

---

### get — Fetch Single Entity

```bash
tpcli get <entity-type> <id>
```

**Examples**:

```bash
tpcli get UserStory 12345
tpcli get Bug 67890
tpcli get Feature 111
tpcli get Task 999
```

**Output**: Full entity details in JSON.

---

### plan — Discover PI Planning Structure

```bash
tpcli plan [command]
```

**Sub-commands**:

```bash
tpcli plan discover              # Show planning hierarchy
tpcli plan --team "TeamName"     # Items for specific team
tpcli plan --art "ARTName"       # Items for specific ART
tpcli plan --release "RelName"   # Items for specific release
```

**Examples**:

```bash
# Discover ARTs, teams, releases
tpcli plan discover

# Get team roadmap
tpcli plan --team "Platform"

# Get ART planning
tpcli plan --art "Enterprise" --release "2024.Q1"

# Combine filters
tpcli plan --team "Backend" --art "Infrastructure"
```

**Output**: Planning hierarchy and work items in JSON.

---

### arts — Analyze ART Structure

```bash
tpcli arts
tpcli arts --verbose
```

**Output**: Available ARTs, their teams, and releases.

---

### ext — Run Extension Scripts

```bash
tpcli ext <script-name> [args]
```

**Available scripts**:

```bash
tpcli ext team-dashboard --team "TeamName"
tpcli ext portfolio-view
tpcli ext velocity-report
```

**Custom scripts**: Add `.tpcli/ext/` directory with custom analysis scripts.

---

## Entity Types Reference

Common TargetProcess entity types for `list` and `get`:

| Entity Type | What It Is | Fields |
|-------------|-----------|--------|
| `UserStories` | User stories | Id, Name, EntityState, Project, Owner, Priority |
| `Bugs` | Defects/bugs | Id, Name, Severity, Priority, Status, Owner |
| `Tasks` | Tasks (work items) | Id, Name, Status, Owner, Parent |
| `Features` | Features | Id, Name, Status, Owner, Project |
| `Releases` | Releases | Id, Name, StartDate, EndDate, Status |
| `Teams` | Teams | Id, Name, Members |
| `Projects` | Projects | Id, Name, Owner |
| `Portfolios` | Portfolio items | Id, Name, Status |

## Configuration

### Environment Variables (Highest Priority)

```bash
export TP_TOKEN="your-api-token"
export TP_URL="https://company.tpondemand.com"
tpcli list UserStories
```

### Config File

**Default locations** (checked in order):
1. File specified with `--config`
2. `~/.config/tpcli/config.yaml` (XDG standard)
3. `~/.tpcli.yaml` (legacy)
4. `./.tpcli.yaml` (local, current directory)

**Format** (`~/.tpcli.yaml`):

```yaml
token: your-api-token
url: https://company.tpondemand.com
verbose: false
```

### Command-Line Flags

```bash
tpcli list UserStories --token "xyz" --url "https://..."
```

**Precedence**: Env > Config > Flags

---

## Common Workflows

### 1. Explore What's Available

```bash
# Step 1: See available data
tpcli discover

# Step 2: Pick an entity type
tpcli list UserStories --take 5

# Step 3: Inspect one item
tpcli get UserStory 12345
```

### 2. Find Open Work

```bash
# All open user stories
tpcli list UserStories --where "EntityState.Name eq 'Open'"

# Open bugs by priority
tpcli list Bugs \
  --where "EntityState.Name eq 'Open' and Priority gt 1" \
  --fields Id,Name,Priority,Owner
```

### 3. Get Team Roadmap

```bash
# Team's planning view
tpcli plan --team "MyTeam"

# With specific ART
tpcli plan --team "MyTeam" --art "MyART"
```

### 4. Search by Name

```bash
# Find items containing "dashboard"
tpcli list UserStories --where "Name like '%dashboard%'"

# Feature names starting with "Auth"
tpcli list Features --where "Name startswith 'Auth'"
```

### 5. Paginate Large Result Sets

```bash
# Get 50 items at a time
tpcli list UserStories --take 50 --skip 0
tpcli list UserStories --take 50 --skip 50
tpcli list UserStories --take 50 --skip 100
```

### 6. Export Specific Data

```bash
# Export IDs and names only
tpcli list UserStories --fields Id,Name > stories.json

# With filtering
tpcli list Bugs \
  --where "Severity eq 'Critical'" \
  --fields Id,Name,Owner > critical-bugs.json
```

---

## Filtering Deep Dives

### Field Navigation (Nested Properties)

Access nested properties with dot notation:

```bash
# Project properties
--where "Project.Name eq 'MyProject'"
--where "Project.Id eq 1234"

# Entity state
--where "EntityState.Name eq 'Open'"
--where "EntityState.Id eq 10"

# Owner/user properties
--where "Owner.FirstName eq 'John'"
--where "Owner.Email like '%@company.com'"
```

### Comparison Operators

```bash
# Numeric
--where "Priority gt 2"        # Greater than
--where "Priority gte 2"       # Greater than or equal
--where "Priority lt 3"        # Less than
--where "Priority lte 3"       # Less than or equal
--where "Priority eq 2"        # Equals
--where "Priority ne 2"        # Not equal

# String
--where "Name like '%foo%'"    # Contains
--where "Name startswith 'x'"  # Starts with
--where "Name endswith 'y'"    # Ends with

# Boolean
--where "IsActive eq true"
--where "IsActive eq false"
```

### Logical Operators

```bash
# AND (both conditions must be true)
--where "Priority gt 1 and Owner.Name eq 'John'"

# OR (either condition can be true)
--where "Status eq 'Open' or Status eq 'In Progress'"

# Grouping (parentheses)
--where "(Priority gt 1 and Owner.Name eq 'John') or Status eq 'Closed'"

# NOT / Negation
--where "Status ne 'Closed'"
```

### Date Filtering

```bash
# Created in 2024
--where "Created ge 2024-01-01 and Created lt 2025-01-01"

# Modified in last 7 days
--where "Modified gt 2024-03-02"  # Adjust date as needed

# Due date is today or in future
--where "DueDate ge 2024-03-09"
```

---

## Output Formats

### JSON Output (Default)

```bash
tpcli list UserStories --take 2
```

**Output**:
```json
[
  {
    "Id": 12345,
    "Name": "As a user...",
    "EntityState": {
      "Id": 10,
      "Name": "Open"
    },
    "Project": {...}
  },
  ...
]
```

### Format with jq (Optional)

```bash
# Pretty-print (already done by tpcli)
tpcli list UserStories | jq .

# Extract specific fields
tpcli list UserStories | jq '.[].Name'

# Count results
tpcli list UserStories | jq 'length'

# Filter by condition
tpcli list UserStories | jq '.[] | select(.Priority > 1)'
```

---

## Troubleshooting

### Authentication Error

```
Error: API token is required
```

**Fix**: Set `TP_TOKEN` env var, `--token` flag, or config file.

```bash
export TP_TOKEN="your-token"
tpcli list UserStories
```

### Base URL Error

```
Error: base URL is required
```

**Fix**: Set `TP_URL` env var, `--url` flag, or config file.

```bash
export TP_URL="https://company.tpondemand.com"
tpcli list UserStories
```

### Invalid Filter Expression

```
Error: invalid where clause
```

**Fix**: Check filter syntax matches OData v4 spec.

```bash
# Wrong
--where "Name = 'foo'"     # ← Use 'eq' not '='

# Right
--where "Name eq 'foo'"
```

### No Results Returned

```bash
# Check if entity type exists
tpcli discover

# Verify filter expression
tpcli list UserStories --where "EntityState.Name eq 'Open'" --verbose

# Try without filter
tpcli list UserStories --take 1
```

### Verbose Mode

```bash
# Enable detailed output
tpcli list UserStories --verbose

# Check config being used
tpcli discover --verbose
```

---

## Performance Tips

1. **Use `--fields`** to limit data retrieved
   ```bash
   tpcli list UserStories --fields Id,Name --take 100
   ```

2. **Use `--where`** to filter server-side (not client-side)
   ```bash
   tpcli list Bugs --where "Severity eq 'Critical'"
   ```

3. **Adjust `--take`** for balance between speed and data
   ```bash
   --take 10   # Faster, less data
   --take 100  # More data, slower
   ```

4. **Use `--skip`** for pagination, not to fetch all then filter
   ```bash
   # Good: Paginate
   tpcli list UserStories --take 25 --skip 0
   tpcli list UserStories --take 25 --skip 25
   
   # Bad: Fetch all
   tpcli list UserStories --take 100000
   ```

---

## Related Documentation

- Full docs: `~/shalomb/tpcli/docs/`
- API v1 reference: `~/shalomb/tpcli/docs/reference/api-v1-reference.md`
- Entity structure: `~/shalomb/tpcli/docs/reference/entity-types.md`
- How-to guides: `~/shalomb/tpcli/docs/how-to/`
