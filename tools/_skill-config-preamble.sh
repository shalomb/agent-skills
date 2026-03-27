#!/usr/bin/env bash
# _skill-config-preamble.sh
# Source this near the top of any skill script to load layered configuration.
#
# Usage in a script:
#   SKILL_NAME="tfc-api"
#   source "$(dirname "$0")/_skill-config-preamble.sh"
#
# After sourcing, all configured KEY=value pairs are exported.
# Pre-existing environment variables are never overwritten.

# Locate skill-config.sh — search common locations
_find_skill_config() {
  local candidates=(
    # Relative to this script (tools/ sibling to scripts/)
    "$(dirname "$0")/../../../../tools/skill-config.sh"
    "$(dirname "$0")/../../../tools/skill-config.sh"
    # XDG data
    "${XDG_DATA_HOME:-$HOME/.local/share}/agent-skills/tools/skill-config.sh"
    # Well-known install locations
    "$HOME/shalomb/agent-skills/tools/skill-config.sh"
    "$HOME/.local/lib/agent-skills/tools/skill-config.sh"
  )
  for c in "${candidates[@]}"; do
    local resolved
    resolved=$(realpath "$c" 2>/dev/null) || continue
    [[ -f "$resolved" ]] && echo "$resolved" && return 0
  done
  return 1
}

_SKILL_CONFIG_SH=$(_find_skill_config) || {
  # skill-config not found — not fatal, scripts still work via env vars or other means
  return 0 2>/dev/null || true
}

# Load configuration for the skill
# shellcheck disable=SC1090
source "$_SKILL_CONFIG_SH"
skill_config_load "${SKILL_NAME:-}" "${PWD}"
unset _SKILL_CONFIG_SH
