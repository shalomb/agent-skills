#!/usr/bin/env bash
# skill-config — XDG-based layered config loader for agent skills
#
# Resolves skill configuration in priority order:
#   1. Environment variables already set (highest — never overridden)
#   2. Project shadow config: $XDG_CONFIG_HOME/agent-skills/projects/{rel-path}/{skill}.env
#   3. Global skill config:   $XDG_CONFIG_HOME/agent-skills/{skill}.env
#   4. Unset / caller handles missing values
#
# Usage (source into your script):
#   source "$(skill-config --locate)" && skill_config_load github-cli
#
# Or as a one-liner in scripts:
#   eval "$(skill-config github-cli)"
#
# Or to just print the resolved config file paths (for debugging):
#   skill-config --show github-cli
#
# Config file format: KEY=value pairs, one per line, bash-compatible.
# Lines starting with # are comments. Blank lines ignored.
# Values with spaces must be quoted: KEY="value with spaces"
#
# Directory layout:
#
#   $XDG_CONFIG_HOME/agent-skills/
#   ├── github-cli.env            # global defaults for github-cli skill
#   ├── tfc-api.env               # global defaults for tfc-api skill
#   ├── harness-idp.env           # global defaults for harness-idp skill
#   └── projects/
#       └── oneTakeda/
#           └── my-repo/
#               ├── github-cli.env   # project-specific github-cli overrides
#               ├── tfc-api.env      # project-specific tfc-api overrides
#               └── config.env       # cross-skill project config (GH_ORG, etc.)
#
# The project key is derived from the git repo root (or $PWD) relative to $HOME.
# Example: ~/oneTakeda/my-repo → projects/oneTakeda/my-repo/
#
# Secrets note: these files should be chmod 600. skill-config warns if they are not.
# Do NOT commit these files to any repository.

set -euo pipefail

XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
SKILL_CONFIG_DIR="$XDG_CONFIG_HOME/agent-skills"

# ---------------------------------------------------------------------------
# Internal: resolve the project key from the current working directory.
# Returns a relative path like "oneTakeda/my-repo" or "" if not in a git repo.
# ---------------------------------------------------------------------------
_skill_config_project_key() {
  local cwd="${1:-$PWD}"
  local repo_root

  # Try git first
  if repo_root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null); then
    # Make relative to $HOME
    local rel="${repo_root#$HOME/}"
    if [[ "$rel" != "$repo_root" ]]; then
      echo "$rel"
      return 0
    fi
    # Absolute path outside HOME — use it as-is, stripping leading /
    echo "${repo_root#/}"
    return 0
  fi

  # Fall back to $PWD relative to HOME
  local rel="${cwd#$HOME/}"
  if [[ "$rel" != "$cwd" ]]; then
    echo "$rel"
    return 0
  fi

  echo ""
}

# ---------------------------------------------------------------------------
# Internal: source a config file unconditionally (later callers overwrite).
# ---------------------------------------------------------------------------
_skill_config_source_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0

  # Warn if permissions are too open
  local perms
  perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%OLp" "$file" 2>/dev/null || echo "")
  if [[ -n "$perms" && "$perms" != "600" && "$perms" != "400" ]]; then
    echo "⚠️  skill-config: $file has permissions $perms (recommend: chmod 600 $file)" >&2
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    # shellcheck disable=SC1090
    eval "export $line" 2>/dev/null || true
  done < "$file"
}

# ---------------------------------------------------------------------------
# skill_config_load SKILL [CWD]
#   Sources config for SKILL in priority order:
#     env (pre-existing) > project skill > project cross > global
#
#   Strategy: snapshot pre-existing env vars, load files low→high so later
#   files naturally overwrite earlier ones, then restore the snapshot so
#   pre-existing env vars always win.
# ---------------------------------------------------------------------------
skill_config_load() {
  local skill="$1"
  local cwd="${2:-$PWD}"

  local project_key
  project_key=$(_skill_config_project_key "$cwd")

  # Snapshot all KEY=VALUE pairs currently in env (these will be restored at end)
  local -A _env_snapshot=()
  while IFS='=' read -r k v; do
    _env_snapshot["$k"]="$v"
  done < <(env | grep -E '^[A-Z_][A-Z0-9_]*=')

  # Load files lowest → highest priority (each overwrites previous)

  # Layer 3 (lowest): global skill defaults
  _skill_config_source_file "$SKILL_CONFIG_DIR/${skill}.env"

  # Layer 2: cross-skill project config (shared ORG, WORKSPACE, etc.)
  if [[ -n "$project_key" ]]; then
    _skill_config_source_file "$SKILL_CONFIG_DIR/projects/${project_key}/config.env"
  fi

  # Layer 1: project-specific skill config (highest from files)
  if [[ -n "$project_key" ]]; then
    _skill_config_source_file "$SKILL_CONFIG_DIR/projects/${project_key}/${skill}.env"
  fi

  # Layer 0: restore pre-existing env vars (they always win over any file)
  for k in "${!_env_snapshot[@]}"; do
    export "$k=${_env_snapshot[$k]}"
  done
}

