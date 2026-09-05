---
name: architecture-decision-records
description: Create, update, and review Architecture Decision Records (ADRs) using the Y-Statement format. Use when making a significant architectural decision, choosing between implementation approaches, evaluating trade-offs, or capturing immutable architectural history. Triggers include "write an ADR", "document this decision", "architecture decision", "Y-statement", or "record this trade-off".
---

# Architecture Decision Records

Create ADRs that capture *why* an architectural decision was made, the forces balanced, and the trade-offs accepted—not merely *what* was implemented.

## Core Architectural Qualities & Principles

Every generated ADR must satisfy and consider these foundational qualities:

1. **Intention-Revealing (Intent over Mechanism):**
   - Frame the decision around **domain capability and architectural intent**, not incidental tooling or vendor names (e.g., *"Ephemeral Request De-duplication"* rather than *"Use Redis"*).
   - The core intent and invariant must remain understandable even if the underlying library or cloud service is replaced.

2. **Architectural Reification (Making the Implicit Concrete):**
   - Decisions must not rely on unwritten tribal agreements or developer memory.
   - Explain how the decision is **mechanically reified and enforced** in the codebase (e.g., explicit domain types, strict module boundaries, architectural fitness functions, CI lints, contract tests, or telemetry alarms).

3. **Singular Focus (One ASR per Document):**
   - Address exactly one Architecturally Significant Requirement (ASR) per ADR.
   - If a proposed decision covers multiple orthogonal concerns (e.g., language runtime, persistence store, auth provider, and hosting), decompose it into separate, focused ADRs.

4. **Objective & Consequence-Driven ("No Free Lunch"):**
   - Refuse decisions that list only benefits. Every architectural choice accepts trade-offs.
   - Actively identify and document negative consequences: operational complexity, latency overhead, performance trade-offs, or accepted technical debt.

5. **Alternatives Required (Avoid Strawmen):**
   - An ADR is incomplete without legitimate rejected options.
   - Document at least one viable alternative with its strongest argument and the objective reason it was not chosen. Avoid ridiculous caricature alternatives.

6. **Reversibility & Optionality (Two-Way vs. One-Way Doors):**
   - Assess how difficult and costly it will be to reverse this choice in 12–24 months.
   - Introduce architectural seams or abstractions to preserve optionality where possible.
   - Define concrete **Revisit Criteria** (e.g., throughput thresholds, team growth, or external constraints that invalidate the choice).

7. **The Advice Process (Social Alignment):**
   - Architecture requires team alignment over isolated decree.
   - Explicitly record who was **Consulted** (whose input was sought) and who must be **Informed** (stakeholders impacted).

8. **Immutability & Traceability (Living Proposals vs. Historical Records):**
   - While in review (`Proposed`), an ADR is a living document and may be revised in place.
   - Once `Accepted`, an ADR is an immutable historical record. Never rewrite an accepted ADR.
   - To revise a past decision, create a new `Proposed` ADR that links `Supersedes: [ADR-00X](...)`, and upon acceptance mark the prior ADR as `Superseded by [ADR-00Y](...)`.

9. **Proximity & Portability:**
   - Store ADRs as plain Markdown (`.md`) co-located with the source code inside the repository to ensure version control alignment.

---

## Agent Directives (Operational Guardrails)

- **Active Interrogation:** When working interactively with a user, if downsides, risks, or alternatives are omitted, prompt for them before writing:
  - *"What are the primary trade-offs, operational burdens, or technical debt accepted with this choice?"*
  - *"Who was consulted and who needs to be informed?"*
  - *"What was the runner-up alternative and why was it rejected?"*
- **Downside Gate:** Refuse to finalize an ADR that lists only positive consequences.
- **Decomposition Gate:** If a user requests a sprawling decision, propose breaking it down into distinct, single-focus ADRs before drafting.

---

## When to Write an ADR

Write one when:
- Choosing between two or more valid implementation approaches with distinct trade-offs
- Adding, changing, or removing a public API, service boundary, or subsystem contract
- Accepting technical debt or operational burden that future maintainers will question
- Introducing a new technology, architectural pattern, or paradigm
- Deviating from an established codebase pattern with good reason

Skip for:
- Routine bug fixes with an obvious solution
- Cosmetic, formatting, or stylistic changes
- Easily reversible, low-stakes implementation details

---

## The Y-Statement Format (The Decision Anchor)

```
In context of [situation / use case],
facing [concern / tension / constraint],
we decided for [chosen option]
to achieve [quality attribute / goal],
accepting [downside / trade-off].
```

This single sentence forces synthesis: if the Y-Statement cannot be drafted cleanly, the trade-offs are not yet sufficiently understood.

---

## Instructions & Workflow

1. **Discover Repository Conventions:**
   - Scan the codebase for existing ADR directories: `docs/adr/`, `docs/decisions/`, `.github/decisions/`, or `doc/architecture/decisions/`. Default to `docs/adr/` if none exist.
   - Inspect existing filenames to detect the numbering and naming convention (e.g., `0001-title.md` vs `ADR-001-title.md`). Determine the next sequential number.
2. **Frame Intent, Forces, and Stakeholders:**
   - Define the architectural intent (avoid mechanism-first titles).
   - Identify stakeholders consulted and informed.
   - Identify at least one credible alternative and at least one non-trivial downside.
3. **Draft the Y-Statement:**
   - Synthesize the core decision into the 5-clause Y-statement format.
4. **Instantiate the Template:**
   - Load [`references/adr-template.md`](references/adr-template.md) and populate all sections.
   - Document how the decision is reified and enforced in code or CI.
5. **Verify Against Core Qualities:**
   - Check against the 9 Core Architectural Qualities & Principles above.
6. **Update the ADR Index:**
   - If an `index.md` or `README.md` exists in the ADR directory, append a table row with the new ADR's ID, Title, Status, and Date.

---

## Reviewing an ADR

When asked to review an existing ADR:
1. **Intention Check:** Is the decision framed around architectural capability, or just naming a tool?
2. **Honesty Check:** Are negative consequences genuine, or is it a one-sided justification?
3. **Alternative Check:** Is the alternative realistic with substantive rationale for rejection?
4. **Reification Check:** Is there a mechanism (type, lint, test, boundary) that enforces this decision?
5. **Y-Statement Integrity:** Does the Y-Statement clearly link the tension, choice, benefit, and trade-off?

---

## References

- [`references/adr-template.md`](references/adr-template.md) — Standard markdown ADR template.
- [`references/example-adr.md`](references/example-adr.md) — Gold-standard example illustrating architectural qualities in practice.
