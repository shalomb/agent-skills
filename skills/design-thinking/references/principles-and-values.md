# Design Thinking Principles and Values

This document outlines the core philosophy behind the Design Thinking (DT) skill for AI agents. It bridges the gap between exploration (Are we building the right thing?) and implementation (Are we building the thing right?).

## 1. Non-Linearity of Thinking
Design is not a checklist. It is an interconnected web of modes: Empathize, Define, Ideate, Prototype, and Test. The agent must freely jump between these states—for example, looping back to the "Define" stage if a "Test" proves the initial assumption was wrong.

## 2. Working Prototypes > Perfect Designs (The Scooter vs. Bicycle)
It's better to have a working scooter than a perfect, unbuilt bicycle. We explicitly **reject** the notion of "perfect" specifications and monolithic plans produced by spec-driven design agents. Instead, we embrace "good enough" prototypes that demonstrate the concept, communicate intent, release value, and gather real-world feedback. A prototype can be iterated upon; a perfect 50-page spec document cannot be tested.

## 3. The Collapse of Ideate & Prototype
With AI, the cost of prototyping and iteration is near zero. The space between "ideation" and "prototyping" has collapsed. Instead of spending hours debating options in text, the agent should rapidly generate throwaway prototypes to fail bad options instantly. 

## 4. Iterative and Emergent Design
Good design emerges from contact with reality. In complex systems, requirements and constraints inevitably change over time. The design process must be fundamentally iterative and emergent rather than predictive.

## 5. The Context Hypothesis (Waterfall Context, Agile Execution)
AI agents possess massive, near-perfect working memory, allowing them to ingest entire repositories of history, documentation, and code upfront. 
- **Context Gathering:** It is acceptable to lean "waterfall" in gathering context, as the agent can hold more state than a human.
- **The "Scar Tissue" Bias:** *Warning!* While system empathy is required in brownfield projects, agents are highly susceptible to the "scar tissue" of the current system. They may blindly inherit bad legacy patterns or artificial constraints. The agent must aggressively challenge whether an existing constraint is real or just historical baggage.

## 6. Strict Handoff Boundaries (What and Why, Never How)
Implementation agents are highly susceptible to instruction-following bias. If the design phase dictates *how* to write the code, the implementation agent will blindly follow it, losing its creative problem-solving ability.
The handoff from Design to Implementation must strictly be:
- **The What:** Behavior constraints (BDD / Gherkin specs).
- **The Why:** Immutable constraints and trade-offs (ADRs).
- **The Boundaries:** Ubiquitous language (Domain Glossary / `CONTEXT.md`) and component fences (C4 Models).
- **The Anti-Goals:** Explicitly what *not* to do.

## 7. Backend Design is Still Design Thinking
Design thinking is not just for UI/UX wireframes. Empathizing with an SRE to build an observability stack (e.g., tracing latency bottlenecks) requires the exact same empathy, definition, rapid prototyping, and throwaway testing as designing a frontend workflow.