# ---------------------------------------------------------------------------
# skill_config_show SKILL [CWD]
#   Print the resolved config file chain (for debugging).
# ---------------------------------------------------------------------------
skill_config_show() {
  local skill="$1"
  local cwd="${2:-$PWD}"

  local project_key
  project_key=$(_skill_config_project_key "$cwd")

  echo "skill-config resolution chain for skill: $skill"
  echo "  cwd:          $cwd"
  echo "  project key:  ${project_key:-(none — not in a git repo under \$HOME)}"
  echo ""
  echo "  Config files (low → high priority):"

  local f1="$SKILL_CONFIG_DIR/${skill}.env"
  local status1="✗ missing"
  [[ -f "$f1" ]] && status1="✓ exists"
  printf "    [global]   %-60s  %s\n" "$f1" "$status1"

  if [[ -n "$project_key" ]]; then
    local f2="$SKILL_CONFIG_DIR/projects/${project_key}/config.env"
    local status2="✗ missing"
    [[ -f "$f2" ]] && status2="✓ exists"
    printf "    [project cross-skill] %-45s  %s\n" "$f2" "$status2"

    local f3="$SKILL_CONFIG_DIR/projects/${project_key}/${skill}.env"
    local status3="✗ missing"
    [[ -f "$f3" ]] && status3="✓ exists"
    printf "    [project skill] %-49s  %s\n" "$f3" "$status3"
  fi

  echo ""
  echo "  Environment vars (highest priority — override all files):"
  echo "    Already-set env vars take precedence over any config file."
}

# ---------------------------------------------------------------------------
# skill_config_init SKILL [CWD]
#   Scaffold empty config files with commented-out key templates.
#   Templates are read from the skill's own config-template files if present,
#   otherwise a minimal stub is created.
# ---------------------------------------------------------------------------
skill_config_init() {
  local skill="$1"
  local cwd="${2:-$PWD}"

  local project_key
  project_key=$(_skill_config_project_key "$cwd")

  local global_file="$SKILL_CONFIG_DIR/${skill}.env"
  local project_file=""
  local cross_file=""

  if [[ -n "$project_key" ]]; then
    project_file="$SKILL_CONFIG_DIR/projects/${project_key}/${skill}.env"
    cross_file="$SKILL_CONFIG_DIR/projects/${project_key}/config.env"
  fi

  # Find skill directory to get template
  local skill_dir=""
  for candidate in \
    "$(dirname "$0")/../skills/${skill}" \
    "$HOME/shalomb/agent-skills/skills/${skill}" \
    "$XDG_DATA_HOME/agent-skills/skills/${skill}" \
    "$HOME/.local/share/agent-skills/skills/${skill}"; do
    if [[ -d "$candidate" ]]; then
      skill_dir="$candidate"
      break
    fi
  done

  local template=""
  if [[ -n "$skill_dir" && -f "$skill_dir/config.env.template" ]]; then
    template="$skill_dir/config.env.template"
  fi

  _skill_config_scaffold "$global_file" "$skill" "global" "$template"

  if [[ -n "$project_file" ]]; then
    _skill_config_scaffold "$cross_file" "" "cross-skill project ($project_key)" ""
    _skill_config_scaffold "$project_file" "$skill" "project ($project_key)" "$template"
  fi

  echo ""
  echo "✅ Config files scaffolded. Edit them, then chmod 600."
  echo "   Run: skill-config --show $skill   to verify resolution."
}

