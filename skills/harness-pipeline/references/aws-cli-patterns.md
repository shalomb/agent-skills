# Harness Pipeline Patterns for AWS CLI Execution

In Harness NextGen pipelines, there are **three primary patterns** to execute AWS CLI commands against target accounts.

---

## Pattern 1: Delegate Identity / IRSA (Kubernetes EKS Delegate)
**Best for**: Secure, zero-secret automation running on internal Kubernetes delegates.

When a delegate pod runs in an EKS cluster with **IAM Roles for Service Accounts (IRSA)**, any step executed on that delegate inherits the pod's AWS IAM credentials automatically via the default AWS SDK/CLI credential provider chain.

```yaml
- step:
    type: ShellScript
    name: Run AWS CLI via Delegate IRSA
    identifier: run_aws_cli_irsa
    spec:
      shell: Bash
      onDelegate: true
      delegateSelectors:
        - avm-delegate-usvga92348-eks-p002
      source:
        type: Inline
        spec:
          script: |-
            #!/bin/bash
            set -euo pipefail
            
            # Authenticates automatically via $AWS_WEB_IDENTITY_TOKEN_FILE
            aws sts get-caller-identity
            aws s3 ls
```

---

## Pattern 2: Containerized Execution with Pre-built AWS CLI (`type: Run`)
**Best for**: Consistent toolchains, avoiding dynamic installation of packages (`apt`, `curl`, `awscli`) at pipeline runtime.

Instead of installing the AWS CLI inside a base VM or delegate, use a lightweight, pre-packaged container image (`amazon/aws-cli:latest` or custom Docker/JFrog image).

```yaml
- step:
    type: Run
    name: Execute AWS CLI Container
    identifier: execute_aws_cli_container
    spec:
      connectorRef: account.dockerhub
      image: amazon/aws-cli:latest
      shell: Sh
      command: |-
        aws sts get-caller-identity
        aws s3 ls
```

---

## Pattern 3: Dynamic Role Assumption via Harness Secrets & JEXL
**Best for**: Multi-account cross-account operations where the pipeline must assume a role into a target account on the fly.

```yaml
- step:
    type: ShellScript
    name: Assume Target Role and Run CLI
    identifier: assume_role_and_run
    spec:
      shell: Bash
      onDelegate: true
      source:
        type: Inline
        spec:
          script: |-
            #!/bin/bash
            set -euo pipefail

            ROLE_ARN="arn:aws:iam::<+pipeline.variables.targetAccountId>:role/HarnessDeploymentRole"
            
            CREDS=$(aws sts assume-role \
              --role-arn "$ROLE_ARN" \
              --role-session-name "HarnessPipeline-<+pipeline.executionId>" \
              --output json)

            export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r '.Credentials.AccessKeyId')
            export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r '.Credentials.SecretAccessKey')
            export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r '.Credentials.SessionToken')

            echo "Successfully assumed role into <+pipeline.variables.targetAccountId>"
            aws sts get-caller-identity
```
