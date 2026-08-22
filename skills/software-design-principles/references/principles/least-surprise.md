# Principle of Least Surprise (Least Astonishment)

**Tags:** `UX`, `API Design`, `Developer Experience`, `Naming`, `Defaults`
**Related Principles:** [DWIM (Do What I Mean)](dwim.md) — DWIM removes the boilerplate; Least Surprise ensures what remains behaves as expected.

## Context/Problem
When designing APIs, functions, or user interfaces, developers often make decisions that contradict established norms or user expectations (e.g., a getter function that modifies state, or a configuration default that prioritizes edge cases over the common use case). This forces the consumer to deeply inspect documentation or source code rather than relying on their intuition.

## Solution/Pattern
The behavior of a system or component should naturally align with how a reasonable user expects it to behave based on standard conventions. Name functions accurately to their actions, keep interfaces consistent, avoid hidden side-effects, and set predictable defaults.

## Example
A `get_user_data()` function should strictly return data and have zero side-effects on the database state. If an operation mutates state, it should be explicitly named to reflect that mutation (e.g., `fetch_and_update_user_data()`).
