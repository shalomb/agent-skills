# Send the Delta, Not the Document

**Tags:** `Efficiency`, `Architecture`, `Human-in-the-Loop`, `Token Economy`
**Related Principles:** [Commensurate Scaling](commensurate-scaling.md) — cost grows with the change, not with the size of the artefact; [Least-Resistance Defaults](least-resistance-defaults.md) — unchanged parts mean consent, so only changes need attention.

## Context/Problem
A producer sends a document to a reviewer and gets it back with edits. If the producer reads the full document again to find the changes, the cost is proportional to the document size on every round, and the changes are easy to miss among unchanged content.

## Solution/Pattern
The producer already knows the original. A cheap, deterministic layer between producer and reviewer computes the difference and sends only that, anchored to stable identifiers in the original (an id plus a short quote of the line). The full returned document is kept as the record, but nobody re-reads it to act on it.

- Normalise before diffing: ignore whitespace, instructions, and other trivial changes.
- Attach each addition to the nearest original anchor, so free-form comments keep their context.
- Collapse unchanged sections into one summary line.
- An empty delta is a signal in its own right. Handle it explicitly.

## Example
In the `/grill-me` design rounds, the extension diffs the returned vim file against the round it wrote and sends the model about 550 bytes instead of the 2.6 KB file: `Q2 sync.scope: pick=C (was A)` plus each `>>` note tied to the question and line it was written under. The model already has the questions in its context from the `grill_round` tool call.