_skill_config_scaffold() {
  local file="$1"
  local skill="$2"
  local layer="$3"
  local template="$4"

  if [[ -f "$file" ]]; then
    echo "  ✓ already exists: $file"
    return 0
  fi

  mkdir -p "$(dirname "$file")"

  {
    echo "# agent-skills config — ${layer}${skill:+ / $skill}"
    echo "# Layer: ${layer}"
    echo "# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# Format: KEY=value  (bash-compatible, one per line)"
    echo "# chmod 600 this file — do NOT commit to any repository"
    echo ""
    if [[ -n "$template" && -f "$template" ]]; then
      cat "$template"
    else
      _skill_config_default_template "$skill"
    fi
  } > "$file"

  chmod 600 "$file"
  echo "  + created: $file"
}

_skill_config_default_template() {
  local skill="$1"
  case "$skill" in
    github-cli)
      cat << 'EOF'
# GitHub org (default for operations when not inferred from git remote)
#GH_ORG=your-org

# GitHub Projects V2
# Run: gh api graphql -f query='{ organization(login: "$GH_ORG") { projectsV2(first:10) { nodes { id title number } } } }'
#GH_PROJECT_ID=PVT_kwDO...
#GH_PROJECT_NUMBER=0
#GH_PROJECT_URL=https://github.com/orgs/your-org/projects/0

# Field IDs (stable — query once per project setup)
# Run: gh api graphql -f query='{ node(id:"$GH_PROJECT_ID") { ... on ProjectV2 { fields(first:20) { nodes { ... on ProjectV2FieldCommon { id name } } } } } }'
#GH_FIELD_STATUS=PVTSSF_...
#GH_FIELD_PRIORITY=PVTSSF_...
#GH_FIELD_SIZE=PVTSSF_...
#GH_FIELD_ITERATION=PVTIF_...

# Status option IDs (single-select)
#GH_STATUS_TODO=
#GH_STATUS_IN_PROGRESS=
#GH_STATUS_DONE=
#GH_STATUS_BACKLOG=
#GH_STATUS_BLOCKED=
EOF
      ;;
    tfc-api)
      cat << 'EOF'
# Terraform Cloud organisation name
#TFC_ORG=your-tfc-org

# TFC token — prefer reading from ~/.terraform.d/credentials.tfrc.json
# Only set here if you cannot use the credentials file
#TFC_TOKEN=

# Default workspace (optional — most scripts take workspace as argument)
#TFC_WORKSPACE=
EOF
      ;;
    harness-idp)
      cat << 'EOF'
# Harness account ID
#HARNESS_ACCOUNT_ID=

# Harness API key — keep secret, chmod 600 this file
#HARNESS_API_KEY=

# Optional: custom Harness base URL (default: https://app.harness.io)
#HARNESS_BASE_URL=
EOF
      ;;
    targetprocess)
      cat << 'EOF'
# TargetProcess instance URL
#TP_URL=https://your-org.tpondemand.com

# TargetProcess API token
#TP_TOKEN=

# Default team ID (optional)
#TP_TEAM_ID=
EOF
      ;;
    jira)
      cat << 'EOF'
# Jira instance URL
#JIRA_URL=https://your-org.atlassian.net

# Jira project key (default project for operations)
#JIRA_PROJECT=

# Jira token (if not using CLI auth)
#JIRA_TOKEN=
EOF
      ;;
    "")
      # Cross-skill project config
      cat << 'EOF'
# Cross-skill project configuration
# Values here apply to ALL skills for this project unless overridden
# in a skill-specific .env file.

# GitHub org (used by github-cli, pr-review, tfc-api VCS validation)
#GH_ORG=

# Terraform Cloud org (used by tfc-api, terraform-dev)
#TFC_ORG=

# Jira project prefix (used by meeting-notes, jira skill)
#JIRA_PROJECT=

# Slack workspace (used by meeting-notes)
#SLACK_WORKSPACE=
EOF
      ;;
    *)
      echo "# Add KEY=value pairs for $skill configuration"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# CLI dispatch — only runs when executed directly, not when sourced
# ---------------------------------------------------------------------------
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  case "${1:-}" in
    --show|-s)
      skill_config_show "${2:-}" "${3:-$PWD}"
      ;;
    --init|-i)
      skill_config_init "${2:-}" "${3:-$PWD}"
      ;;
    --locate)
      echo "${BASH_SOURCE[0]}"
      ;;
    --project-key)
      _skill_config_project_key "${2:-$PWD}"
      ;;
    --help|-h)
      grep '^#' "$0" | head -30 | sed 's/^# *//'
      ;;
    "")
      echo "Usage: skill-config [--show|--init|--project-key|--help] SKILL [CWD]"
      echo "       source skill-config && skill_config_load SKILL"
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
fi
