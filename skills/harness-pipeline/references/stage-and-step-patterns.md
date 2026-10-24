# Harness Stage and Step Patterns

## Stage Architecture

A Harness NextGen Pipeline is organized into sequential or parallel stages.

### 1. Deployment Stage (`type: Deployment`)
Deploys containers or artifacts to target infrastructure with rollback strategies.
```yaml
- stage:
    name: Deploy to Production
    identifier: deploy_production
    type: Deployment
    spec:
      deploymentType: Kubernetes
      service:
        serviceRef: payment_service
      environment:
        environmentRef: production_env
        infrastructureDefinitions:
          - infrastructureDefinitionRef: prod_k8s_cluster
      execution:
        steps:
          - step:
              name: Rolling Deployment
              identifier: rolling_deploy
              type: K8sRollingDeploy
              spec:
                skipDryRun: false
        rollbackSteps:
          - step:
              name: Rollback Deployment
              identifier: rollback_deploy
              type: K8sRollingRollback
              spec: {}
```

### 2. CI Stage (`type: CI`)
Builds, tests, and publishes artifacts.
```yaml
- stage:
    name: Build & Test
    identifier: build_and_test
    type: CI
    spec:
      cloneCodebase: true
      platform:
        os: Linux
        arch: Amd64
      runtime:
        type: Cloud
        spec: {}
      execution:
        steps:
          - step:
              type: Run
              name: Run Unit Tests
              identifier: run_unit_tests
              spec:
                connectorRef: account.dockerhub
                image: python:3.11-slim
                shell: Bash
                command: pytest -v
```

### 3. Custom Orchestration Stage (`type: Custom`)
Ideal for Infrastructure-as-Code (Terraform, OpenTofu, Ansible) and administrative automation without requiring a rigid service/environment binding.
```yaml
- stage:
    name: Provision Cloud Workspace
    identifier: provision_cloud_workspace
    type: Custom
    spec:
      execution:
        steps:
          - stepGroup:
              name: Terraform Workflow
              identifier: tf_workflow
              steps:
                - step:
                    type: ShellScript
                    name: Run Terraform Init & Plan
                    identifier: run_tf_plan
                    spec:
                      shell: Bash
                      onDelegate: true
                      source:
                        type: Inline
                        spec:
                          script: |-
                            terraform init
                            terraform plan -out=tfplan
```
