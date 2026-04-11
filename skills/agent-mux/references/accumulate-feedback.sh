#!/bin/bash
# accumulate-feedback.sh — gather all Bart outputs into planning/FEEDBACK.md
#
# Usage: bash accumulate-feedback.sh <planning-feedback-path> <worktree1> [worktree2...]
# Example: bash accumulate-feedback.sh .worktrees/planning/FEEDBACK.md quick-wins cli-ux raw-flag

set -euo pipefail

FEEDBACK_FILE="${1:?Usage: $0 <planning-feedback-path> <worktree1> [worktree2...]}"
shift
WORKTREES=("$@")
GEMINI_TMP="${HOME}/.gemini/tmp"

echo "" >> "$FEEDBACK_FILE"
echo "---" >> "$FEEDBACK_FILE"
echo "# Bart Review Session — $(date '+%Y-%m-%d %H:%M')" >> "$FEEDBACK_FILE"
echo "" >> "$FEEDBACK_FILE"

for wt in "${WORKTREES[@]}"; do
  # gemini writes to ~/.gemini/tmp/<worktree-name>/
  gemini_file=$(ls "${GEMINI_TMP}/${wt}/bart-issues-"*.md 2>/dev/null | head -1 || true)
  # pi writes to /tmp/
  pi_file="/tmp/bart-issues-${wt}.md"

  if [ -n "$gemini_file" ] && [ -s "$gemini_file" ]; then
    echo "  ✓ [gemini] $wt → $gemini_file"
    cat "$gemini_file" >> "$FEEDBACK_FILE"
    echo "" >> "$FEEDBACK_FILE"
  elif [ -f "$pi_file" ] && [ -s "$pi_file" ]; then
    echo "  ✓ [pi] $wt → $pi_file"
    cat "$pi_file" >> "$FEEDBACK_FILE"
    echo "" >> "$FEEDBACK_FILE"
  else
    echo "  - no issues file for: $wt (approved with no observations, or not written)"
  fi
done

echo ""
echo "Accumulated → $FEEDBACK_FILE"
echo "Now triage: critical rejections → update Ralph prompts; systemic → next wave guardrails"
