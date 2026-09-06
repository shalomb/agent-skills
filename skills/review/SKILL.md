---
name: review
description: Critically review code, diffs, or pull requests for bugs, edge cases, and design flaws. Short command alias for bart-adversarial-reviewer.
---

# Bart Adversarial Code Reviewer (/review)

<!-- generated:alias-skill -->
When invoked, load and execute the **`bart-adversarial-reviewer`** skill:
1. Follow all instructions and guidelines in [`bart-adversarial-reviewer`](../bart-adversarial-reviewer/SKILL.md).
2. Perform an adversarial code review looking for bugs, edge cases, correctness failures, lazy shortcuts, and pattern violations.
3. Check whether the target repository defines its own review agent via find-repo-agents.sh.
4. Scrutinize tests, verify real failure modes, and evaluate CI results before providing a clear quality assessment and merge decision.
