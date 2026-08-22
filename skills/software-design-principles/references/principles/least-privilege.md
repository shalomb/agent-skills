# Principle of Least Privilege (PoLP)

**Tags:** `Security`, `Architecture`, `IAM`, `Blast-Radius`
**Related Principles:** *(None yet)*

## Context/Problem
Components, users, or modules are often given broad, overarching permissions (like `AdministratorAccess` or wildcard database roles) because it's easier during initial development. This leads to massive security blast radii; if a component is compromised or experiences a bug, it has the authorization to destroy or leak parts of the system it never actually needed access to.

## Solution/Pattern
Any system component, module, or user should be granted only the minimum permissions necessary to perform its intended function, and no more. Boundaries should be tightly scoped by time, resource, and action.

## Example
An AWS Lambda function designed to resize images should only have `s3:GetObject` on the upload bucket and `s3:PutObject` on the destination bucket. It should not be granted `s3:*` on all buckets, preventing it from accidentally deleting data if the code is manipulated.
