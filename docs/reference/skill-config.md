# Skill Configuration System

Agent skills often need org-specific configuration: API tokens, project IDs, org names,
instance URLs. This system provides **layered XDG-based configuration** that keeps
secrets out of repositories and out of skill definitions.

## Design

Configuration resolves in priority order (highest wins):

```
[0] Environment variables already set in shell       ← always wins
[1] Project-specific skill config                    ← $XDG_CONFIG_HOME/agent-skills/projects/{project}/{skill}.env
[2] Project cross-skill config                       ← $XDG_CONFIG_HOME/agent-skills/projects/{project}/config.env
[3] Global skill defaults                            ← $XDG_CONFIG_HOME/agent-skills/{skill}.env
```

The **project key** is derived automatically from the current working directory's git
repo root, relative to `$HOME`:

```
~/oneTakeda/my-repo/  →  projects/oneTakeda/my-repo/
~/work/api-service/   →  projects/work/api-service/
```

If not in a git repo, `$PWD` relative to `$HOME` is used.

## Directory Layout

```
$XDG_CONFIG_HOME/agent-skills/          # default: ~/.config/agent-skills/
├── github-cli.env                       # global github-cli defaults
├── tfc-api.env                          # global tfc-api defaults
├── harness-idp.env                      # global harness-idp defaults
└── projects/
    └── oneTakeda/
        └── my-repo/
            ├── config.env               # cross-skill: GH_ORG, TFC_ORG, etc.
            ├── github-cli.env           # project-specific github-cli overrides
            └── tfc-api.env              # project-specific tfc-api overrides
```

**All files should be `chmod 600`. Never commit them to any repository.**

## Quick Start

### 1. Scaffold config for the current project

```bash
# From inside your project directory
skill-config --init github-cli
skill-config --init tfc-api
```

This creates the config files with commented-out key templates. Edit them and fill in values.

### 2. See the resolution chain

```bash
skill-config --show github-cli
```

Output:
```
skill-config resolution chain for skill: github-cli
  cwd:         /home/user/oneTakeda/my-repo
  project key: oneTakeda/my-repo

  Config files (low → high priority):
    [global]              ~/.config/agent-skills/github-cli.env              ✓ exists
    [project cross-skill] ~/.config/agent-skills/projects/oneTakeda/my-repo/config.env  ✓ exists
    [project skill]       ~/.config/agent-skills/projects/oneTakeda/my-repo/github-cli.env  ✓ exists
```

### 3. Use in scripts

```bash
#!/usr/bin/env bash
SKILL_NAME="tfc-api"
source "$(dirname "$0")/../../../tools/_skill-config-preamble.sh"

# TFC_ORG, TFC_TOKEN etc. are now available
echo "Using org: ${TFC_ORG:-<not set>}"
```

Or load directly in a shell session:

```bash
source ~/.local/lib/agent-skills/tools/skill-config.sh
skill_config_load tfc-api
echo $TFC_ORG
```

## Config File Format

Files use plain `KEY=value` syntax, bash-compatible:

```bash
# This is a comment
GH_ORG=my-org
GH_PROJECT_ID=PVT_kwDO...

# Quoted values for spaces
TFC_WORKSPACE="my workspace name"
```

## Key Reference by Skill

### `config.env` (cross-skill, project-level)

| Key | Used by | Description |
|-----|---------|-------------|
| `GH_ORG` | github-cli, pr-review, tfc-api | Default GitHub organisation |
| `TFC_ORG` | tfc-api, terraform-dev | Terraform Cloud organisation name |
| `JIRA_PROJECT` | jira, meeting-notes | Default Jira project key |
| `SLACK_WORKSPACE` | meeting-notes | Slack workspace name |

### `github-cli.env`

| Key | Description |
|-----|-------------|
| `GH_ORG` | GitHub org (overrides cross-skill) |
| `GH_PROJECT_ID` | Projects V2 node ID (`PVT_kwDO...`) |
| `GH_PROJECT_NUMBER` | Projects V2 number (integer) |
| `GH_FIELD_STATUS` | Status field ID (`PVTSSF_...`) |
| `GH_FIELD_PRIORITY` | Priority field ID |
| `GH_FIELD_ITERATION` | Iteration field ID (`PVTIF_...`) |
| `GH_STATUS_TODO` | Status option ID for "Todo" |
| `GH_ITER_CURRENT` | Current iteration ID |

See `skills/github-cli/config.env.template` for the full list.

### `tfc-api.env`

| Key | Description |
|-----|-------------|
| `TFC_ORG` | Terraform Cloud org name (overrides cross-skill) |
| `TFC_TOKEN` | API token (prefer `~/.terraform.d/credentials.tfrc.json`) |
| `TFC_WORKSPACE` | Default workspace name |

See `skills/tfc-api/config.env.template` for the full list.

### `harness-idp.env`

| Key | Description |
|-----|-------------|
| `HARNESS_ACCOUNT_ID` | Harness account ID |
| `HARNESS_API_KEY` | Harness API key (secret — chmod 600) |
| `HARNESS_BASE_URL` | Custom base URL (default: `https://app.harness.io`) |

### `targetprocess.env`

| Key | Description |
|-----|-------------|
| `TP_URL` | TargetProcess instance URL |
| `TP_TOKEN` | API token |
| `TP_TEAM_ID` | Default team ID |

## Security

- **Never commit** `.env` files to any repository.
- `skill-config` warns if a config file has permissions wider than `600`.
- Tokens are loaded into the environment for the duration of the shell/script — use
  dedicated short-lived tokens where possible.
- `$XDG_CONFIG_HOME` defaults to `~/.config` if unset. Set it explicitly if you use
  a non-standard location.

## Tool Reference

```
tools/skill-config.sh               # main config loader
tools/_skill-config-preamble.sh     # source this from skill scripts
```

### `skill-config` CLI

```bash
skill-config --show SKILL [CWD]     # show resolution chain
skill-config --init SKILL [CWD]     # scaffold config files
skill-config --project-key [CWD]    # print project key for cwd
skill-config --help                 # show usage
```

### Shell function (after sourcing)

```bash
source skill-config.sh
skill_config_load SKILL [CWD]       # load config into current environment
```
