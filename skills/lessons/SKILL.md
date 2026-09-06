---
name: lessons
description: Extract software engineering principles, takeaways, and anti-patterns from recent commits or diffs. Short command alias for lessons-learned.
---

# Lessons Learned Retrospective (/lessons)

<!-- generated:alias-skill -->
When invoked, load and execute the **`lessons-learned`** skill:
1. Follow all instructions and guidelines in [`lessons-learned`](../lessons-learned/SKILL.md).
2. Determine analysis scope: feature branch (`git log main..HEAD` + `git diff main...HEAD`), last N commits, or specific SHA.
3. Load core software engineering principles catalog from `references/se-principles.md` and `references/anti-patterns.md`.
4. Extract actionable, grounded software engineering lessons demonstrating what the code changes prove or caution against.
