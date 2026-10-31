# AI-Native Design Thinking: A Framework for Agentic Workflows

## 1. Core Values & Principles

*   **Working Prototypes > Perfect Specs (Scooter vs. Bicycle)**
    It is better to have a working scooter than a perfect, unbuilt bicycle. An imperfect bicycle is useless if it never gets built, but a working scooter demonstrates the concept, communicates intent, releases value, and gathers real-world feedback. We explicitly reject the notion of "perfect" monolithic specifications produced by spec-driven design agents. We embrace "good enough," iterative prototypes.
*   **The Collapse of Ideate & Prototype**
    With AI, the cost to prototype and iterate is near zero. The traditional gap between "ideation" (talking) and "prototyping" (building) has diminished. We can afford to produce throwaway prototypes instantly to fail bad options faster rather than debating them in text.
*   **Non-Linear, Emergent Design**
    Good design is inherently iterative and emergent. In complex systems, requirements and constraints inevitably change. Thinking must be non-linear.
*   **The Context Hypothesis & The "Scar Tissue" Bias**
    AI agents possess massive working memory, allowing them to ingest entire repositories upfront. It is acceptable for design agents to lean "waterfall" in gathering context. *However*, this creates a risk of "scar tissue" bias: agents may blindly inherit bad legacy patterns or artificial constraints from the current system. Agents must actively challenge whether constraints are real or historical baggage.
*   **Strict Handoff Boundaries (What/Why, never How)**
    Implementation agents suffer from instruction-following bias. If given the "how," they lose their creative flexibility. The handoff from Design to Implementation must strictly provide the "what" and "why" (behavior, vocabulary, and boundaries), leaving the "how" to the implementation agent.

## 2. Architecture & Artefacts

*   **Context Management:** Use subagents for discovery and summarization to manage massive context effectively without losing critical details.
*   **Living Documentation (Governed by Owner Skills):** Documentation evolves *with* the design process, not at the end of it, and always loads its owner skill before writing rather than drafting from memory.
    *   **Real-time Glossary:** Fuzzy terms are clarified and updated in `GLOSSARY.md` the minute they are redefined (`domain-modeling`).
    *   **Just-in-Time Decisions:** Non-trivial decisions are logged in single-focus ADRs immediately (`architecture-decision-records`, 1 decision per ADR, never a compound "God Decision").
*   **The Handoff Artefacts:** BDD/Gherkin specs (`adzic-bdd`) are the primary "What." However, they aren't enough. The handoff must also include Domain Glossaries, Architectural Boundaries (`c4-architecture`), targeted single-focus ADRs, Falsifiable Hypotheses with kill criteria, and explicit Anti-Goals.
*   **Backend Design Matters:** Design thinking is not just for UI wireframes. It applies equally to backend architecture (e.g., designing an observability stack, choosing metrics, and defining data visualization flows).

## 3. Agent UX & Interaction ("Grilling" the User)

*   **High-Agency Fact Finding:** The agent is explicitly forbidden from asking the user for information it can find itself. It must consult glossaries, ADRs, BDD specs, and git history (using selective double-clicking), or use tools like `codemap` and `ast-grep` to map reality. It only asks the user for *decisions*.
*   **The "Seed" Intake:** When invoked with a vague idea, the agent does not immediately map a massive tree. It asks a single, high-leverage "seed" question to establish the core constraint (e.g., *"Who is the primary user, and what is their pain point?"*).
*   **Transparent Prototyping:** The agent explicitly announces when it goes into High-Agency mode to build a prototype (e.g., *"I'm going to quickly prototype a Python script to test memory footprint. Give me a moment..."*).
*   **Batching the Frontier (No Interrogations):** Avoid slow-pacing, high-latency, one-by-one Q&A. The agent presents the full current set of "frontier" decisions at once. This allows the user to see the big picture, disagree only when necessary, and default to accepting the agent's recommendations.
*   **Scenario Stress-Testing:** The agent actively invents edge cases, failure modes, and anti-goals to ensure the design is robust.
*   **Code vs. Intent Matching:** The agent cross-references what the user wants against what the code actually does, clearly explaining trade-offs, risks, and recommended paths forward.

## 4. The Design Loop (Execution Workflow)

1.  **Map the Design Tree:** Silently construct a dependency tree of decisions.
2.  **Breadth-First Exploration (The Frontier):** Avoid depth-first rabbit holes. Explore the highest unblocked layer broadly.
    *   *Problem Space:* Define constraints, anti-goals, and the core problem.
    *   *Option Space:* Map assumptions, unknowns, options, trade-offs, and risks.
3.  **Diverge, Prune, and Prototype:** Rapidly build "quick and dirty" throwaway prototypes for the remaining options to validate assumptions.
4.  **Present the Round:** The agent presents findings, recommendations, and validated/invalidated assumptions to the human for sign-off.
5.  **Settle and Recalculate:** Lock into a design direction, generate living documentation, and calculate the next layer of the tree.
6.  **Adversarial Self-Falsification (Penultimate Round):** Once functional nodes settle, pivot from co-creator to adversary (`waf.*` round) — challenge cost/latency overhead, concurrency contention, partial-failure salvage, and small-$N$ assumptions, and bind each core bet to a Falsifiable Hypothesis and kill threshold before final handoff.
