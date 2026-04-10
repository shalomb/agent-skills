# GitHub Epic Issue Template

Use this template when creating GitHub issues that mirror Jira/TargetProcess PI epics.

## When to Use

- Creating a PI-level epic issue in the engineering repo
- The issue will have child sub-issues for user stories and tasks (added later)
- There is a corresponding Jira epic and TargetProcess Objective + Feature

## Title Convention

```
Epic: <Objective title>
```

e.g. `Epic: IaCRE FY2026Q1`

## Labels

Always apply:
- `epic` — marks this as a PI epic
- `pi:<yy>-<n>` — e.g. `pi:1-26`
- `committed` OR `uncommitted`
- `type:feature` / `type:enabler` / `type:capability` / `tech-debt`
- `HIGH` / `MEDIUM` / `LOW` if priority warrants it

## Body Template

```markdown
## Problem Statement

<!-- Why this work exists. Focus on the problem, not the solution. -->

## Acceptance Criteria

- [ ] <!-- Testable, unambiguous outcome -->
- [ ] 
- [ ] 

## Dependencies

| Direction | Issue / Ticket | Status | Notes |
|-----------|---------------|--------|-------|
| depends-on | <!-- #issue or PROJ-123 --> | unacknowledged | |
| incoming | <!-- #issue or PROJ-123 --> | unacknowledged | <!-- who is waiting on us --> |

## Risks

| Severity | Description | Mitigation |
|----------|-------------|------------|
| high | | |

## Sub-Issues

<!-- Link child issues here as they are created. One checkbox per story/task. -->

- [ ] <!-- #issue — Story: ... -->

## References

| | Link |
|---|---|
| Jira Epic | [PROJ-XXXX](https://onetakeda.atlassian.net/browse/PROJ-XXXX) |
| TP Objective | [XXXXXXX](https://takedamain.tpondemand.com/entity/XXXXXXX) |
| TP Feature | [XXXXXXX](https://takedamain.tpondemand.com/entity/XXXXXXX) |
| Epic file | [DAD-XXXX-*.md](https://github.com/oneTakeda/gmsgq-dad-10345-fusion-platform-control-tower/blob/main/program-increments/PI-1-26/DAD-XXXX-*.md) |
| Carry-over from | <!-- PROJ-XXXX if applicable --> |
```

## Notes

- **Sub-Issues**: Do not inline the decomposition. Add `- [ ] #issue` links as child issues are created.
- **Dependencies**: List both outgoing (`depends-on`) and incoming (`incoming`) — incoming means another team/epic is waiting on this one.
- **References**: Always include all four links (Jira, TP Objective, TP Feature, epic file). These are the canonical cross-system joins.
- **Carry-over**: If this is a carry-over from a previous PI, link the predecessor Jira epic in References.

---

## Creating Labels

Labels with colons (e.g. `pi:1-26`, `type:enabler`) work fine with `gh label create`.
Check for existing labels first to avoid duplicate errors:

```bash
REPO="org/repo"
gh label create "epic"       --color "5319e7" --description "PI-level epic" --repo "$REPO"
gh label create "pi:1-26"    --color "0075ca" --description "Program Increment 1/26" --repo "$REPO"
gh label create "committed"  --color "0e8a16" --description "Committed PI objective" --repo "$REPO"
gh label create "uncommitted" --color "e4e669" --description "Uncommitted PI objective" --repo "$REPO"
gh label create "tech-debt"  --color "d93f0b" --description "Technical debt" --repo "$REPO"
gh label create "type:capability" --color "a38bb9" --description "Capability objective" --repo "$REPO"
gh label create "type:enabler"    --color "a38bb9" --description "Enabler objective" --repo "$REPO"
gh label create "type:feature"    --color "a38bb9" --description "Feature objective" --repo "$REPO"
```

If labels already exist, use `--force` to update colour/description.

---

## Safe Issue Rewrite Pattern

When an existing issue needs to be repurposed as an epic (body replaced):

1. **Archive the original body as a comment** — preserves context, never loses history
2. **Rewrite the body** with the epic template
3. **Update labels** — add new, remove obsolete in the same `gh issue edit` call

```bash
# Step 1 — archive original body
ORIGINAL=$(gh issue view 42 --repo ORG/REPO --json body -q .body)
gh issue comment 42 --repo ORG/REPO --body "$(cat <<EOF
## Archived: Original content

The original body is preserved here after this issue was promoted to a PI epic.

<details>
<summary>Original content (click to expand)</summary>

${ORIGINAL}

</details>
EOF
)"

# Step 2 — rewrite body
gh issue edit 42 --repo ORG/REPO \
  --title "Epic: New Title" \
  --body-file /tmp/epic_body.md \
  --add-label "epic,pi:1-26,committed,type:enabler" \
  --remove-label "enhancement,spike"
```
