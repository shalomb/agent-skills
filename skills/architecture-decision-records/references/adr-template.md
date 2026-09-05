# ADR Template (Decision Drivers, Tabular Y-Statement & Multi-Criteria Matrix)

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

[Describe the context, problem statement, and background. What situation forces this decision? What baseline metrics, incidents, or changes compelled this review? Link to relevant baseline evidence.]

## Decision Drivers

[List the 3–5 primary forces, constraints, and requirements compelling this decision in priority order. These drivers directly feed the Y-Statement, the Comparison Matrix, and alternative rejection rationales.]
1. **[DRV-01 — Core ASR / Capability]:** [e.g., Target throughput SLA, latency budget, or essential business capability]
2. **[DRV-02 — Technical / Resource Constraint]:** [e.g., Hard connection limits, legacy system compatibility, compute bounds]
3. **[DRV-03 — Quality Attribute / Framework Pillar]:** [e.g., ISO 25010 Modifiability/Testability, AWS WAF Security/Blast Radius]
4. **[DRV-04 — Operational / Organizational Constraint]:** [e.g., On-call cognitive burden, delivery timeline, licensing, compliance/GxP]

## Domain Quality Framework Alignment

[Identify the domain archetype and cite the 2–3 specific quality pillars driving this decision. See `references/architectural-frameworks.md` for guidance.]
- **Domain Archetype:** Cloud & Infrastructure | Software & Code | Distributed Systems & Data
- **Primary Framework:** AWS/Azure Well-Architected Framework | ISO/IEC 25010 & Evolutionary Architecture | CAP & Data Mesh
- **Guiding Quality Pillars:**
  1. *[Pillar/Quality 1 — e.g., Software Testability / Cloud Reliability]:* [How this choice directly satisfies this pillar]
  2. *[Pillar/Quality 2 — e.g., Operational Excellence / Cost Optimization]:* [How this choice directly satisfies this pillar]

## Decision

[State the chosen architectural approach. Frame the decision around **architectural intent and domain capability** rather than only named tools or libraries.]

## Y-Statement

| Dimension | Detail |
|---|---|
| **Context** | [Situation driving the decision — link to baseline evidence] |
| **Constraint(s)** | [Hard limits — reference DRV-02, DRV-04] |
| **Requirement(s)** | [Core ASRs to deliver — reference DRV-01, DRV-03] |
| **Decision** | [Chosen architectural approach — or `[PROPOSED]` / `[PENDING]`] |
| **Alternatives Rejected** | [Primary rejected options — or `[PENDING]`] |
| **Rationale** | [Core justification linking drivers to decision] |
| **Tradeoff Accepted** | [Explicit non-trivial cost, debt, or limitation accepted] |
| **Decision Authority** | [Accountable role/decider — review timebox: YYYY-MM-DD] |

*Rule:* Keep rows concise (≤ 25 words). Elaborate in the dedicated sections below.

## Architectural Reification & Enforcement

[How is this decision made tangible, observable, and mechanically enforced in the codebase?
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

### Multi-Criteria Comparison Matrix

*Map criteria directly to the Decision Drivers above.*

| Evaluation Criterion | Option A (Chosen) | Option B | Option C |
|---|---|---|---|
| **DRV-01: [Requirement]** | [Fit/Score] | [Fit/Score] | [Fit/Score] |
| **DRV-02: [Constraint]** | [Fit/Score] | [Fit/Score] | [Fit/Score] |
| **DRV-03: [Quality / WAF]** | [Fit/Score] | [Fit/Score] | [Fit/Score] |
| **DRV-04: [Ops / Team]** | [Fit/Score] | [Fit/Score] | [Fit/Score] |
| **Reversibility / Lock-in** | [Two-way door / open standard] | [...] | [...] |

### Option A: [Name of Chosen Option]
- **Why Chosen:** [Summary of primary advantage and fit across drivers]
- **Key Caveat:** [Primary trade-off accepted]

### Option B: [Name of Alternative]
- **Description:** [Brief summary of the alternative]
- **Strongest Argument:** [Why this option was compelling]
- **Why Rejected:** [Explicitly cite which Decision Driver(s) this option fails or violates]

## Revisit Criteria

- [Define concrete metric thresholds, architectural changes, or events that would trigger re-evaluating or superseding this decision (e.g., throughput exceeding 5,000 req/s, team doubling, or upstream vendor change).]
```
