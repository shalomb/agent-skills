# Agent Definitions

Reusable agent definitions collected from various AI agent harnesses and sanitized for public use. Organized by source/domain.

All files have been stripped of organization-specific identifiers, credentials, internal URLs, and proprietary information. Placeholders like `{ORGANIZATION}`, `{GITHUB_ORG}` mark values you must supply for your context.

**Progressive disclosure principle**: agents are lean persona shells (~20–35 lines). Detailed checklists, templates, and standards live in `skills/*/references/` and are loaded on demand. No agent-local `references/` directories — all reusable content lives in the skills tree.

## Directory Structure

```
agents/
├── springfield/                         # Springfield crew — TDD + product delivery team
│   ├── bart.md                          # Adversarial reviewer (quality critic)
│   ├── lisa.md                          # Strategic planner & orchestrator
│   ├── lovejoy.md                       # Release & ceremony agent
│   ├── marge.md                         # Product & empathy agent
│   └── ralph.md                         # TDD executor & build agent
│
├── copilot-builtin/                     # GitHub Copilot CLI built-in agents (YAML, reference only)
│   ├── code-review.agent.yaml
│   ├── configure-copilot.agent.yaml
│   ├── explore.agent.yaml
│   ├── research.agent.yaml
│   └── task.agent.yaml
│
├── terraform-building-block/            # 7-agent model for Terraform module development
│   ├── README.md                        # Workflow overview and placeholder guide
│   ├── developer-agent.md
│   ├── triage-agent.md
│   ├── review-agent.md
│   ├── release-agent.md
│   ├── solutions-architect.md
│   ├── platform-architect.md
│   └── documentation-agent.md
│
└── terraform-troubleshooter.agent.md   # Generic Terraform error troubleshooter
```

## Checklist content lives in skills/

Agent reference content is stored in `skills/*/references/` so it's reusable across agents and skills:

| Content | Where |
|---|---|
| Bart's review checklist + Refactor Judge | `skills/bart/references/review-checklist.md` |
| Semver rules, changelog format, release notes | `skills/lovejoy/references/release-standards.md` |
| Adzic scenario quality scoring | `skills/adzic-index/` |
| Farley per-test quality checklist | `skills/farley-index/` |
| TDD red-green-refactor discipline | `skills/test-driven-development/` |
| TODO.md template (feature work) | `skills/ralph/references/todo-template.md` |
| ADR format + Y-Statement + design rules | `skills/architecture-decision-records/adr-template.md` |
| WAF review checklist + FEEDBACK.md template | `skills/pr-review/references/waf-and-feedback.md` |
| Issue triage: DoR, labels, priority matrix | `skills/github-cli/references/issue-triage-standards.md` |

## Agent format by harness

| File format | Load with |
|---|---|
| Plain `.md` | `pi --append-system-prompt @file`, `claude --system-prompt "$(cat file)"` |
| Copilot `.agent.md` | Copy to `~/.config/copilot/agents/`; invoke via `--agent stem-name` |
| Copilot `.agent.yaml` | Built into copilot CLI binary (reference only) |
| Gemini | Write to `GEMINI.md` in project root before invoking |

## Using Springfield agents

```bash
# pi
pi --append-system-prompt @agents/springfield/ralph.md --no-session --mode json -p @task.md

# claude
claude --system-prompt "$(cat agents/springfield/bart.md)" -p "review this" --dangerously-skip-permissions

# copilot (needs .agent.md frontmatter — see below)
cp agents/springfield/ralph.md ~/.config/copilot/agents/ralph.agent.md
copilot --agent ralph -p @task.md --yolo
```

## Using terraform-troubleshooter

```bash
cp agents/terraform-troubleshooter.agent.md ~/.config/copilot/agents/
# Edit to set {KEDB_REPO} etc.
copilot --agent terraform-troubleshooter -p "Error: Error creating S3 bucket: AccessDenied"
```
