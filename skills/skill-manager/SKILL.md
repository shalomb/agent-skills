---
name: skill-manager
description: Discover, audit, update, and organise skills across all agent skill directories. Use when asked to list installed skills, find duplicates or broken symlinks, update a skill with session learnings, promote a project skill to the personal collection, or audit skill health. Triggers on "list skills", "update skill", "skill audit", "promote skill", "skill inventory", "what skills do I have", "sync skills", or "skill health check".
---

# Skill Manager

Higher-order skill that wraps `skill-creator` for new skills and adds
discovery, audit, and update workflows across all skill installation locations.

## Skill topology

Skills live at two levels:

1. **Personal (L1)** — `~/.pi/agent/skills/` (canonical). Other agents symlink here:
   - `~/.claude/skills → ~/.pi/agent/skills`
   - `~/.gemini/skills → ~/.pi/agent/skills`
   - `~/.kiro/skills → ~/.pi/agent/skills`

2. **Project (L2)** — `.github/skills/` in each repo. Scoped to that project.

Personal skills come from multiple sources via symlinks:
- `~/shalomb/agent-skills/skills/` — personal, git-tracked (sharable)
- `~/projects/obra/superpowers/skills/` — obra's superpowers (upstream)
- Local dirs in `~/.pi/agent/skills/` — not symlinked (codemap, _common)

## Workflows

### 1. Inventory

```bash
# Count by source
echo "=== Skill sources ==="
find ~/.pi/agent/skills -maxdepth 1 -type l -exec readlink {} \; | \
  sed 's|/[^/]*$||' | sort | uniq -c | sort -rn

# List local (untracked) skills
find ~/.pi/agent/skills -maxdepth 1 -not -type l -type d | tail -n +2 | \
  xargs -I{} basename {}

# List project skills in current repo
ls .github/skills/ 2>/dev/null
```

### 2. Audit

Check for broken symlinks, missing SKILL.md, or skills not in git:

```bash
# Broken symlinks
find ~/.pi/agent/skills -maxdepth 1 -type l ! -exec test -e {} \; -print

# Missing SKILL.md
for d in ~/.pi/agent/skills/*/; do
  [ -f "$d/SKILL.md" ] || echo "MISSING: $d"
done

# Local skills not in agent-skills repo
for d in ~/.pi/agent/skills/*/; do
  [ -L "$d" ] || echo "UNTRACKED: $(basename $d)"
done
```

### 3. Update a skill from session learnings

When a session reveals new knowledge (gotchas, patterns, workflows):

1. **Identify the skill** — which skill's domain does the learning belong to?
2. **Decide the scope** — does it go in SKILL.md body or a reference file?
   - Core workflow change → SKILL.md
   - Service-specific gotcha → `references/{topic}.md`
   - Cross-reference to another skill → one-liner in References section
3. **Edit and verify** — read the skill-creator SKILL.md for progressive
   disclosure principles. Keep SKILL.md lean (ideally under 100-300 lines).
4. **Commit** — if the skill is in a git-tracked location, use ACP.

Key principle: **add what you fumbled with**. If you had to discover something
through trial and error that wasn't in the skill, that's exactly what should
be added.

### 4. Promote a project skill to personal

When a `.github/skills/` skill is generic enough to share:

```bash
SKILL="terraform-plan-parser"
SOURCE=".github/skills/$SKILL"
TARGET="$HOME/shalomb/agent-skills/skills/$SKILL"

# 1. Copy, stripping org-specific references
cp -r "$SOURCE" "$TARGET"

# 2. Audit for org-specific content
grep -rni "takeda\|oneTakeda\|apms\|your-org" "$TARGET/"

# 3. Replace hardcoded paths with env vars or placeholders
#    e.g. ~/oneTakeda/repo → $REPO_ROOT or {REPO_PATH}

# 4. Symlink from pi skills
ln -sf "$TARGET" "$HOME/.pi/agent/skills/$SKILL"

# 5. Commit to agent-skills repo
cd ~/shalomb/agent-skills && git add "skills/$SKILL" && git commit -m "feat($SKILL): promote from project skills"
```

### 5. Create a new skill

Delegate to `skill-creator`:

```bash
# Read the skill-creator SKILL.md first for full guidance
python3 ~/.pi/agent/skills/skill-creator/scripts/init_skill.py <name> --path ~/shalomb/agent-skills/skills
```

Then symlink: `ln -sf ~/shalomb/agent-skills/skills/<name> ~/.pi/agent/skills/<name>`

## Decision: where does a skill live?

| Criterion | Personal (agent-skills) | Project (.github/skills/) |
|-----------|------------------------|--------------------------|
| Org-specific references (ARNs, team names, internal URLs) | ✗ | ✓ |
| Reusable across orgs | ✓ | ✗ |
| Depends on project codebase layout | ✗ | ✓ |
| Generic tool/workflow (plan parser, git patterns) | ✓ | ✗ |

When in doubt: start in `.github/skills/`, promote later after stripping
org-specific content.

## References

- `skill-creator` skill — SKILL.md structure, progressive disclosure, init/package scripts
- See `references/skill-update-checklist.md` for the post-session update procedure
