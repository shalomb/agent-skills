---
description: Create, update, or review an Architecture Decision Record (ADR)
---

You are tasked with: Create, update, or review an Architecture Decision Record (ADR).

Follow the instructions in the `architecture-decision-records` skill:
1. Enforce the 5 Core Tenets:
   - **Intent over Mechanism:** Domain capability and architectural invariants over tool brand names.
   - **Reification over Tribal Memory:** Mechanically enforceable via explicit types, module boundaries, automated CI fitness functions (e.g., ArchUnit, import linter rules), contract tests, or alarms.
   - **Honest Trade-offs & Real Alternatives:** Zero free lunches; evaluate genuine runners-up and state why they were rejected.
   - **Advice Process over Gatekeepers:** Autonomous team ownership with transparent alignment (`Consulted` and `Informed`).
   - **Reversibility & Immutability:** Two-way doors with explicit revisit criteria; immutable accepted history.
2. Structure the record using the 8-row Tabular Y-Statement, prioritized Decision Drivers (`DRV-01`, `DRV-02`, etc.), and the Multi-Criteria Comparison Matrix.
3. Pass the Uninformed Reader Test (understandable in 3 minutes) and guard against the 6 Anti-Patterns.
4. Fulfill the user's specific request: drafting a new ADR or reviewing an existing one.

User request:
$ARGUMENTS
