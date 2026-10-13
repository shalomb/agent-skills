---
name: design-thinking
description: Engage in non-linear design thinking for new ideas or features. Empathizes, defines, ideates, and prototypes to validate constraints before passing structured handoffs (What/Why/Boundaries) to implementation agents. Use when starting a new idea or feature that is still vague, before brainstorming or planning. Triggers include 'design thinking', 'empathize', 'what should we build'.
---

# Design Thinking (/design)

Use this skill when exploring a new idea, feature, or architecture before committing to an implementation plan. 

**Read the foundational philosophy first:** [principles-and-values.md](references/principles-and-values.md)

## Skill Invocation & Interaction UX (How to act)

When this skill is invoked, you must take control of the session and guide the user through a structured experience. 

1. **The JTBD Intake:** If the user's initial request is vague, do not immediately map the entire tree. Ask a single, high-leverage "seed" question using the Jobs-To-Be-Done framework (e.g., *"What is the specific 'Job' the user is hiring this software to do? What is their current painful workaround?"*). 
2. **Fact-Finding is Your Job:** Never ask the user for information you can discover yourself. If you need to know the current database schema, use your tools to check it. Only ask the user for *decisions*.
3. **High Agency Prototyping:** When you are testing hypotheses, tell the user what you are doing behind the scenes. (e.g., *"I'm going to quickly prototype a Python script to test if the memory footprint holds up. Give me a moment..."*)

## The Workflow

This is a non-linear process driven by a breadth-first exploration of a **Design Tree**. You must not go down depth-first rabbit holes.

### 1. Map the Design Tree (Leap of Faith Priorities)
Silently construct a dependency tree of decisions. What must be decided first before other decisions can be made? Identify the "Frontier"—the set of foundational decisions that have no unresolved prerequisites. 
*Lean UX Rule:* Prioritize the **Leap of Faith Assumptions (LoFAs)**. Technical dependencies matter, but business risk matters more. The riskiest assumptions must form the first Frontier.

### 2. Breadth-First Exploration of the Frontier
For the current frontier, map both the Problem Space and the Hypothesis Space:
- **Problem Space:** What are the constraints (beware of "scar tissue" biases from legacy code)? What are the anti-goals?
- **Hypothesis Space (Assumption Map):** Shift from proposing "Options" to testing "Hypotheses". Frame them as: *"We believe that [building X] will result in [User Behavior Y]."* What are the unknowns and risks for each hypothesis?

### 3. Diverge, Prune, and Prototype
- Prune the obviously bad hypotheses immediately.
- **Rapid Prototyping (Quick & Dirty):** For the remaining hypotheses, do not debate them endlessly in text. Rapidly build throwaway "scooters" (e.g., a quick script, a rough API endpoint) to validate the assumptions and constraints. 
- *Rule: Prototypes must be completely disposable. Do not over-engineer them.*

### 4. Present the Round (Strict Formatting)
Do not ask questions one by one. Present the entire frontier round to the human using this exact format:

```markdown
### Design Round: [Name of the current Frontier, e.g., Core Architecture]

*I have mapped the Problem Space and run [X] prototypes to test our hypotheses.*

❓ **Decision 1** - **<title>**: <Context based on prototypes. What were the hypotheses? What worked and what failed?>
➡️ **Recommendation:** <Your recommended path forward and why>

---

❓ **Decision 2** - **<title>**: <Context...>
➡️ **Recommendation:** <Your recommended path>

**Are you happy to settle these decisions, or should we pivot?**
```

### 5. Settle and Define Success (Outcomes over Output)
- Once the human agrees, those nodes on the Design Tree are "settled."
- **Define the Metric:** Before locking in, briefly validate how success will be measured. (*"How will we know this feature is successful in production? What is the telemetry or metric we are watching?"*)
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
6. **Tracer-Bullet Tickets:** Break the validated design down into actionable User Stories or tickets to populate the backlog, ensuring value is delivered in chunks.

---
**Terminal State:** The session ends when the handoff artefacts are complete, reviewed by the human, and ready to be fed into an implementation skill.
