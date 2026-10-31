---
name: design-thinking
description: Engage in non-linear design thinking for new ideas or features. Empathizes, defines, ideates, and prototypes to validate constraints before passing structured handoffs (What/Why/Boundaries) to implementation agents. Use when starting a new idea or feature that is still vague, before brainstorming or planning. Triggers include 'design thinking', 'empathize', 'what should we build', 'grill me', '/grill-me'.
---

# Design Thinking (/design)

Use this skill when exploring a new idea, feature, or architecture before committing to an implementation plan. 

**Read the foundational philosophy first:** [principles-and-values.md](references/principles-and-values.md)

## Skill Invocation & Interaction UX (How to act)

When this skill is invoked, you must take control of the session and guide the user through a structured experience. 

1. **The JTBD Intake:** If the user's initial request is vague, do not immediately map the entire tree. Ask a single, high-leverage "seed" question using the Jobs-To-Be-Done framework (e.g., *"What is the specific 'Job' the user is hiring this software to do? What is their current painful workaround?"*). 
2. **Fact-Finding is Your Job:** Never ask the user for information you can discover yourself. If you need to know the current database schema, use your tools to check it. Only ask the user for *decisions*.
3. **High Agency Prototyping:** When you are testing hypotheses, tell the user what you are doing behind the scenes. (e.g., *"I'm going to quickly prototype a Python script to test if the memory footprint holds up. Give me a moment..."*)
4. **Horizon and the Code:** Decide how much authority the current code has before you map the tree. State the stance in the first round as a pre-selected question, so the user can change it.
   - **Long horizon** (new capability, re-architecture, evolutionary architecture): the code is *evidence* of the current state, not authority. Challenge constraints that come only from the code ("scar tissue"). An option can be "change the code".
   - **Mid-execution** (implementing or fixing inside a settled design): the code and the accepted ADRs are the *foundation*. Judge options by how they fit it. To deviate, reopen the node explicitly, and supersede the ADR if one exists.
   - Infer the stance from the request and the repo state (an approved plan or a branch with work in progress means mid-execution). If the signals conflict, recommend long horizon for new scope and mid-execution for in-flight work.
