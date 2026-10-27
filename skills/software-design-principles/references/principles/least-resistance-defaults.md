# Least-Resistance Defaults

**Tags:** `UX`, `Interaction Design`, `Defaults`, `Human-in-the-Loop`
**Related Principles:** [DWIM](dwim.md) — both act on the user's likely intent; [Principle of Least Surprise](least-surprise.md) — the default must be the expected choice, not a convenient one.

## Context/Problem
A system asks a person to confirm a set of choices. If every choice needs an explicit answer, the person does work even where they agree, so they skim, abandon, or answer at random. If the system silently assumes answers, the person loses control and errors go unnoticed.

## Solution/Pattern
Pre-select the most likely choice for each decision and state why it is recommended. The cheapest action (one key, save and quit, press Enter) accepts all pre-selected choices. The person spends effort only where they disagree or know more.

- An untouched choice means consent. Do not ask again about it.
- A follow-up prompt also puts the most likely next action first, as its default.
- When the response is ambiguous (nothing changed), ask once, with the likely meaning as the default. Do not guess silently.
- Any question or doubt that the person attaches to a choice cancels the consent for that choice.

## Example
In the `/grill-me` design rounds, each question's recommended option is already ticked in the vim round file. `:wq` accepts them all. If the user returns the file unchanged, the extension asks "No answers changed. What next?" and the default is "Accept the recommendations and continue". A `>>` note that asks a question keeps that decision open.
