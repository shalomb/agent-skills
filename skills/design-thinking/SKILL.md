---
name: design-thinking
description: Engage in non-linear design thinking for new ideas or features. Empathizes, defines, ideates, and prototypes to validate constraints before passing structured handoffs (What/Why/Boundaries) to implementation agents.
---

# Design Thinking (/design)

Use this skill when exploring a new idea, feature, or architecture before committing to an implementation plan.

**Read the foundational philosophy first:** [principles-and-values.md](references/principles-and-values.md)

## The Workflow

This is a non-linear process. You may jump between these modes based on what is discovered.

### 1. System Empathy (Context Discovery)
- **If Greenfield:** Define the user (who are we building this for, including backend users like SREs) and their pain points.
- **If Brownfield:** Explore the existing codebase (`codemap`, `ast-grep`). Read `CONTEXT.md` and `docs/adr/`. Understand the tribal knowledge via git history.
  - If it id not clear, use the greenfield approach to understand the user and their pain points.

### 2. Define & Ideate
- Synthesize the findings into a clear problem statement.
- Propose wildly different approaches (e.g., CLI vs UI vs Cron).
- Challenge existing assumptions.

### 3. Frictionless Prototyping
- Write minimal, throwaway code (a quick script, a single HTML file, or a spike branch) to prove viability.
- **Rule:** Prototypes are for learning, not for production. They must be discarded after validation.

### 4. The Handoff (Extracting the Guardrails)
When the prototype proves viable, generate the inputs required for the implementation agents. **DO NOT** write a monolithic implementation spec dictating "how" to write the code.

Produce the following artefacts:
1. **Domain Glossary (`CONTEXT.md`):** Define the ubiquitous language.
2. **Behavioral Specs (BDD/Gherkin):** Define the acceptance criteria (The "What").
3. **Architecture Decision Records (ADRs):** Only for immutable, hard-to-reverse trade-offs (The "Why").
4. **Architectural Seams:** (e.g., C4 diagrams) to define component boundaries.
5. **Anti-Goals:** What the implementation agent should strictly avoid.

---
**Terminal State:** The session ends when the handoff artefacts are complete, reviewed by the human, and ready to be fed into an implementation skill (like `subagent-driven-development` or `test-driven-development`).
