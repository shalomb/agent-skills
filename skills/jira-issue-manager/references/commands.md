# Commands Reference

Complete reference for the `jira` CLI.

---

## Viewing Issues

```bash
# View single issue
jira issue view ISSUE-KEY

# View with more comments
jira issue view ISSUE-KEY --comments 5

# Get raw JSON
jira issue view ISSUE-KEY --raw
```

---

## Listing Issues

```bash
# List all issues in project
jira issue list

# List my issues
jira issue list -a$(jira me)

# Filter by status (use quotes for multi-word statuses)
jira issue list -s"In Progress"
jira issue list -s"To Do"
jira issue list -sDone

# Filter by type
jira issue list -tBug
jira issue list -tStory
jira issue list -tTask
jira issue list -tEpic

# Filter by priority
jira issue list -yHigh
jira issue list -yCritical

# Filter by label
jira issue list -lurgent -lbug

# Combine filters
jira issue list -a$(jira me) -s"In Progress" -yHigh

# Search with text
jira issue list "login error"

# Recently accessed
jira issue list --history

# Issues I'm watching
jira issue list -w

# Created/updated filters
jira issue list --created today
jira issue list --created week
jira issue list --updated -2d

# Plain output for scripting
jira issue list --plain --no-headers

# Specific columns
jira issue list --plain --columns key,summary,status,assignee

# Raw JQL query
jira issue list -q"status = 'In Progress' AND assignee = currentUser()"

# Paginate results
jira issue list --paginate 20
jira issue list --paginate 10:50 # start:limit
```

---

## Creating Issues

```bash
# Interactive creation
jira issue create

# Non-interactive with all fields
jira issue create \
    -tBug \
    -s"Login button not working" \
    -b"Users cannot click the login button on Safari" \
    -yHigh \
    -lbug -lurgent

# Create and assign to self
jira issue create -tTask -s"Summary" -a$(jira me)

# Create subtask (requires parent)
jira issue create -tSub-task -P"PROJ-123" -s"Subtask summary"

# Create with custom fields
jira issue create -tStory -s"Summary" --custom story-points=3

# Skip prompts for optional fields
jira issue create -tTask -s"Quick task" --no-input

# Open in browser after creation
jira issue create -tBug -s"Bug title" --web

# Read description from file
jira issue create -tStory -s"Summary" --template /path/to/template.md

# Read description from stdin
echo "Description here" | jira issue create -tTask -s"Summary"
```

**Multi-line content:** The CLI chokes on multi-line strings. Write to `/tmp` first:

```bash
cat > /tmp/jira_body.md <<'EOF'
## Description
User needs ability to export data...

## Acceptance Criteria
- Export works for CSV
- Export works for JSON
EOF

jira issue create --no-input \
  -tStory \
  -pPROJ \
  -s"Add export functionality" \
  -b"$(cat /tmp/jira_body.md)"
```

---

## Transitioning Issues

```bash
# Move to a state
jira issue move ISSUE-KEY "In Progress"
jira issue move ISSUE-KEY "Done"
jira issue move ISSUE-KEY "To Do"

# Move with comment
jira issue move ISSUE-KEY "Done" --comment "Completed the implementation"

# Move and set resolution
jira issue move ISSUE-KEY "Done" -R"Fixed"

# Move and reassign
jira issue move ISSUE-KEY "In Review" -a"reviewer@example.com"

# Open in browser after transition
jira issue move ISSUE-KEY "Done" --web
```

---

## Assigning Issues

```bash
# Assign to specific user
jira issue assign ISSUE-KEY "user@example.com"
jira issue assign ISSUE-KEY "John Doe"

# Assign to self
jira issue assign ISSUE-KEY $(jira me)

# Assign to default assignee
jira issue assign ISSUE-KEY default

# Unassign
jira issue assign ISSUE-KEY x
```

---

## Comments

```bash
# Add comment
jira issue comment add ISSUE-KEY -b"This is my comment"

# Add comment from file
jira issue comment add ISSUE-KEY --template /path/to/comment.md
```

---

## Sprints

```bash
# List sprints
jira sprint list

# Active sprint only
jira sprint list --state active

# Add issue to sprint
jira sprint add SPRINT-ID ISSUE-KEY

# Close sprint
jira sprint close SPRINT-ID
```

---

## Linking Issues

| Relationship | Meaning |
|--------------|---------|
| `Blocks` | First ticket blocks second |
| `Relates` | General relationship |
| `Duplicate` | Same work |
| `Epic-Story` | Story belongs to Epic |

```bash
# Basic link
jira issue link PROJ-123 PROJ-456 "Relates"

# Blocker (blocker comes first)
jira issue link PROJ-100 PROJ-200 "Blocks"
# Meaning: PROJ-100 blocks PROJ-200

# Link to epic
jira issue link PROJ-EPIC PROJ-STORY "Epic-Story"
```

---

## Other Commands

```bash
# Open issue in browser
jira open ISSUE-KEY

# Show current user
jira me

# Server info
jira serverinfo

# List projects
jira project list

# List boards
jira board list
```

---

## Gotchas

### `jira issue edit` exits 1 on success

The CLI prints `✓ Issue updated` and the URL but exits with code 1. Do not treat
exit code 1 as failure for `jira issue edit`. Check for the `✓` in stdout instead.

```bash
# Pattern: run sequentially, check output not exit code
jira issue edit DAD-123 --no-input -b"$(cat /tmp/body.md)" 2>&1
# ✓ Issue updated → success despite exit 1
```

### Parallel edits cancel each other

Running multiple `jira issue edit` calls in parallel causes all but the first to be
cancelled. Always run description updates **sequentially**.

```bash
# Good — sequential
jira issue edit DAD-100 --no-input -b"$(cat /tmp/a.md)" 2>&1
jira issue edit DAD-101 --no-input -b"$(cat /tmp/b.md)" 2>&1

# Bad — parallel (second call cancels)
# jira issue edit DAD-100 & jira issue edit DAD-101
```

### Jira Cloud descriptions use ADF, not wiki markup

Jira Cloud stores descriptions as **Atlassian Document Format (ADF)** JSON.
The `jira` CLI accepts wiki markup input but **converts hyperlinks incorrectly**:
`[text|url]` becomes two separate ADF nodes (italic label + bare URL), which
renders broken in the browser.

**Rule**: any description containing hyperlinks must be written via REST API v3
with ADF JSON directly. The CLI is fine for plain text and simple formatting
without links.

→ See `references/jira-cloud-adf.md` for the full pattern, Python ADF builder,
and valid node types.

### Epic description template

For PI epics, load `references/epic-template.md`. Key structure:
1. Cross-system links block at the top (GitHub issue, TP Objective, TP Feature, epic file)
2. `h2. Problem Statement`
3. `h2. Acceptance Criteria`
4. `h2. Sprint Breakdown` (table)
5. `h2. Dependencies` (table with incoming + outgoing)
6. `h2. Risks` (table with ID, severity, ROAM, mitigation)
7. `h2. Notes` (deferred decisions, constraints, carry-over context)

**Note**: use ADF JSON (not wiki markup) when the epic description contains
hyperlinks — see `references/jira-cloud-adf.md`.
