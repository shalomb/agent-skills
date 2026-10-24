# Harness JEXL Expression Syntax & Namespaces

Harness uses Java Expression Language (JEXL) enclosed in `<+...>` delimiters for dynamic evaluation at pipeline runtime.

## Common Expression Namespaces

### 1. Pipeline Level (`<+pipeline.*>`)
- `<+pipeline.identifier>`: Identifier of the current pipeline.
- `<+pipeline.name>`: Name of the current pipeline.
- `<+pipeline.sequenceId>`: Monotonically increasing execution sequence ID.
- `<+pipeline.triggeredBy.name>`: User or trigger that initiated execution.
- `<+pipeline.triggeredBy.email>`: Email address of executor.
- `<+pipeline.variables.VAR_NAME>`: Value of custom pipeline variable.

### 2. Project, Org & Account (`<+project.*>`, `<+org.*>`, `<+account.*>`)
- `<+project.identifier>`: Project identifier.
- `<+project.name>`: Project display name.
- `<+org.identifier>`: Organization identifier.
- `<+account.identifier>`: Account identifier.

### 3. Stage & Execution Scopes (`<+stage.*>`, `<+execution.*>`)
- `<+stage.identifier>`: Identifier of the current stage.
- `<+execution.steps.STEP_ID.output.outputVariables.VAR_NAME>`: Output variable produced by a prior step.
- `<+pipeline.stages.STAGE_ID.spec.execution.steps.STEP_ID.output.outputVariables.VAR_NAME>`: Full absolute cross-stage output reference.

### 4. Secrets Resolution (`<+secrets.getValue(...)>`)
- `<+secrets.getValue("secret_identifier")>`: Resolves secret value safely on delegate.
- `<+secrets.getValue("org.secret_identifier")>`: Org-scoped secret.
- `<+secrets.getValue("account.secret_identifier")>`: Account-scoped secret.

### 5. Runtime Inputs (`<+input>`)
- Used in template / pipeline definitions to signify that the value must be provided at execution time or via an Input Set:
  ```yaml
  variables:
    - name: environment
      type: String
      value: <+input>
  ```
