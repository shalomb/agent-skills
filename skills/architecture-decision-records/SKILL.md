---
name: architecture-decision-records
description: Create, update, and review Architecture Decision Records (ADRs) using the Y-Statement format. Use when making a significant architectural decision, choosing between implementation approaches, evaluating trade-offs, or capturing immutable architectural history. Triggers include "write an ADR", "document this decision", "architecture decision", "Y-statement", or "record this trade-off".
---

# Architecture Decision Records

Create ADRs that capture *why* an architectural decision was made, the forces balanced, and the trade-offs accepted—not merely *what* was implemented.

## Core Principles: The 5 Tenets

Every ADR generated or reviewed must adhere to these five universal tenets:

1. **Intent over Mechanism:** Frame decisions around domain capabilities and architectural invariants, not tool brands (e.g., *"Ephemeral Request De-duplication"* vs. *"Use Redis"*). The intent must hold even if tooling changes.
2. **Reification over Tribal Memory:** Architecture is what the system mechanically enforces, not what people remember. Every decision must anchor in code: explicit domain types, module boundaries, automated CI fitness functions (e.g., ArchUnit, import linter rules), contract tests, or telemetry alarms.
3. **Honest Trade-offs & Real Alternatives:** Zero "free lunches." Every choice incurs costs (operational debt, latency, lock-in). Evaluate genuine runners-up and state the concrete driver that disqualified them.
4. **Advice Process over Gatekeepers:** Decentralize decisions with transparent alignment rather than committee bottlenecks. Autonomously own choices, but explicitly record who was consulted (for expertise) and who is informed (for impact).
5. **Reversibility & Immutability:** Treat decisions as two-way doors: preserve optionality with seams and define explicit revisit criteria. Once accepted, records are immutable history—supersede with a new ADR, never rewrite.

*(Enforced via **Singular Focus & Plain Language**: exactly one decision per document, passing the 3-minute Uninformed Reader test in repository-co-located Markdown).*

## Agent Directives (Operational Guardrails)

- **Active Interrogation:** When working interactively with a user, if downsides, risks, or alternatives are omitted, prompt for them before writing:
  - *"What are the primary trade-offs, operational burdens, or technical debt accepted with this choice?"*
  - *"Who was consulted and who needs to be informed?"*
  - *"What was the runner-up alternative and why was it rejected?"*
- **Downside Gate:** Refuse to finalize an ADR that lists only positive consequences.
- **Decomposition Gate:** If a user requests a sprawling decision, propose breaking it down into distinct, single-focus ADRs before drafting.

---

## Anti-Patterns & Red Flags (STOP and Correct)

Before finalizing an ADR, the agent must self-critique against these common architectural traps:

| Anti-Pattern | Symptom / Red Flag | Required Correction |
|---|---|---|
| **The "God Decision"** | Multiple compound choices (e.g., database + caching + auth in one ADR). | **Decompose:** One ASR per document. Split into independent, linked ADRs. |
| **The Change Log** | Reading like a sprint recap or git commit log of tasks performed. | **Refocus:** Strip task history. ADRs document *decision forks*, not task execution. |
| **The Jargon Fortress** | Heavy tribal acronyms, insider shorthand, and unstated context. | **Apply Uninformed Reader Test:** Rewrite crisply so a newcomer understands the forces in 3 minutes. |
| **The Free Lunch** | Glowing benefits with only trivial/cosmetic cons ("minor learning curve"). | **Enforce Trade-offs:** Actively identify operational debt, blast radius, or performance costs accepted. |
| **The Strawman** | Ridiculous alternatives designed only to make the chosen option look good. | **Fair Representation:** List genuine runners-up and give their strongest arguments fair weight. |
| **The Implementation Manifesto** | Long code blocks, task steps, and migration runbooks. | **Extract to Issues/PRs:** Document the architectural invariant and reification; delegate task steps to epics. |

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

Format the Y-Statement as an 8-row scannable table:

| Dimension | Detail |
|---|---|
| **Context** | [Situation driving the decision — link to baseline evidence] |
| **Constraint(s)** | [Hard technical, budget, team, or regulatory limits] |
| **Requirement(s)** | [Core capability or ASR that must be delivered] |
| **Decision** | [Chosen architectural approach — or `[PROPOSED]` / `[PENDING]`] |
| **Alternatives Rejected** | [Primary rejected options — or `[PENDING]`] |
| **Rationale** | [Core justification linking requirement to decision] |
| **Tradeoff Accepted** | [Explicit non-trivial cost, debt, or limitation accepted] |
| **Decision Authority** | [Accountable role/decider — review timebox: YYYY-MM-DD] |

