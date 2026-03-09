#!/bin/bash
#
# Sync script: ~/.claude/skills → ~/shalomb/agent-skills/
# 
# This script syncs only universal skills that comply with AGENTS.md privacy guidelines.
# Takeda-specific skills are automatically skipped to protect proprietary content.
#
# Usage: ./sync-from-claude.sh
#

set +e  # Don't exit on errors, continue syncing other skills

SOURCE_DIR=~/.claude/skills
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills"
AGENTS_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/AGENTS.md"

# Universal skills (safe to sync - no organization-specific content)
# These skills are reusable across organizations
UNIVERSAL_SKILLS=(
  "adzic-index"
  "bart"
  "copilot-cli"
  "docx"
  "farley-index"
  "github-cli"
  "humanizer"
  "impersonate"
  "lisa"
  "lovejoy"
  "marge"
  "pdf"
  "pptx"
  "ralph"
  "terraform-dev"
  "tmux"
  "xlsx"
)

# Organization-specific skills (require sanitization per AGENTS.md)
# These must be manually reviewed and sanitized before syncing
ORGANIZATION_SPECIFIC_SKILLS=(
  "bb-patch"
  "bb-quality"
  "kedb"
  "mode1-cloud-request"
  "takeda-building-blocks"
  "tfc-api"
)

echo "╭─────────────────────────────────────────────────────╮"
echo "│ AGENT SKILLS SYNC                                   │"
echo "│ Source: ~/.claude/skills/                           │"
echo "│ Target: ~/shalomb/agent-skills/skills/              │"
echo "╰─────────────────────────────────────────────────────╯"
echo ""

# Verify source exists
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "❌ ERROR: Source directory not found: $SOURCE_DIR"
  exit 1
fi

# Verify AGENTS.md exists
if [[ ! -f "$AGENTS_FILE" ]]; then
  echo "❌ ERROR: AGENTS.md not found at $AGENTS_FILE"
  echo "   This file contains privacy guidelines. Aborting sync."
  exit 1
fi

echo "✅ Verified: AGENTS.md privacy guidelines will be respected"
echo ""

echo "📦 SYNCING UNIVERSAL SKILLS (${#UNIVERSAL_SKILLS[@]} total)"
echo "───────────────────────────────────────────────────────"

synced=0
uptodate=0
failed=0

for skill in "${UNIVERSAL_SKILLS[@]}"; do
  source_skill="$SOURCE_DIR/$skill"
  target_skill="$TARGET_DIR/$skill"
  
  if [[ ! -d "$source_skill" ]]; then
    echo "⚠️  SKIP: $skill (not found in source)"
    continue
  fi
  
  # Use rsync with checksums to detect real changes
  if rsync -av --checksum --delete "$source_skill/" "$target_skill/" > /tmp/rsync-$skill.log 2>&1; then
    if grep -q "SKILL.md" /tmp/rsync-$skill.log; then
      echo "✅ SYNCED: $skill"
      ((synced++))
    else
      echo "✓ UP-TO-DATE: $skill"
      ((uptodate++))
    fi
  else
    echo "❌ FAILED: $skill (rsync error)"
    ((failed++))
  fi
done

echo ""
echo "⏭️  SKIPPING ORGANIZATION-SPECIFIC SKILLS (${#ORGANIZATION_SPECIFIC_SKILLS[@]} total)"
echo "────────────────────────────────────────────────────────────────────"
echo ""
echo "Per AGENTS.md guidelines, the following skills require sanitization:"
echo "- Remove hardcoded credentials, API keys, and tokens"
echo "- Replace organization names with placeholders: {ORGANIZATION}, {WORKSPACE}"
echo "- Remove internal URLs and resource IDs"
echo ""

for skill in "${ORGANIZATION_SPECIFIC_SKILLS[@]}"; do
  source_skill="$SOURCE_DIR/$skill"
  
  if [[ -d "$source_skill" ]]; then
    echo "⊘ $skill"
  fi
done

echo ""
echo "╭─────────────────────────────────────────────────────╮"
echo "│ SYNC COMPLETE                                       │"
echo "╰─────────────────────────────────────────────────────╯"
echo ""
echo "📊 SUMMARY:"
echo "  ✅ Synced:      $synced"
echo "  ✓ Up-to-date:   $uptodate"
echo "  ❌ Failed:      $failed"
echo "  ⊘ Skipped:     ${#ORGANIZATION_SPECIFIC_SKILLS[@]} (organization-specific)"
echo ""

if [[ $failed -gt 0 ]]; then
  echo "⚠️  Some syncs failed. Check /tmp/rsync-*.log for details."
  exit 1
fi

echo "✅ Sync completed successfully!"
exit 0
