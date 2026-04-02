# ADR Template (Y-Statement Format)

Architecture Decision Records for Terraform modules.

## Format

```markdown
# ADR-NNN: [Decision Title]

## Status
Proposed / Accepted / Deprecated / Superseded by ADR-XXX

## Context
[Problem statement and background — what situation forces this decision?]

## Decision
[What we decided to do]

## Rationale (Y-Statement)
In context of [use case / situation],
facing [concern / tension / constraint],
we decided for [chosen option]
to achieve [quality attribute / goal],
accepting [downside / trade-off].

## Consequences
+ [Positive outcome 1]
+ [Positive outcome 2]
- [Trade-off accepted]
- [Limitation introduced]

## Alternatives Considered
- **[Option A]**: [Why rejected]
- **[Option B]**: [Why rejected]
```

## When to write an ADR

Write an ADR when:
- Adding, removing, or changing a user-facing variable or output
- Choosing between two or more valid implementation approaches
- Accepting a trade-off that future maintainers might question
- Deviating from a standard pattern with good reason

Skip for: cosmetic changes, bug fixes with obvious correct solution.

## Variable & output design principles

```hcl
# ✅ Match AWS provider attribute names exactly
variable "allocated_storage" {
  type        = number
  description = "Storage size in GiB. See: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance#allocated_storage"
}

# ❌ Don't hide AWS concepts with custom names
variable "storage" {
  type        = number
  description = "Storage amount"
}
```

```hcl
# ✅ Output names match aws resource attribute names
output "endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = aws_db_instance.main.endpoint
}

# ❌ Don't invent custom output names
output "connection_endpoint" { ... }
```

## Example structure

```
examples/
  basic/          # Minimal working example — copy-paste ready, all defaults
  with-kms/       # One advanced feature demonstrated
  multi-az/       # High availability / production pattern
```

Each example needs:
- `main.tf` — uses registry source with pessimistic constraint `~> X.Y`
- `variables.tf` + `outputs.tf`
- `README.md` — copy-paste instructions, what gets created, cleanup steps