*Rule:* Keep rows concise (≤ 25 words). Elaborate in the dedicated sections of the ADR.

---

## Instructions & Workflow

1. **Discover Repository Conventions:**
   - Scan the codebase for existing ADR directories: `docs/adr/`, `docs/decisions/`, `.github/decisions/`, or `doc/architecture/decisions/`. Default to `docs/adr/` if none exist.
   - Inspect existing filenames to detect the numbering and naming convention (e.g., `0001-title.md` vs `ADR-001-title.md`). Determine the next sequential number.
2. **Classify Domain Archetype & Framework:**
   - Classify the decision archetype: *Cloud & Infrastructure*, *Software & Code Architecture*, or *Distributed Systems & Data*.
   - Consult [`references/architectural-frameworks.md`](references/architectural-frameworks.md) and select 2–3 driving pillars/qualities (e.g., AWS/Azure WAF Cost & Reliability vs. ISO 25010 Modifiability & Testability).
3. **Enumerate Prioritized Decision Drivers:**
   - Define the architectural intent (avoid mechanism-first titles).
   - Identify stakeholders consulted and informed (The Advice Process).
   - List 3–5 prioritized Decision Drivers (e.g., `DRV-01` primary ASR, `DRV-02` technical constraint, `DRV-03` quality attribute, `DRV-04` operational boundary).
   - These drivers anchor the Y-statement, define the rows in the Comparison Matrix, and provide the objective criteria for rejecting alternatives.
4. **Draft the Tabular Y-Statement:**
   - Synthesize the core decision into the 8-row Y-statement table, mapping `Constraint(s)` and `Requirement(s)` directly to the numbered Decision Drivers.
5. **Instantiate the Template:**
   - Load [`references/adr-template.md`](references/adr-template.md) and populate all sections.
   - Map the rows of the **Multi-Criteria Comparison Matrix** directly to the Decision Drivers.
   - In rejected alternatives, explicitly cite which Decision Driver(s) they failed or violated.
   - Document how the decision is reified and mechanically enforced in code or CI.
6. **Verify Against Core Qualities & Self-Critique:**
   - Check against the 5 Core Tenets above.
   - Run the **Uninformed Reader Test**: Can an engineer with zero prior context understand the problem, constraints, and why we chose this in under 3 minutes?
   - Scan against the Anti-Patterns table to ensure no God Decisions, change logs, free lunches, strawmen, or implementation bloat crept in.
7. **Update the ADR Index:**
   - If an `index.md` or `README.md` exists in the ADR directory, append a table row with the new ADR's ID, Title, Status, and Date.

---

## Reviewing an ADR

When asked to review an existing ADR:
1. **Intention Check:** Is the decision framed around architectural capability, or just naming a tool?
2. **Domain Quality Alignment:** Does it cite concrete quality pillars from the relevant framework (AWS/Azure WAF, ISO 25010, Evolutionary Architecture)?
3. **Decision Driver Traceability:** Are 3–5 prioritized decision drivers listed? Do the Y-Statement constraints/requirements, comparison matrix rows, and alternative rejections map back directly to these drivers?
4. **Uninformed Reader Test:** Is the language crisp, clear, and readable by anyone without relying on tribal jargon?
5. **Honesty & Downside Check:** Are negative consequences genuine and non-trivial, or is it a one-sided "free lunch"?
6. **Comparison Matrix:** Does the multi-criteria matrix evaluate realistic alternatives across the stated drivers?
7. **Reification Check:** Is there a concrete mechanism (type, lint, test, boundary) that mechanically enforces this decision?
8. **Anti-Pattern Gate:** Is the document free from God Decisions (multi-ASR bundling), change log narration, and implementation manifesto bloat?
9. **Y-Statement Completeness:** Are all 8 dimensions populated clearly without hand-waving?

---

## References

- [`references/adr-template.md`](references/adr-template.md) — Standard markdown ADR template with Decision Drivers, tabular Y-statement, and comparison matrix.
- [`references/architectural-frameworks.md`](references/architectural-frameworks.md) — Domain evaluation frameworks (AWS/Azure WAF, ISO 25010, Evolutionary Architecture, Distributed Data).
- [`references/example-adr.md`](references/example-adr.md) — Gold-standard example illustrating Decision Drivers, tabular Y-statement, and matrix in practice.
