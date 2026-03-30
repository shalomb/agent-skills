# Post-Session Skill Update Checklist

Run through this after any session that involved non-trivial tool use,
debugging, or discovery of undocumented behaviour.

## 1. Identify learnings

```
□ What did I fumble with before finding the right approach?
□ What tool flags / API patterns / config options weren't documented?
□ What cross-skill workflows emerged (skill A output → skill B input)?
□ Were there provider/SDK gotchas worth capturing?
```

## 2. Map to skills

For each learning, determine:

```
□ Which skill's domain does this belong to?
□ Does it go in SKILL.md body (core workflow) or references/ (deep-dive)?
□ Is it a new cross-reference between skills (one-liner in References)?
□ Does it warrant a new skill entirely?
```

## 3. Apply progressive disclosure

Before editing, check:

```
□ Is SKILL.md still under 500 lines after the addition?
□ Does the new content justify its token cost?
□ Would a reference file be more appropriate (loaded only when needed)?
□ Am I duplicating content already in another skill?
```

## 4. Edit and commit

```
□ Use mktemp for temp file paths (not hardcoded /tmp)
□ Strip org-specific references if skill is in agent-skills (personal)
□ Keep examples concrete — prefer code over prose
□ Commit with ACP: one logical change per commit
```

## 5. Verify symlinks

After editing skills in `~/shalomb/agent-skills/skills/`:

```bash
# Confirm pi picks up the change
diff <(cat ~/.pi/agent/skills/{skill}/SKILL.md) \
     <(cat ~/shalomb/agent-skills/skills/{skill}/SKILL.md)
# Should show no diff (symlinked)
```

After promoting a project skill:

```bash
# Confirm symlink exists and resolves
readlink -f ~/.pi/agent/skills/{skill}/SKILL.md
# Should point to ~/shalomb/agent-skills/skills/{skill}/SKILL.md
```
