# Software Design Principles Catalogue

This document serves as a living catalogue of software design principles discovered during coding sessions.

## 1. DWIM (Do What I Mean) Pattern

- **Context/Problem:** When a user consumes a module or building block, they often have to provide boilerplate configuration or wire up disconnected components (like attaching a specific security group to an instance just to allow health checks to pass). If they forget, the deployment fails or times out.
- **Solution/Pattern:** The module should anticipate the user's intent and automatically handle the required boilerplate internally. If a feature (like health checks) is enabled, the module should intrinsically inject the necessary networking, IAM roles, or configurations into the underlying resources without forcing the user to explicitly define them. Ensure a "pit of success".
- **Example:** In the ASG Building Block, when `health_check_lambda_enabled = true`, the module automatically provisions a `readiness_ingress` security group and seamlessly injects it into the ASG's Launch Template. The user no longer has to manually attach a health check SG to `vpc_security_group_ids`.
