# Grill rounds in vim

Use this transport when the `grill_round` tool is available (`/grill-me`).
Without the tool, present the round in chat (SKILL.md, step 4).

The round file is the interface. The extension writes it, opens it in vim
in a tmux popup, and sends back only the delta. The agent never reads the
returned file again. The questions are already in its context.

## 1. UX rules

1. **Least resistance.** The likely choice is the default. The recommended
   option is ticked before the user sees the file. `:wq` accepts it.
2. **Silence is consent.** A question with no change and no note is settled
   with the recommendation.
3. **A question in a note keeps the node open.** A note that asks something
   does not accept the default. Answer it in the next round.
4. **Batch the frontier.** One round has 3 to 7 questions: every decision
   whose prerequisites are settled. A question that depends on another open
   question in the same round belongs to a later round.
5. **Ask only for decisions.** Look up facts in the code, docs, ADRs, and git
   history. Use a sub-agent for slow lookups. Only questions downstream of a
   running lookup wait for it.
6. **Show complex leaves.** A decision with more than two interacting parts
   gets an ASCII diagram. ASCII only, 72 columns maximum.
7. **Never lose work.** The extension keeps the round file until the
   decisions are recorded.

## 2. Round file format

Write the file in Strict ASD-STE100 (see the `asd-ste100` skill): one word
for one meaning, active voice, no `-ing` verbs, 20 words or less in each
instruction. The user can reply in any style.

```
# GRILL ROUND 1 -- topic: offline sync for the mobile app
# STANCE: long horizon. The current code is evidence, not authority.
#
# KEYS:  ]q / [q  next / previous question
#        <Space>  select the option on this line
#        >>       write a reply under this line
#        :wq      send       :q!  stop

## Q1 [sync.conflict] -- Which rule must resolve a sync conflict?

CONTEXT:
  Two devices can change the same record when they are offline.

OPTIONS:
  [x] A. Last write wins, with a conflict log.  (RECOMMENDED)
         Easy to make. The log lets support find lost data.
  [ ] B. Field-level merge.
         Less data loss. Needs a change to the schema.

DIAGRAM:
  device-1 --edit--+                +--> A: keep newest, write log
                   +--> server -----+
  device-2 --edit--+                +--> B: merge field by field

## TERMS

  Record: one item that a user owns and can change, for example a work order.
    Avoid: entry, row, item
  Sync conflict: two different versions of one record reach the server.
    Avoid: collision, clash
  [?] Device: <the agent is not sure. Reply with >> to define it.>
```

- Each question has a stable node id in brackets (`sync.conflict`).
- Each option has a label of 1 to 6 words and one line of trade-offs.
- Lines that start with `#` are instructions. The parser ignores them.
- The first line of the file states the stance on the code (see SKILL.md,
  "Horizon and the code").

### The TERMS section

The `## TERMS` section is always the last section. It lists the domain terms
that the round uses: the settled terms from the glossary, and the new or
unclear terms marked `[?]`. It has two purposes:

1. **The user can correct a term while thinking about the round.** A `>>`
   reply or an edit under a term is a term change. The delta reports it as
   `TERMS <term>: ...`. The agent puts the change in the glossary when it
   settles.
2. **Vim completion knows the terms.** Keyword completion (`Ctrl-N`,
   `Ctrl-P`) reads words from the buffer. With the terms in the file, the
   user's replies use the same words as the glossary.

A term conflict is a frontier question. The agent proposes one term, lists
the rejected synonyms under `Avoid`, and marks the term `[?]`. It does not
stop the round to ask about one word.

## 3. Replies: the `>>` convention

The user writes `>> text` under the line of concern. Consecutive `>>` lines
are one paragraph. An empty `>>` line starts a new paragraph. A line that
the user adds without `>>` is also a note. The user can also rewrite a
generated line, for example to correct a fact.

The vim buffer maps `>>` to "open a reply line under the cursor".

## 4. The delta

The extension compares the returned file with the original, line by line.
It attaches each added block to the original line above it. A note under an
option's trade-off line attaches to the option label. The model gets this:

