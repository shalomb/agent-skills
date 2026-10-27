# Artefact package

Planning produces artefacts. Under "everything is code", the design session
writes them into the repo, next to the code they shape. Write each artefact
when its decision settles, not at the end. Only the handoff spec waits for
the final review round. Create files lazily.

## Contents

| Artefact             | Purpose                                         | Owner skill or rule               |
| :------------------- | :---------------------------------------------- | :-------------------------------- |
| Handoff spec         | The what, why and boundaries. Links to the rest. | "Writing for humans" (below)     |
| Decision tree        | Every node: state, decision, reason, links.     | `decision tree` format (below)    |
| Round replies        | The user's returned round files, as written.    | `grill-rounds.md`                 |
| Glossary             | The ubiquitous language.                        | Glossary rules (below)            |
| ADRs                 | Decisions that pass the ADR test.               | `architecture-decision-records`   |
| Architecture views   | Decided boundaries (C4).                        | `c4-architecture`                 |
| Acceptance scenarios | `.feature` files for each settled leaf group.   | `adzic-bdd` (Adzic Index ≥ 7)     |
| Tracer-bullet tickets | Backlog items, after the user approves.        | backlog / `jira-issue-manager`    |

## Placement

Do not impose a layout. Find the repo's layout first, then put each
artefact where a reader of that repo expects it.

### 1. Discover

Look for these signals, in this order:

1. **Written rules.** `AGENTS.md`, `CONTRIBUTING.md`, or a docs README that
   says where documents go. Obey them.
2. **Diataxis.** Directories such as `tutorials/`, `how-to/`, `reference/`,
   `explanation/` under `docs/`.
3. **A docs site.** `mkdocs.yml`, `_config.yml` (Jekyll), `docusaurus.config.*`,
   sidebar files. Copy the front matter of sibling pages (for example
   `parent`, `nav_order`, `layout`) so the new page appears in the nav.
4. **Existing homes.** ADR directories (`docs/adr/`, `docs/ADRs/`, `adrs/`,
   `docs/decisions/`) and their numbering; glossary files (`GLOSSARY.md`,
   `GLOSSARY-MAP.md`, a glossary page); spec or design directories
   (`docs/specs/`, `docs/design/`, `docs/architecture/`, `docs/rfcs/`);
   feature directories (`features/`, `validation/features/`,
   `tests/acceptance/`).
5. **Index pages.** A README or index that lists sibling documents. Add the
   new document to it.
6. **Doc checks.** Link, nav, or render checks in scripts or CI. Run them
   before the handoff.

### 2. Place

| Artefact             | In a Diataxis repo                    | Otherwise: reuse              | If nothing exists              |
| :------------------- | :------------------------------------ | :---------------------------- | :----------------------------- |
| Handoff spec         | `reference/` (readers consult it while they build) | the spec / design / architecture directory | `docs/specs/<topic>/` |
| Decision tree        | `explanation/` (it records why)       | next to the handoff spec      | next to the handoff spec       |
| Round replies        | next to the decision tree, `rounds/`  | same                          | same                           |
| Glossary             | `reference/`                          | the existing glossary         | `GLOSSARY.md` at the root      |
| ADRs                 | the existing ADR directory            | same                          | `docs/adr/NNNN-<slug>.md`      |
| Architecture views   | `explanation/`                        | the architecture directory    | a section in the handoff spec  |
| Acceptance scenarios | where the test runner reads them      | same                          | `features/`                    |

- A repo with several bounded contexts can have one glossary and one ADR
  directory per context (`src/<context>/GLOSSARY.md`,
  `src/<context>/docs/adr/`), listed in `GLOSSARY-MAP.md`. Put each artefact
  in the context that it belongs to.
- Design does not write tutorials or how-to guides. If a decision changes a
  procedure, add a follow-up item to the handoff spec.
- Tell the user where each artefact goes, in the first round that writes one.

## Glossary rules

From Matt Pocock's `domain-modeling` skill (MIT):

- One term, one meaning. List rejected synonyms under `_Avoid_`. This is
  also the core rule of ASD-STE100.
- One or two sentences for each term. Define what it is, not what it does.
  Write definitions in STE-flavored English: agents and people read them.
- Only domain terms. No implementation details, no general programming terms.

```md
**Sync conflict**:
Two different versions of one record reach the server.
_Avoid_: collision, clash
```

## ADR test

Write an ADR only when all three are true: hard to reverse, surprising
without context, and a real trade-off. A spec can hold settled decisions
first and promote them to ADRs when they are agreed (`promotes_to`).

## Decision tree format

An outline: easy to read, easy to diff. Each node has a stable id.

```
# Design tree: <topic>

Goal: <one sentence>
Stance: long horizon | mid-execution

- [settled] sync.conflict -- Last write wins, with a conflict log.
    Reason: <one line>. Round 1. ADR: <link>
  - [open] sync.conflict.log-fields -- Which fields does the log keep?
- [deferred] sync.scope -- Reason: wait for storage metrics.
- [rejected] sync.manual -- Reason: users forget to sync.
```

## Writing for humans

The artefacts are for people first. Many audiences read them: engineers,
testers, QA, owners, and agents. Model: diagrams as the specification, with
a contract block that makes the implementation reproducible.

### Structure of the handoff spec

1. **Front matter.** Status, version, owner, type, related documents, and
   `promotes_to` (the ADRs the spec will become). Use the repo's own keys
   if it has them.
2. **Status banner.** Status, owner, audience, scope, in 3 to 6 lines.
3. **Who reads what.** A table: for each audience, the sections to read,
   in order.
4. **At a glance.** One table or one diagram that shows the full design.
5. **Goal and success metric.** Two or three sentences.
6. **Spec units.** One for each part of the design:
   - a **Who / When** line;
   - a **diagram** that is the specification;
   - a **contract block**: the rules as MUST / SHOULD / MAY sentences, and
     a machine-readable contract (YAML) in a collapsed `<details>` block.
7. **Anti-goals.** What the implementation must not do.
8. **Open decisions.** A table: id, question, owner, needed before. These
   come from the `open` and `deferred` nodes.
9. **Links.** Decision tree, ADRs, glossary terms, acceptance scenarios.

### Rules

- **Pictures before prose.** Use text only for what the diagram cannot show.
- **The diagram is normative.** Name its elements with glossary terms. Use
  the same names in the contract block. Then an implementer (a person or an
  agent) can reproduce the design without guesses.
- **Diagram limits.** One abstraction level for each diagram. 20 elements
  maximum. Top-down layout, because pages are narrow. Use the repo's
  diagram tool and version (Mermaid is common). In vim rounds, use ASCII.
  Convert the ASCII diagram when the decision moves into the docs.
- **Language.** STE-flavored English for prose (`asd-ste100`). Strict
  ASD-STE100 for rules, contracts, and anything that an agent executes.
- **No jargon walls.** Define each term at first use, or link it to the
  glossary. Apply the uninformed reader test: a newcomer understands the
  section in 3 minutes.
- **What and why, never how.** The contract states behaviour and
  invariants. It does not dictate code structure.
- **Verify before the handoff.** Links resolve, diagrams render, contract
  blocks parse, and the repo's doc checks pass. Report the results to the
  user.
