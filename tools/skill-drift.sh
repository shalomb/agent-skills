#!/usr/bin/env bash
# skill-drift.sh — detect drift between canonical skills and deployed copies
#
# Usage:
#   ./tools/skill-drift.sh [SKILL_NAME]          # check one skill
#   ./tools/skill-drift.sh                        # check all skills
#   ./tools/skill-drift.sh --summary              # one-line-per-skill drift summary
#   ./tools/skill-drift.sh --diff SKILL COPY_PATH # show unified diff for a skill copy

set -euo pipefail

CANONICAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)/skills"

# All locations where skills may be deployed
# Symlinked farms (.pi/agent/skills, .gemini/skills) are excluded — they
# point back to canonical and are always in sync by definition.
SEARCH_ROOTS=(
  "$HOME/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills"
  "$HOME/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills"
  "$HOME/oneTakeda/gmsgq-dad-10345-fusion-platform-control-tower/.github/skills"
  "$HOME/oneTakeda/terraform-BuildingBlock-Template/.github/skills"
)

# Symlinked locations — always in sync (symlinks point back to canonical)
SYMLINKED_ROOTS=(
  "$HOME/.pi/agent/skills"
  "$HOME/.gemini/skills"
)

# Short label for a deployment path
label() {
  local path="$1"
  echo "$path" \
    | sed "s|$HOME/||" \
    | sed 's|oneTakeda/||' \
    | sed 's|/.github/skills||' \
    | sed 's|/.pi/agent/skills|.pi/skills|' \
    | sed 's|/.gemini/skills|.gemini/skills|'
}

# Compute a content fingerprint for all files in a skill dir.
# Output: sorted "sha256  relative/path" lines (excluding .git, __pycache__, *.pyc)
fingerprint_dir() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  find -L "$dir" -type f \
    ! -path '*/.git/*' \
    ! -path '*/__pycache__/*' \
    ! -name '*.pyc' \
    ! -name '*.pyo' \
    | sort \
    | while read -r f; do
        rel="${f#$dir/}"
        sha256sum "$f" | awk -v r="$rel" '{print $1 "  " r}'
      done
}

# Compare two skill directories; output drift lines
compare_skill() {
  local canonical="${1%/}"   # strip trailing slash (from glob expansion)
  local copy="${2%/}"
  local copy_label="$3"

  local missing=0 added=0 changed=0 identical=0

  # Collect relative file lists
  local files_a files_b
  files_a=$(find -L "$canonical" -type f ! -path '*/.git/*' ! -name '*.pyc' ! -name '*.pyo' \
              | sed "s|$canonical/||" | sort)
  files_b=$(find -L "$copy"      -type f ! -path '*/.git/*' ! -name '*.pyc' ! -name '*.pyo' \
              | sed "s|$copy/||"      | sort)

  missing=$(comm -23 <(echo "$files_a") <(echo "$files_b") | wc -l | tr -d ' ')
  added=$(  comm -13 <(echo "$files_a") <(echo "$files_b") | wc -l | tr -d ' ')

  # Files present in both — compare by sha256
  while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    local sha_a sha_b
    sha_a=$(sha256sum "$canonical/$rel" | awk '{print $1}')
    sha_b=$(sha256sum "$copy/$rel"      | awk '{print $1}')
    if [[ "$sha_a" == "$sha_b" ]]; then
      (( identical++ )) || true
    else
      (( changed++ )) || true
    fi
  done < <(comm -12 <(echo "$files_a") <(echo "$files_b"))

  printf "  %-45s  +%-2s -%-2s ~%-2s ✓%-2s\n" \
    "$copy_label" "$added" "$missing" "$changed" "$identical"
}

# Show a human-readable diff for a specific copy
show_diff() {
  local skill="$1"
  local copy="$2"
  local canonical="$CANONICAL_ROOT/$skill"

  [[ -d "$canonical" ]] || { echo "ERROR: canonical skill '$skill' not found"; exit 1; }
  [[ -d "$copy" ]]      || { echo "ERROR: copy path '$copy' not found"; exit 1; }

  echo "=== Diff: $skill"
  echo "    canonical: $canonical"
  echo "    copy:      $copy"
  echo ""

  # Collect all file paths from both sides
  local all_files
  all_files=$(
    { find -L "$canonical" -type f ! -path '*/.git/*' ! -name '*.pyc' | sed "s|$canonical/||"
      find -L "$copy"      -type f ! -path '*/.git/*' ! -name '*.pyc' | sed "s|$copy/||"
    } | sort -u
  )

  while IFS= read -r rel; do
    local fa="$canonical/$rel"
    local fb="$copy/$rel"

    if [[ ! -f "$fa" ]]; then
      echo "--- ONLY IN COPY: $rel"
      diff /dev/null "$fb" | head -40
      echo ""
    elif [[ ! -f "$fb" ]]; then
      echo "--- MISSING FROM COPY: $rel"
      echo ""
    else
      local sha_a sha_b
      sha_a=$(sha256sum "$fa" | awk '{print $1}')
      sha_b=$(sha256sum "$fb" | awk '{print $1}')
      if [[ "$sha_a" != "$sha_b" ]]; then
        echo "--- CHANGED: $rel"
        diff -u "$fa" "$fb" || true
        echo ""
      fi
    fi
  done <<< "$all_files"
}

# Summary mode: one line per skill showing total drift count across all copies
summary_mode() {
  local filter="${1:-}"
  printf "%-30s  %-45s  %s\n" "SKILL" "COPY" "+added -missing ~changed ✓same"
  printf "%-30s  %-45s  %s\n" "-----" "----" "----------------------------"

  for skill_dir in "$CANONICAL_ROOT"/*/; do
    local skill
    skill=$(basename "$skill_dir")
    [[ -n "$filter" && "$skill" != "$filter" ]] && continue

    local found_any=false
    for root in "${SEARCH_ROOTS[@]}"; do
      local copy="$root/$skill"
      if [[ -d "$copy" ]]; then
        found_any=true
        printf "%-30s" "$skill"
        compare_skill "$skill_dir" "$copy" "$(label "$copy")"
      fi
    done

    if ! $found_any; then
      printf "%-30s  %s\n" "$skill" "(no deployed copies found)"
    fi
  done
}

# --- Main dispatch ---

case "${1:-}" in
  --summary)
    summary_mode "${2:-}"
    ;;
  --diff)
    [[ -n "${2:-}" && -n "${3:-}" ]] || { echo "Usage: $0 --diff SKILL COPY_PATH"; exit 1; }
    show_diff "$2" "$3"
    ;;
  --help|-h)
    grep '^#' "$0" | sed 's/^# *//'
    ;;
  "")
    summary_mode
    ;;
  *)
    # Single skill name — full summary for that skill only
    summary_mode "$1"
    ;;
esac
