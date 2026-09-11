---
name: design-thinking
description: Engage in non-linear design thinking for new ideas or features. Empathizes, defines, ideates, and prototypes to validate constraints before passing structured handoffs (What/Why/Boundaries) to implementation agents.
---

# Design Thinking (/design)

Use this skill when exploring a new idea, feature, or architecture before committing to an implementation plan. 

**Read the foundational philosophy first:** [principles-and-values.md](references/principles-and-values.md)

## The Workflow

This is a non-linear process driven by a breadth-first exploration of a **Design Tree**. You must not go down depth-first rabbit holes (e.g., designing database schemas before validating the need for a database).

### 1. Map the Design Tree
Silently construct a dependency tree of decisions. What must be decided first before other decisions can be made? Identify the "Frontier"—the set of foundational decisions that have no unresolved prerequisites.

### 2. Breadth-First Exploration of the Frontier
For the current frontier, map both the Problem Space and the Option Space:
- **Problem Space Mapping:** 
  - What is the problem? 
  - What are the constraints (beware of "scar tissue" biases from legacy code)? 
  - What are the anti-goals?
- **Option Space Mapping (Assumption Map):** 
  - What are the unknowns and uncertainties?
  - What are the options, trade-offs, and risks?

### 3. Diverge, Prune, and Prototype
- Prune the obvious bad options immediately.
- **Rapid Prototyping (Quick & Dirty):** For the remaining options, do not debate them endlessly in text. Rapidly build throwaway "scooters" (e.g., a quick script, a rough API endpoint) to validate the assumptions and constraints. 
- *Rule: Prototypes must be completely disposable. Do not over-engineer them.*

### 4. Present the Round
Do not ask questions one by one. Present the entire frontier round to the human:
- Explain the findings from your prototypes.
- Provide clear recommendations based on what worked and what failed.
- Explicitly ask the human to validate or invalidate the assumptions and design decisions for this round.

### 5. Settle and Recalculate
- Once the human agrees, those nodes on the Design Tree are "settled."
- Lock into that design direction.
- Recalculate the next layer of the Design Tree (the new Frontier) and repeat from Step 2 until the entire tree is resolved.

### 6. The Handoff (Extracting the Guardrails)
When the tree is fully resolved, generate the inputs required for the implementation agents. **DO NOT** write a monolithic implementation spec dictating "how" to write the code. 

Produce the following artefacts:
1. **Domain Glossary (`CONTEXT.md`):** Define the ubiquitous language.
2. **Behavioral Specs (BDD/Gherkin):** Define the acceptance criteria (The "What").
3. **Architecture Decision Records (ADRs):** Only for immutable, hard-to-reverse trade-offs (The "Why").
4. **Architectural Seams:** Define component boundaries (e.g., C4 diagrams).
5. **Anti-Goals:** What the implementation agent should strictly avoid.

---
**Terminal State:** The session ends when the handoff artefacts are complete, reviewed by the human, and ready to be fed into an implementation skill.
