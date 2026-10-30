# PR bot comments and merge-blocking checks

Use this when a workflow comments on pull requests (validation guidance,
plan output, coverage) or when a failing check must block merges.

## The problem

A workflow that calls `createComment` on every failed run adds a new
comment per push or title edit. The PR fills with copies and buries the
review. The comment also does not block anything: only a **required
status check** stops a merge.

## Pattern: one comment per PR

| Event | Action |
|---|---|
| First failure | Create the comment, `@author` on the first line (notifies once) |
| Failure, same reasons | Leave the comment alone |
| Failure, reasons changed | Edit in place (edits do not re-notify) |
| All checks pass | Delete the comment |
| Every run | Write the same text to `$GITHUB_STEP_SUMMARY` |

Identify the comment by a hidden marker and store a hash of the rendered
failures in it:

```markdown
<!-- pr-validation-comment -->
<!-- pr-validation-hash: 96748ba8e240823c -->
@author

## 🤖 Beep boop: 1 of 3 checks failed: PR title
```

```javascript
// actions/github-script
const marker = '<!-- pr-validation-comment -->';
const comments = await github.paginate(github.rest.issues.listComments,
  { owner, repo, issue_number, per_page: 100 });
const ours = comments.filter(c => c.user.type === 'Bot' && c.body.includes(marker));
for (const c of ours.slice(1)) {            // clean up duplicates from older runs
  await github.rest.issues.deleteComment({ owner, repo, comment_id: c.id });
}
const existing = ours[0];
if (!failed) { if (existing) await github.rest.issues.deleteComment({ owner, repo, comment_id: existing.id }); return; }
if (existing?.body.includes(hashLine)) return;   // reasons unchanged
existing
  ? await github.rest.issues.updateComment({ owner, repo, comment_id: existing.id, body })
  : await github.rest.issues.createComment({ owner, repo, issue_number, body });
```

## Make it readable in three seconds

- Headline: what failed and how many, e.g. `🤖 Beep boop: 2 of 3 checks failed: PR title, PR body`.
- A short pass/fail table, then a fix section **only for failed checks**.
- Plain-language reasons, not raw tool output: "74 characters; the limit is 50. Cut 24", and show where the limit falls.
- A collapsed `<details>` "Why this rule?" per section.
- Strip ANSI colour codes (`--color=false`, or a regex) before quoting tool output.
- Treat a **skipped** step as not failed; only `failure` counts.

## Keep the logic testable

Do the pass/fail decision, rendering and hashing in a script with unit
tests (e.g. `scripts/pr-validation-report.py`). The workflow passes step
outcomes and outputs as env vars and reads back `failed=` and `hash=` from
`$GITHUB_OUTPUT`. Keep only the GitHub API calls in `github-script`.

Test the API part live on the PR itself: set an invalid title (one comment
appears with the mention), push again (same comment edited), restore the
title (comment deleted, check green).

## Block merges with a required check

```bash
R=repos/<owner>/<repo>
# Exact check name and app id from a real run
gh api $R/commits/<sha>/check-runs --jq '.check_runs[]|[.name,.app.id]|@tsv'
# Current required checks
gh api $R/branches/main/protection --jq .required_status_checks.checks
# Add one (send the full list: PATCH replaces it)
jq -n '{strict:false,checks:[{context:"docs",app_id:15368},{context:"commitlint",app_id:15368}]}' |
  gh api -X PATCH $R/branches/main/protection/required_status_checks --input -
```

- Needs repo admin.
- A job skipped by `if:` (release-please, Dependabot) reports as passing, so
  it does not block those PRs.
