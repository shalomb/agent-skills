---
description: Critically review code, diffs, or pull requests for bugs, edge cases, and design flaws
---

You are tasked with: Critically review code, diffs, or pull requests for bugs, edge cases, and design flaws.

Follow the instructions in the `bart-adversarial-reviewer` skill:
1. Perform an adversarial code review looking for bugs, edge cases, correctness failures, lazy shortcuts, and pattern violations.
2. Check whether the target repository defines its own review agent via find-repo-agents.sh.
3. Scrutinize tests, verify real failure modes, and evaluate CI results before providing a clear quality assessment and merge decision.

User request:
$ARGUMENTS
