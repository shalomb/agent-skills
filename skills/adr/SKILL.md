---
name: adr
description: Create, update, or review an Architecture Decision Record (ADR). Short command alias for architecture-decision-records.
---

# Architecture Decision Records (/adr)

When invoked, load and execute the **`architecture-decision-records`** skill:
1. Follow all instructions and guidelines in [`architecture-decision-records`](../architecture-decision-records/SKILL.md).
2. Adhere to the 5 Core Tenets:
   - **Intent over Mechanism:** Domain capability and architectural invariants over tool brand names.
   - **Reification over Tribal Memory:** Mechanically enforceable via explicit types, module boundaries, automated CI fitness functions (e.g., ArchUnit, import linter rules), contract tests, or alarms.
   - **Honest Trade-offs & Real Alternatives:** Zero free lunches; evaluate genuine runners-up and state why they were rejected.
   - **Advice Process over Gatekeepers:** Autonomous team ownership with transparent alignment (`Consulted` and `Informed`).
   - **Reversibility & Immutability:** Two-way doors with explicit revisit criteria; immutable accepted history.
3. Structure the record using the 8-row Tabular Y-Statement, prioritized Decision Drivers (`DRV-01`, `DRV-02`, etc.), and the Multi-Criteria Comparison Matrix.
4. Pass the Uninformed Reader Test (understandable in 3 minutes) and guard against the 6 Anti-Patterns.
5. Fulfill the user's specific request: drafting a new ADR or reviewing an existing one.
