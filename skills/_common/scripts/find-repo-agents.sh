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
# Searches both agent definitions and repo-local skills:
#   agents: .github,.claude,.gemini/agents/, .agents/agents/, .agents/, docs/agents/
#   skills: .github,.claude,.gemini,.agents/skills/*/SKILL.md (canonical copies skipped)
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

# This collection's own skills — used to ignore deployed copies of them.
CANONICAL_SKILLS="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Role synonyms per persona. Matched case-insensitively against the filename.
case "${PERSONA,,}" in
  bart)    NAMES='bart|review|reviewer|quality|qa|qtest|test|testing|adversarial|audit|compliance|security' ;;
  lisa)    NAMES='lisa|plan|planning|architect|architecture|design|solutions?-architect|platform' ;;
  ralph)   NAMES='ralph|develop|developer|build|builder|implement|refactor|creation|coding|import|migration' ;;
  marge)   NAMES='marge|product|triage|discovery|requirements|feature-research|intake' ;;
  lovejoy) NAMES='lovejoy|release|deploy|ship|publish|changelog|docs?|documentation' ;;
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

# Repo-local skills are as relevant as repo-local agents — a skill named
# bb-quality or review-inline-comments belongs to Bart just as review-agent.md
# does. Match on the containing directory name (skills live in <name>/SKILL.md).
SKILL_DIRS=(
  "$ROOT/.github/skills"
  "$ROOT/.claude/skills"
  "$ROOT/.gemini/skills"
  "$ROOT/.agents/skills"
)

found=0
for d in "${SKILL_DIRS[@]}"; do
  [[ -d "$d" ]] || continue
  while IFS= read -r sk; do
    name="$(basename "$(dirname "$sk")")"
    # Skip deployed copies of canonical skills — they are the same skill, not a
    # repo-specific definition. Compare against this collection's own skills.
    [[ -d "$CANONICAL_SKILLS/$name" ]] && continue
    # Stricter than agent files: require the role word as a whole segment
    # (bb-quality, review-inline-comments) rather than any substring, so
    # a catalogue skill like acme-building-blocks does not read as a "build" agent.
    shopt -s nocasematch
    if [[ "-$name-" =~ [-_](${NAMES})[-_] ]]; then
      echo "$sk"; found=1
    fi
    shopt -u nocasematch
  done < <(find "$d" -maxdepth 2 -type f -name 'SKILL.md' 2>/dev/null | sort)
done

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
