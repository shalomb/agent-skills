# DWIM (Do What I Mean) Pattern

**Tags:** `UX`, `Developer Experience`, `Architecture`, `Automation`, `Boilerplate-Reduction`
**Related Principles:** *(None yet)*

- **Abstract Problem:** Users of a system are often burdened with connecting disparate, boilerplate components to achieve a single, high-level intent. If they forget a component, the system fails or times out, forcing them to understand the underlying mechanics of the system rather than their own goal.
- **Abstract Solution:** The system should anticipate the user's intent from minimal configuration. It should intrinsically handle hidden dependencies and boilerplate, providing a 'pit of success' without forcing explicit orchestration by the user.

## Concrete Examples

- **[Domain: Terraform / Infrastructure as Code]** In the AWS AutoScalingGroup Building Block, enabling `health_check_lambda_enabled = true` automatically provisions and injects a readiness security group. The caller does not have to manually attach network rules for the health checks to pass.
