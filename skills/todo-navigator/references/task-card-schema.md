# Task Card Schema & Specification

Every task managed by `todo-navigator` is backed by a standalone Markdown task card located in the shadow directory:
`~/.cache/agent-skills/todos/<repo_slug>/tasks/<id>.md`

## Structure

```markdown
# Task: <Title>
**Parent:** [TODO.md](../TODO.md)
**ID:** `<id>`

## Acceptance Criteria (BDD)
- [ ] **Scenario 1: <Description>**
  - Given <precondition>
  - When <action>
  - Then <expected outcome>

## Target Codebase Artifacts
- `<file-path-1>`
- `<file-path-2>`

## Notes
- Non-obvious design decisions or context.
```

## Field Definitions

1. **Title & Parent:** Connects the card to the project backlog.
2. **Acceptance Criteria (BDD):** Follows Gojko Adzic's Specification by Example principles. Each scenario provides verifiable, unambiguous pass/fail criteria.
3. **Target Codebase Artifacts:** Concrete file paths that the task will touch or create.
4. **Notes:** Architectural guardrails, caveats, or trade-offs.
