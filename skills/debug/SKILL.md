---
name: debug
description: Investigate and resolve bugs systematically with root cause analysis before proposing fixes. Short command alias for systematic-debugging.
---

# Systematic Debugging (/debug)

<!-- generated:alias-skill -->
When invoked, load and execute the **`systematic-debugging`** skill:
1. Follow all instructions and guidelines in [`systematic-debugging`](../systematic-debugging/SKILL.md).
2. Enforce the Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.
3. Follow the 4 Systematic Phases: (1) Root Cause Investigation & reproduction, (2) Pattern Analysis & reference comparison, (3) Single-variable Hypothesis testing, (4) Implementation via TDD regression test.
4. Apply systematic troubleshooting playbooks: backward data-flow tracing (`root-cause-tracing.md`), test pollution isolation (`find-polluter.sh`), condition-based waiting (`condition-based-waiting.md`), and defense-in-depth boundary validation (`defense-in-depth.md`).
5. Adhere to the 3-strike rule: if 3 fix attempts fail, stop immediately and question the architecture.
