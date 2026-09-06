---
description: Investigate and resolve bugs systematically with root cause analysis before proposing fixes
---

You are tasked with: Investigate and resolve bugs systematically with root cause analysis before proposing fixes.

Follow the instructions in the `systematic-debugging` skill:
1. Enforce the Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.
2. Follow the 4 Systematic Phases: (1) Root Cause Investigation & reproduction, (2) Pattern Analysis & reference comparison, (3) Single-variable Hypothesis testing, (4) Implementation via TDD regression test.
3. Apply systematic troubleshooting playbooks: backward data-flow tracing (`root-cause-tracing.md`), test pollution isolation (`find-polluter.sh`), condition-based waiting (`condition-based-waiting.md`), and defense-in-depth boundary validation (`defense-in-depth.md`).
4. Adhere to the 3-strike rule: if 3 fix attempts fail, stop immediately and question the architecture.

User request:
$ARGUMENTS
