#!/usr/bin/env bash
# find-repo-agents.sh — discover repo-local agent definitions belonging to a persona.
#
# Personas (Lisa/Marge/Ralph/Bart/Lovejoy) ship a generic definition, but a repo
# may define its own. Repo-local definitions are more specific and should win.
#
# Usage:
#   find-repo-agents.sh <persona> [repo_root]
#
#   persona:   bart | lisa | ralph | marge | lovejoy
#   repo_root: defaults to the current git repo root, else $PWD
#
# Searches: .github/agents/, .claude/agents/, .gemini/agents/, .agents/agents/,
#           .agents/, docs/agents/
#
# Prints matching file paths, one per line. Exit 0 with no output = none found.

set -uo pipefail

PERSONA="${1:-}"
if [[ -z "$PERSONA" ]]; then
  echo "usage: $(basename "$0") <bart|lisa|ralph|marge|lovejoy> [repo_root]" >&2
  exit 2
fi

ROOT="${2:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
[[ -d "$ROOT" ]] || { echo "not a directory: $ROOT" >&2; exit 2; }

# Role synonyms per persona. Matched case-insensitively against the filename.
case "${PERSONA,,}" in
  bart)    NAMES='bart|review|reviewer|quality|qa|qtest|test|testing|adversarial|audit' ;;
  lisa)    NAMES='lisa|plan|planning|architect|architecture|design|solutions?-architect' ;;
  ralph)   NAMES='ralph|develop|developer|build|builder|implement|refactor|creation|coding' ;;
  marge)   NAMES='marge|product|triage|discovery|requirements|feature-research|intake' ;;
  lovejoy) NAMES='lovejoy|release|deploy|ship|publish|changelog' ;;
  *) echo "unknown persona: $PERSONA" >&2; exit 2 ;;
esac

DIRS=(
  "$ROOT/.github/agents"
  "$ROOT/.claude/agents"
  "$ROOT/.gemini/agents"
  "$ROOT/.agents/agents"
  "$ROOT/.agents"
  "$ROOT/docs/agents"
)

found=0
for d in "${DIRS[@]}"; do
  [[ -d "$d" ]] || continue
  while IFS= read -r f; do
    base="$(basename "$f")"
    # Skip READMEs, templates and defaults anywhere in the name — not definitions.
    shopt -s nocasematch
    if [[ "$base" =~ (^|[-_.])(README|TEMPLATE|DEFAULT|EXAMPLE)([-_.]|\.md$) ]]; then
      shopt -u nocasematch; continue
    fi
    shopt -u nocasematch
    if [[ "${base,,}" =~ ${NAMES} ]]; then
      echo "$f"
      found=1
    fi
  done < <(find "$d" -maxdepth 2 -type f -name '*.md' 2>/dev/null | sort)
done

exit 0
