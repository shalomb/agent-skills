# Terraform Building Block Agents

Seven-agent model for developing, reviewing, releasing, and maintaining Terraform module repositories.

## Agents

| Agent | Role | When to use |
|---|---|---|
| `triage-agent` | Issue quality + DoR validation | A new issue arrives; before developer-agent starts |
| `developer-agent` | IaC implementation, TDD, atomic commits | Implementing a feature or fix |
| `review-agent` | WAF + architecture + quality PR review | Reviewing any PR |
| `release-agent` | Semver, changelog, TFC publishing | Merging and releasing a version |
| `solutions-architect` | Module API design, trade-off analysis, ADRs | Designing a new module or significant API change |
| `platform-architect` | Cross-module coherence, versioning, debt | Evaluating new module proposals or ecosystem drift |
| `documentation-agent` | Intro.md, Diataxis docs, variable docs, example READMEs | Any documentation work |

## Workflow

```
New issue
   ↓ triage-agent (DoR validation, labelling)
   ↓ solutions-architect (if new module or API redesign)
   ↓ developer-agent (implement → test → commit)
   ↓ review-agent (WAF + quality gate)
   ↓ release-agent (semver → publish)
```

## Reference content (in skills/, loaded on demand)

All detailed checklists and templates live in the skills tree:

- `skills/ralph/references/todo-template.md` — standard TODO.md structure for feature work
- `skills/architecture-decision-records/adr-template.md` — ADR format, Y-Statement, variable/output design rules
- `skills/pr-review/references/waf-and-feedback.md` — WAF checklist, breaking change analysis, FEEDBACK.md template
- `skills/github-cli/references/issue-triage-standards.md` — issue quality, DoR checklist, label taxonomy

## Placeholders to configure

| Placeholder | Replace with |
|---|---|
| `{ORGANIZATION}` | Your company/org name |
| `{GITHUB_ORG}` | Your GitHub organization slug |
| `{ORGANIZATION_TFC_ORG}` | Your Terraform Cloud org name |
| `{GITHUB_ORG}/{PLATFORM_TEAM}` | Your IaC platform team GitHub handle |
- `skills/lovejoy/references/release-standards.md` — semver rules, changelog, release notes template
