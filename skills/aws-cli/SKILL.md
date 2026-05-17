---
name: aws-cli
description: AWS CLI safety guardrails and account/role management for AI agents. Read before running any AWS CLI command. Covers environment setup, credential checking, account switching, pagination, and account-guard patterns. Triggers on any aws CLI invocation, account switching, SSO login, or when setting up a shell pane for AWS work.
---

# AWS CLI — Agent Safety Guardrails

## Pre-flight: set before any AWS command

```bash
unset AWS_CLI_AUTO_PROMPT && export AWS_PAGER='' AWS_DEFAULT_OUTPUT=json
```

- `AWS_CLI_AUTO_PROMPT` — interactive autocomplete; blocks non-TTY execution, always unset
- `AWS_PAGER=''` — prevents `less` capturing output; empty string disables entirely
- `AWS_DEFAULT_OUTPUT=json` — machine-readable; override per-command with `--output text` for scalar extraction only

## Identity and credential check

Use `aws-whoami` (not bare `aws sts get-caller-identity`) — it prints all `AWS_*` env vars,
shows active account roles with expiry, and calls `sts get-caller-identity`:

```bash
aws-whoami
```

Key env vars to note after `aws-whoami`:
- `AWS_SSO_PROFILE` — the active profile (`account-alias:RoleName`)
- `AWS_SSO_SESSION_EXPIRATION` — credential expiry (ISO8601); check this before long operations
- `AWS_SSO_ACCOUNT_ID` — current account ID; use to guard against wrong-account operations

**If credentials are expired:** do not retry in a loop. Re-authenticate:
```bash
aws-login [account-alias]         # SSO login for a specific account
aws-login                         # SSO login, infers account from git repo name
```

## List accounts and roles

```bash
aws-sso list                                         # all accounts/roles with expiry
aws-sso list -P AccountAlias=tec-dce-inn-dev        # filter by account alias prefix
aws-sso list -P AccountId=990136964265              # filter by account ID
aws-sso list -s AccountAlias                        # sort by alias
```

Available fields for `-P` filtering / `-s` sorting:
`AccountAlias`, `AccountId`, `AccountIdPad`, `AccountName`, `Arn`, `DefaultRegion`,
`EmailAddress`, `Expires`, `ExpiresEpoch`, `Profile`, `RoleName`, `SSO`, `Via`

The `Profile` column value is what goes into `aws-login` and `AWS_SSO_PROFILE`.

## Switch account or role

```bash
aws-login tec-dce-inn-dev                           # login to account, auto-selects best role
aws-login tec-dce-inn-dev:_TECAdmin-Dev             # login with explicit role suffix
aws-login tec-dce-inn-dev -c                        # login and open AWS console
```

`aws-login` calls `aws-sso eval -p <profile>`, writes credentials to `$AWS_SSO_CACHE`,
then sources them into the shell. After login, `aws-whoami` confirms the active identity.

`aws-sso-profile` resolves the correct profile for an account alias (used internally by
`aws-login`; also useful to check what profile would be selected):
```bash
aws-sso-profile tec-dce-inn-dev
```

## Account guard: verify before destructive operations

Always assert the active account matches expectation before mutations:

```bash
EXPECTED_ACCOUNT=990136964265
ACTUAL_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
[[ "$ACTUAL_ACCOUNT" == "$EXPECTED_ACCOUNT" ]] || { echo "Wrong account: $ACTUAL_ACCOUNT"; exit 1; }
```

`AWS_SSO_ACCOUNT_ID` is also available in the environment after `aws-login` / `aws-whoami`
for a no-API-call check.

## Pagination

Many `list-*` / `describe-*` calls return only the first page by default. Always handle this:

```bash
# Small result sets — disable pagination entirely
aws ec2 describe-instances --no-paginate

# Large result sets — use auto-pagination (awscli v2)
aws ec2 describe-instances --output json   # awscli v2 auto-paginates by default on most commands
```

Silent truncation is a common agent bug — if a result set seems incomplete, add `--no-paginate`
or check for `NextToken` in the response.

## Retry and throttle behaviour

```bash
export AWS_RETRY_MODE=standard    # exponential backoff on throttles (default: legacy)
export AWS_MAX_ATTEMPTS=5         # max retries before giving up (default: varies)
```

Set these alongside the pre-flight block for long-running or high-volume sessions.

## Per-command output patterns

```bash
# Scalar extraction
aws sts get-caller-identity --query Account --output text

# Structured extraction — prefer --query + json
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].{ID:InstanceId,State:State.Name}' \
  --output json

# Table format — human readable, useful in watch loops
aws autoscaling describe-auto-scaling-instances \
  --query 'AutoScalingInstances[?AutoScalingGroupName==`MY-ASG`].{Id:InstanceId,State:LifecycleState,Health:HealthStatus}' \
  --output table
```

## MFA / STS session (legacy accounts)

For accounts using MFA rather than SSO:
```bash
aws-sts-mfa-session login        # prompt for MFA token, cache STS creds
aws-sts-mfa-session test         # verify cached creds still valid
aws-sts-mfa-session refresh      # force token refresh
```

Creds are cached at `$STS_SESSION_CACHE` (default `~/.aws/sts-mfa-session.json`).
To load from file into current shell:
```bash
aws-load-sts-session-from-file ~/.aws/sts-mfa-session.json
```
