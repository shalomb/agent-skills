# ADR Template (Y-Statement & Architectural Qualities)

A standard, domain-agnostic template for Architecture Decision Records (ADRs). Copy this template into your project's ADR directory (e.g., `docs/adr/0001-intention-revealing-title.md`).

---

```markdown
# ADR-NNN: [Intention-Revealing Title]

- **Status:** Proposed | Accepted | Deprecated | Superseded by [ADR-XXX](...)
- **Date:** YYYY-MM-DD
- **Decider(s):** [Who owns this architectural choice]
- **Consulted:** [Whose input was sought — Advice Process: e.g., Security, Platform, Data Team]
- **Informed:** [Who must be notified upon acceptance]
- **Supersedes:** [Link to prior ADR, if replacing an existing accepted decision]

## Context

[Describe the context, problem statement, and forces driving this decision. What technical, business, or operational tensions exist (e.g., developer velocity vs. operational overhead, consistency vs. availability, flexibility vs. cognitive load)?]

## Decision

[State the chosen architectural approach. Frame the decision around **architectural intent and domain capability** rather than only named tools or libraries.]

## Rationale (Y-Statement)

In context of [use case / situation],
facing [concern / tension / constraint],
we decided for [chosen option]
to achieve [quality attribute / goal],
accepting [downside / trade-off].

## Architectural Reification & Enforcement

[How is this decision made tangible, observable, and enforceable in the codebase? 
Examples:
- Explicit domain types, schemas, or state machines
- Strict module boundaries or package visibility rules
- Automated architectural fitness functions, lint rules, or CI contract tests
- Specific metrics, tracing, or operational alarms]

## Consequences

### Positive Outcomes (+ Gains)
+ [Gained quality attribute, capability, or reduction in risk]
+ [Secondary benefit]

### Negative Consequences & Trade-offs (- Costs & Accepted Debt)
- [Explicit downside, performance cost, or operational complexity accepted]
- [Technical debt or limitation introduced]
- [Cognitive load or training required]

## Alternatives Considered

### [Option A: Name of Alternative]
- **Description:** [Brief summary of the alternative]
- **Strongest Argument:** [Why this option was compelling]
- **Why Rejected:** [Specific, objective reason this was not chosen]

### [Option B: Name of Alternative]
- **Description:** [Brief summary of the alternative]
- **Strongest Argument:** [Why this option was compelling]
- **Why Rejected:** [Specific, objective reason this was not chosen]

## Revisit Criteria

- [Define concrete metric thresholds, architectural changes, or events that would trigger re-evaluating or superseding this decision (e.g., throughput exceeding 5,000 req/s, team doubling, or upstream vendor change).]
```
