---
name: test-accordion
description: Manage the "Elastic Loop" of development by expanding and contracting test scope. Use when (1) coding in a "Fast-Fail" inner loop (3-5s), (2) graduating to a "Full-Validation" outer loop (2-3m), or (3) performing "Diagnostic Contraction" to a specific Unit Eval after a regression.
---

# Test Accordion: Elastic Loop Management

This skill orchestrates a dynamic, signal-driven control loop where the test "aperture" expands for confidence and contracts for focus.

## 1. Zero-Footprint Mandate (No Cruft)

This skill is **strictly read-only/ephemeral**. 
- **NO Meta-files:** Never create `.ladder.yaml`, `.test-state`, or similar configuration files.
- **NO Markups:** Never modify existing `justfile`, `Makefile`, or source files to add metadata or tags.
- **NO Orchestration State:** Do not persist task progress in the repository. All state must live in the agent's memory or the current session's terminal output.

## 2. Loop Modes (The Accordion)

| Mode | Aperture | Timing | Goal | Command (Typical) |
| :--- | :--- | :--- | :--- | :--- |
| **Inner Loop** | Nucleus + Rungs 0-0.5 | 3-5s | Rapid Feedback | `make fast-fail`, `just test-changed` |
| **Outer Loop** | Full Ladder (0-5.0) | 2-3m | System Integrity | `make test`, `just test` |
| **UAT Loop** | Full Workflow | 3-5m | AWS/Final Validation | `make uat`, `just pr-validation` |

## 2. Semantic Phasing (The Rungs)

When discovering or constructing a ladder, follow this semantic order:
- **Phase 0.0 (Structure):** Syntax validation (blocking).
- **Phase 0.25 (Imports):** Broken symbols/refactoring errors (blocking).
- **Phase 0.35 (Types):** Type checking (often informational/non-blocking).
- **Phase 0.5 (Lint):** Code quality gates (blocking).
- **Phase 1.0 (Regressions):** Last failed (`--lf`) or changed (`--testmon`) tests.
- **Phase 2.0+ (Logic):** Unit -> Integration -> BDD -> E2E.

---

## 3. Workflows

### Progressive Expansion (Forward Path)
1.  **Nucleus Iteration:** Lock into the **Inner Loop**. Run the fastest possible check for your current file (e.g., `pytest path/to/file.py`).
2.  **Inner Graduation:** Once the Nucleus is green, run the **Inner Loop Orchestrator** (e.g., `make fast-fail`).
3.  **Outer Graduation:** Only after the Inner Loop is stable, graduate to the **Outer Loop** (`make test`).
4.  **Recursive Correction:** If Phase 0.5 fails during Outer Graduation, **contract** immediately back to the Inner Loop. Do not attempt to fix logic (Phase 2.0) until the Inner Loop (Phase 0.5) is green.

### Diagnostic Contraction (Inverse Path)
1.  **Global Signal:** Run the **Outer Loop Orchestrator**.
2.  **Diagnostic Map:** Identify the **lowest-level failing phase**.
3.  **Contraction:** Select the specific **Unit Eval** target for that phase (e.g., if Phase 0.25 failed, run `just test-imports`).
4.  **Lock-In:** Fix the failure in the tightest possible loop.
5.  **Re-Expansion:** Step back up the ladder one rung at a time.

---

## 4. Orchestrator Recognition

- **Orchestrator:** A meta-target (e.g., `test`, `fast-fail`) that calls other targets. Use these for **Graduation**.
- **Rung:** A specific, atomic check (e.g., `test-lint`). Use these for **Lock-In** and **Diagnostic Contraction**.

**Economic Tip:** Always prefer targets using `--testmon` or `--lf` for Phase 1.0 to minimize "turn cost."
