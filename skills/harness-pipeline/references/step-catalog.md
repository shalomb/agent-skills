# Harness Step Types Catalog

## Common Step Types

### 1. `ShellScript`
Runs arbitrary shell code on the Harness delegate or container infrastructure.
```yaml
- step:
    type: ShellScript
    name: execute bash script
    identifier: execute_bash_script
    spec:
      shell: Bash
      onDelegate: true
      source:
        type: Inline
        spec:
          script: |-
            #!/bin/bash
            set -euo pipefail
            echo "Running deployment tasks..."
      environmentVariables:
        ENV_NAME: <+pipeline.variables.env>
      outputVariables:
        - name: status_flag
```

### 2. `Run` (Containerized Execution)
Runs commands inside a designated container image.
```yaml
- step:
    type: Run
    name: run python script
    identifier: run_python_script
    spec:
      connectorRef: account.dockerhub
      image: python:3.11-slim
      shell: Bash
      command: |-
        python3 -m pip install requests
        python3 ./deploy.py
```

### 3. `GitClone`
Clones repository content onto the delegate workspace.
```yaml
- step:
    type: GitClone
    name: clone infrastructure repo
    identifier: clone_infra_repo
    spec:
      connectorRef: account.github
      repoName: my-org/infrastructure-repo
      build:
        type: branch
        spec:
          branch: main
```

### 4. `HarnessApproval`
Pauses pipeline execution pending human approval.
```yaml
- step:
    type: HarnessApproval
    name: production approval gate
    identifier: prod_approval_gate
    timeout: 1d
    spec:
      approvalMessage: "Approve deployment to production cluster?"
      includePipelineExecutionHistory: true
      approvers:
        minimumCount: 1
        userGroups:
          - account._project_all_users
```

### 5. `Http`
Executes an HTTP REST request with response assertions.
```yaml
- step:
    type: Http
    name: trigger webhook
    identifier: trigger_webhook
    spec:
      method: POST
      url: https://api.service.com/hooks/deploy
      headers:
        - key: Content-Type
          value: application/json
      assertion: <+httpResponseCode> == 200
```
