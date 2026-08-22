---
name: daily-status
description: >
  Report what you actually did — git commits, GitHub PRs and Project moves,
  assigned GitHub issues with new activity, and Jira issues — then log it to a
  dated file in ~/projects/dailies/. Use when the user asks what they did
  yesterday or wants a status summary of their own recent work. For turning a
  meeting transcript into a plan for the day, use `daily-standup` instead.
  Triggers on: 'daily status', 'what did I do yesterday', 'what have I been
  working on', 'status summary', 'my recent work'.
---

# Daily Status

Gathers yesterday's activity from the systems that already record it, and writes
a dated status note. The goal is recall, not invention — every line in the
output must trace back to something a command returned.

## Scope

This skill covers the **daily** cycle. For sprint boundaries — stocktake,
planning the next iteration — use `iteration-planner` instead.

## Step 1: Set the window

Default window is "since the last working day":

```bash
# Monday looks back to Friday; otherwise yesterday
if [ "$(date +%u)" = "1" ]; then SINCE="3 days ago"; else SINCE="1 day ago"; fi
SINCE_ISO=$(date -d "$SINCE" +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)
```

If the user names a different window ("since Thursday", "this week"), use that.

## Step 2: Gather

Run these independently — a failing source must not abort the report. If a
source is unavailable, note it as unavailable rather than silently omitting it.

### Git commits

Across your active repos:

```bash
for r in ~/projects/*/ ~/shalomb/*/ ~/oneTakeda/*/; do
  [ -d "$r/.git" ] || continue
  log=$(git -C "$r" log --author="$(git -C "$r" config user.email)" \
        --since="$SINCE" --pretty='  %h %s' 2>/dev/null)
  [ -n "$log" ] && printf '%s\n%s\n' "$(basename "$r")" "$log"
done
```

Adjust the repo roots to wherever the user's work actually lives.

### GitHub PRs

```bash
gh search prs --author=@me --updated=">=$SINCE_ISO" \
  --json repository,number,title,state,url --limit 50
```

### GitHub issues assigned to me, with new activity

This is the "decisions and comments" source — an issue you own that moved
without you committing anything:

```bash
gh search issues --assignee=@me --state=open \
  --updated=">=$SINCE_ISO" --json repository,number,title,url --limit 50
```

For each hit, pull what actually changed in the window:

```bash
gh issue view <N> --repo <owner/repo> \
  --json title,url,comments \
  --jq '{title, url, recent: [.comments[] | select(.createdAt >= "'"$SINCE_ISO"'") | {author: .author.login, body: .body[:400]}]}'
```

Summarise the substance of new comments — decisions reached, questions raised,
blockers named. Do not paste comment bodies wholesale.

### GitHub Project moves

If the user tracks work on a GitHub Project, check for items whose status
changed in the window. Follow the patterns in `iteration-planner` for
project/field queries rather than reinventing them.

### Jira

Use the `jira-issue-manager` skill — it resolves CLI vs MCP backend itself.
With the CLI backend:

```bash
jira issue list -a"$(jira me)" --updated ">-1d" --plain
jira issue list -a"$(jira me)" -s"In Progress" --plain
```

## Step 3: Compose

Three sections. Keep each item one line, with a link or ref.

- **Yesterday** — what completed or moved. Merged PRs, commits, issues closed,
  decisions recorded.
- **Today** — what is in progress or next. In-progress Jira issues, open PRs
  awaiting review, assigned issues not yet started.
- **Blockers** — anything waiting on someone else: PRs open for review, issues
  with a question addressed to you, failing CI.

Blockers are inferred, not fabricated. A PR open for >2 days with no review is
a blocker; an issue where someone asked you a question is a blocker. If nothing
qualifies, write `None`.

## Step 4: Write the daily note

```bash
mkdir -p ~/projects/dailies
```

Write to `~/projects/dailies/YYYY-MM-DD.md`. If the file already exists, append
a new timestamped section — never overwrite an earlier entry in the same day.

```markdown
# Daily Status — 2026-08-22

_Window: since 2026-08-21_

## Yesterday
- Merged [#412 fix retry backoff](url) — agent-skills
- 3 commits on `superpowers`: trigger phrases for brainstorming, dispatching
- PROJ-118 moved to In Review

## Today
- PROJ-121 (In Progress) — TDD trigger deconfliction
- [#415](url) open, awaiting review

## Blockers
- [#409](url) open 4 days, no reviewer assigned
- PROJ-118 — Priya asked which region to target, unanswered

## Sources
git, gh (PRs, issues), jira
```

Always include the **Sources** line, naming which sources contributed and which
were unavailable. It is how the reader knows what the summary could not see.

## Step 5: Report

Print the composed status to the terminal as well, and tell the user the path
written. They usually want to read it out immediately.

## Notes

- Never invent activity to fill a section. An empty Yesterday is a real and
  useful signal.
- Prefer the user's own commits (`--author` by configured email) over all
  branch activity — a status report is first-person.
- Keep the whole note under ~30 lines. If there is more, summarise by theme
  rather than listing every commit.