5. **Domain Language (Ubiquitous Language):** Build the glossary as part of the design.
   - Check each term against the glossary. A conflict, or a vague or overloaded term, becomes a frontier question with a proposed term and its rejected synonyms (`_Avoid_`). Do not stop the round to ask about one word.
   - Cross-check claims against the code. Weigh the code according to the stance in item 4.
   - Invent concrete edge-case scenarios to test the boundaries between concepts. A scenario that settles a decision becomes an acceptance scenario (`.feature`), not only conversation.
   - Write a term to the glossary when it settles. Use the glossary rules in [artefact-package.md](references/artefact-package.md). (These habits come from Matt Pocock's `domain-modeling` skill, MIT.)

## The Workflow

This is a non-linear process driven by a breadth-first exploration of a **Design Tree**. You must not go down depth-first rabbit holes.

### 1. Map the Design Tree (Leap of Faith Priorities)
Construct a dependency tree of decisions. What must be decided first before other decisions can be made? Identify the "Frontier"—the set of foundational decisions that have no unresolved prerequisites. 
*Lean UX Rule:* Prioritize the **Leap of Faith Assumptions (LoFAs)**. Technical dependencies matter, but business risk matters more. The riskiest assumptions must form the first Frontier.
*Persist the tree* as a decision-tree document in the repo's design docs and update it after every round. Find the right place first: [artefact-package.md](references/artefact-package.md), "Placement". Each node has a stable id and a state: `open`, `settled`, `deferred`, or `rejected`.

### 2. Breadth-First Exploration of the Frontier
For the current frontier, map both the Problem Space and the Hypothesis Space:
- **Problem Space:** What are the constraints (beware of "scar tissue" biases from legacy code)? What are the anti-goals?
- **Hypothesis Space (Assumption Map):** Shift from proposing "Options" to testing "Hypotheses". Frame them as: *"We believe that [building X] will result in [User Behavior Y]."* What are the unknowns and risks for each hypothesis?

### 3. Diverge, Prune, and Prototype
- Prune the obviously bad hypotheses immediately.
- **Rapid Prototyping (Quick & Dirty):** For the remaining hypotheses, do not debate them endlessly in text. Rapidly build throwaway "scooters" (e.g., a quick script, a rough API endpoint) to validate the assumptions and constraints. 
- *Rule: Prototypes must be completely disposable. Do not over-engineer them.*

### 4. Present the Round (Strict Formatting)
Do not ask questions one by one. Present the entire frontier round at once.

**If the `grill_round` tool is available** (the `/grill-me` command), send the round through it. The user answers in vim and you receive only the delta. Follow [grill-rounds.md](references/grill-rounds.md) for the file format, the `>>` replies, the no-change prompt, and the end-of-session checks.

**Otherwise**, present the round in chat using this exact format:

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
- Recalculate the next layer of the Design Tree (the new Frontier) and repeat from Step 2 until all functional nodes are resolved.

### 6. The Adversarial Stress-Test & Falsifiability Gate (Mandatory Penultimate Round)
Never jump straight from settling functional decisions to the final handoff review. Collaborative convergence breeds confirmation bias. Once the functional frontier is settled, run one dedicated **Well-Architected & Falsifiability Round** (`waf.*` nodes) to shoot holes in the concept across five lenses:
1. **Cost & Latency Ceiling:** Does the proposed orchestration/machinery cost more tokens or latency than the work itself? What can be made deterministic instead of an LLM or network call?
2. **Concurrency & Contention:** Where do parallel pieces collide (shared state, locks, rebase storms, cold-start amplification)?
3. **Partial-Failure Salvage (Blast Radius):** When step $K$ of $N$ fails mid-flight, how is completed work ($1 \dots K-1$) salvaged rather than rolled back?
4. **Cold-Start & Small-$N$ Edge Cases:** Does the design rely on statistical/RL or scale assumptions that fail or overfit at $N=1\text{--}15$?
5. **Blind Spots & Falsifiable Hypotheses:** Bind every core architectural pillar to a **Falsifiable Hypothesis** (`H1..Hn`) with a quantitative pass/kill threshold verified by a Tracer-Bullet Spike before full build-out.

### 7. The Handoff (Extracting the Guardrails via Owner Skills)
When the tree and its `waf.*` stress-test nodes are resolved, generate the inputs required for the implementation agents. **DO NOT** write a monolithic implementation spec dictating "how" to write the code. 

**Just-in-Time Skill Loading (Mandatory Gate):** Do not draft artefacts from memory. Before writing each artefact type for the first time in a session, `read` its owner skill so the output conforms to the canonical structure and anti-pattern gates:
- **ADRs:** Load `architecture-decision-records/SKILL.md` and `references/adr-template.md` *before* writing any ADR (enforce the **Decomposition Gate**: one single architectural decision per ADR, never a compound "God Decision"; include `Decision Drivers`, the 8-row `Y-Statement`, `Domain Quality Framework Alignment`, `Architectural Reification`, and the `Multi-Criteria Comparison Matrix`).
- **Behavioral Specs (`.feature`):** Load `adzic-bdd/SKILL.md` *before* writing Gherkin scenarios (business-readable, declarative, Adzic Index $\ge 7$).
- **Architectural Seams (C4):** Load `c4-architecture/SKILL.md` *before* writing C4 diagrams (`C4Context` / `C4Container` syntax, unidirectional verb-labelled arrows, $\le 20$ elements).

Write the glossary and ADRs as their decisions settle, not only at the end. Use the placement, owner skills, and writing rules in [artefact-package.md](references/artefact-package.md). The handoff is one spec document that links to everything else.

Produce the following artefacts:
1. **Domain Glossary (`GLOSSARY.md`):** Define the ubiquitous language.
2. **Behavioral Specs (BDD/Gherkin):** Define the acceptance criteria (The "What").
3. **Architecture Decision Records (ADRs):** Only for single-focus decisions that pass the ADR test: hard to reverse, surprising without context, and a real trade-off (The "Why"). Split compound choices into separate ADRs.
4. **Architectural Seams:** Define component boundaries (e.g., C4 diagrams).
5. **Anti-Goals:** What the implementation agent should strictly avoid.
6. **Tracer-Bullet Tickets:** Start with falsification spikes for `H1..Hn`, then break the validated design down into actionable slices to populate the backlog.

---
**Terminal State:** The session ends when the handoff artefacts are complete, reviewed by the human, and ready to be fed into an implementation skill. With `/grill-me`, the review is the final review round in [grill-rounds.md](references/grill-rounds.md).
