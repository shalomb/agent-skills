---
name: architecture-decision-records
description: Create, update, and review Architecture Decision Records (ADRs) using the Y-Statement format. Use when making a significant architectural decision, choosing between implementation approaches, or documenting a trade-off that future maintainers should understand. Triggers include "write an ADR", "document this decision", "architecture decision", "Y-statement", or "record this trade-off".
---

# Architecture Decision Records

Create ADRs that capture *why* a decision was made, not just *what* was decided.

## When to write an ADR

Write one when:
- Choosing between two or more valid implementation approaches
- Adding, changing, or removing a public API, interface, or module boundary
- Accepting a trade-off future maintainers might question
- Deviating from an established pattern with good reason

Skip for: bug fixes with an obvious solution, cosmetic changes, reversible low-stakes choices.

## Instructions

1. Identify the decision to document and the forces acting on it
2. Load `adr-template.md` for the format and Y-Statement guidance
3. Fill in each section: Status, Context, Decision, Rationale, Consequences, Alternatives
4. Place in `docs/adr/ADR-NNN-short-title.md` or `.github/decisions/`
5. Link back to the ADR from relevant code comments and PR descriptions

## Y-Statement format (core of every ADR)

```
In context of [situation/use case],
facing [concern / tension / constraint],
we decided for [chosen option]
to achieve [quality attribute / goal],
accepting [downside / trade-off].
```

This one paragraph forces clarity: if you can't write the Y-Statement, the decision isn't understood well enough to record.

## Reference

Load `adr-template.md` for the full template, variable/output design examples (Terraform), and guidance on when to create sub-ADRs.
