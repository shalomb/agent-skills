# Terraform Module Design Principles

Design guidelines for Terraform module APIs, variable naming, output strategy, and example directory structure.

## Variable & Output Design Principles

Match the underlying provider attribute names directly. Avoid unnecessary layers of indirection or custom naming abstractions.

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

## Example Directory Structure

Provide clear, working examples demonstrating real configurations:

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