```
Q1 sync.conflict: pick=A (OPEN, note asks a question)
  re OPTIONS "A. Last write wins, with a conflict log…": What happens when ...
Q2 sync.scope: pick=C (was A)
  edit CONTEXT: "…than 10 000…" -> "…than 5 000…"
Q3: default accepted, no notes
TERMS Device: a phone or tablet that one user signs in to
```

Before the agent changes the tree, it sorts each note into one of these
kinds: question, correction, constraint, decision, or new branch. If one
question gets a long thread of notes, the next round gives it a dedicated
question with a diagram.

## 5. The no-change prompt

The delta is empty after normalisation. Normalisation ignores whitespace,
`#` lines, and changes outside answer boxes and notes. The extension then
asks one question in pi. The first option is the default:

```
No answers changed. What next?
> 1. Accept the recommendations and continue   (default)
  2. Reshape the request          -> type what is wrong
  3. Answer later                 -> keep the file, stop now
  4. Stop the session
```

- **Reshape** makes the same round again with the typed text as context.
  Usual causes: wrong premise, wrong scope, too many or too deep questions.
- **Answer later** keeps the file. `/grill-me resume` opens it again.
- **Stop** records the settled nodes and marks the others open.

## 6. Defaults

| Situation                      | Action                                      |
| :----------------------------- | :------------------------------------------ |
| No tmux session                | Stop. Tell the user that tmux is necessary. |
| File changed                   | Send the delta. Continue without a prompt.  |
| File unchanged                 | No-change prompt. Default: accept.          |
| Question has no tick           | Use the recommendation.                     |
| Question has two ticks         | Ask again in the next round.                |
| Note asks a question           | Keep the node open. Answer next round.      |
| Note rejects the premise       | Reshape the parent node.                    |
| Round file found at start      | Offer resume. Default: resume.              |

## 7. Node states, the Adversarial Stress-Test, and the end of the session

Each node in `decision-tree.md` has one of these states:
`open`, `settled`, `deferred` (with a reason), or `rejected` (with a reason).

### The penultimate round: Adversarial Stress-Test (`waf.*`)

When all functional nodes on the critical path are `settled`, do **not** send
the final review round yet. First send one **Adversarial Stress-Test Round**
(`waf.*` nodes) to shoot holes in the settled concept across five lenses:

1. **Cost & latency ceiling (`waf.cost-overhead-cap`):** Where does
   orchestration or ceremony cost more than the work itself? What must be
   deterministic instead of an LLM or network hop?
2. **Concurrency & contention (`waf.concurrency`):** Where do parallel workers
   or requests collide (locks, rebase storms, cold-start amplification)?
3. **Partial-failure salvage (`waf.partial-salvage`):** When step $K$ of $N$
   fails, how is valid work from steps $1 \dots K-1$ kept instead of lost?
4. **Cold-start & small-$N$ safety (`waf.cold-start`):** Where does the design
   assume large-$N$ statistics or steady-state caches that fail at $N=1$?
5. **Falsifiable hypotheses (`waf.falsifiable-hypotheses`):** Bind each core
   pillar to a numeric pass/kill threshold tested in a tracer spike.

### Handoff readiness checks

The tree is ready for handoff when all of these are true:

1. No `open` node is on the critical path (including the `waf.*` stress-test
   nodes).
2. Each leaf can be written as a Gherkin scenario: the what, not the how.
3. Every core architectural bet has a **Falsifiable Hypothesis** with a numeric
   kill threshold mapped to a tracer spike.
4. Every settled ADR node represents **one** architectural decision (no
   compound "God Decisions") and was written after loading
   `architecture-decision-records`.
5. The last round added no glossary term and changed no definition.
6. The last round made no new node, and the user accepted most defaults.

A soft cap of 5 to 8 rounds applies. At the cap, list the open nodes and
offer to defer them.

Then send a **final review round**. It shows the full tree as an ASCII
outline, the draft handoff spec, and where each artefact goes. The user approves with
`:wq` or corrects with `>>` notes. The user can also end the session at any
time with `/grill-me done`.
