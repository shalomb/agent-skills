---
title: Orchestrating Peer Agents Over Tmux
description: Dispatching work to another interactive agent's pane and independently verifying its results, as distinct from driving a shell/REPL you own
---

# Orchestrating Peer Agents Over Tmux

The rest of this skill (`tmux-exec.sh`, `tmux-read.sh`, `tmux-list.sh`,
`tmux-clear-state.sh`) is built around a **synchronous** model: you send a
command, you wait for it, you get its result back in the same call. That
model fits a shell or a REPL you're driving turn by turn.

Dispatching a task brief to a **peer agent** in another pane — another
`claude` session, say — is a different shape of problem:

- You don't get a return value. The peer works asynchronously, on its own
  clock, possibly for many minutes, possibly spawning its own sub-agents.
- What you get back is a **self-report**, not a result. Treat it exactly
  that way — as a claim to verify, not a fact to relay.
- The brief itself is usually long, multi-line, and full of exactly the
  characters (backticks, parens, quotes) that make shell-escaping painful.

This document covers the mechanics of the paste-and-submit step
(`tmux-dispatch.sh`), the queueing behavior when the target is busy, and the
verification discipline that makes the whole pattern trustworthy.

## Why paste-buffer, not `send-keys -l`

`tmux send-keys -l TARGET 'text'` sends `text` as literal keystrokes, but
`text` still has to survive **your own shell's** quoting rules to become a
single argument in the first place. A brief containing backticks,
`$(...)`, unbalanced parens, or a mix of single and double quotes is a live
hazard here — a misplaced backtick inside a `send-keys -l '...'` argument
gets interpreted by *your* shell before it ever reaches tmux, not by the
target pane's shell as intended:

```bash
# BREAKS: the backticks and $(...) get evaluated by YOUR shell
# while building the argument, not typed literally into the target pane.
tmux send-keys -l -t 0.1 'Fix the `coalesce()` call — see $(git log -1)'
```

`tmux-dispatch.sh` avoids this entirely by using tmux's own buffer
mechanism instead:

1. **Load the brief into a tmux buffer**, verbatim, untouched by any shell
   quoting rules of your own:
   - `tmux set-buffer -- "$BRIEF"` for a short inline string. This still
     goes through *your* shell once to build the `"$BRIEF"` argument, so it
     is only safe for briefs simple enough to survive that — no unescaped
     special characters.
   - `tmux load-buffer -- FILE` for anything else. Write the brief to a
     scratch file first (a heredoc is the natural way), then load it —
     tmux reads the file's bytes directly, with **no shell interpretation
     at all**. This is the reliable path for any brief with backticks,
     parens, quotes, or multiple lines; default to it once a brief is
     nontrivial rather than fighting inline quoting.
2. **`tmux paste-buffer -p -t TARGET`** types the buffer's contents into
   whatever currently has focus in that pane — a shell prompt, or another
   agent's input box — as if pasted. No re-interpretation happens at this
   step either; the bytes land exactly as loaded.
3. **A short settle delay, then `send-keys -t TARGET Enter`** as a separate
   step. Don't fold the Enter into the paste itself. Some TUIs — agent
   input boxes especially — need a moment after a paste to finish
   rendering it before they'll treat the next keystroke as "submit" rather
   than "still part of what was just pasted." `tmux-dispatch.sh` defaults
   to a 0.3s delay (`-s` to adjust).

```bash
$SKILL_SCRIPTS/tmux-dispatch.sh 0.1 'short, simple brief with no special chars'

cat > "$SCRATCH/brief.txt" <<'BRIEF'
Fix the `coalesce()` call in main.tf:42 -- it should read `var.bar`, not
`var.foo` (see ADR-003's "why" section). Use Farley-TDD: red, fix, green.
BRIEF
$SKILL_SCRIPTS/tmux-dispatch.sh -f "$SCRATCH/brief.txt" 0.0
```

## Queueing: dispatching into a busy peer

A target pane running another agent is often mid-task — including mid a
`/compact`, mid a long tool call, or mid its own sub-dispatch. Pasting and
sending Enter into a busy peer does **not** get lost, and does **not**
force the input through mid-operation. Observed directly: pasting a brief
into a `claude` pane that was 60%+ through a `/compact` left the pasted
text sitting in the input box; sending Enter at that point moved it into a
**visible queued-message state** — the pane showed the brief as its own
block above the prompt, with `Press up to edit queued messages` as the new
empty-input hint — and the harness fired it automatically, unprompted, the
moment `/compact` finished.

Practically: it is safe to dispatch to a pane without first polling it to
confirm it's idle. Paste and send Enter; if the target is mid-task, the
message queues and fires when the target frees up. You do not need to
retry, and you do not need to detect busy-vs-idle first the way
`tmux-exec.sh`'s busy-pane protection requires for a shell target. (This is
a property of the target *agent's* own input handling, not something
`tmux-dispatch.sh` implements — a plain shell pane has no such queue, and
pasting into one mid-command just types into whatever the running command
reads from stdin, which is usually not what you want. This queueing
behavior is specific to dispatching into another interactive agent.)

## Verify identity before you dispatch

Before treating a pane as a genuine, independent peer, confirm it actually
is one:

```bash
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{pane_current_command}'
```

A pane running `claude` in the *same window* as your own pane is not
automatically a different agent's session — it can be a pane that mirrors
or shadows your own activity (observed directly: a pane whose transcript
echoed the orchestrator's own tmux investigation commands back at it,
because it was reading the same terminal state rather than running
independently). When genuine independence matters, check the pane's
process against your own `$TMUX_PANE`/PID rather than assuming distinct
pane coordinates imply a distinct, independent session.

## Never trust a peer's self-report

This is the discipline that makes the whole pattern safe to use for real
work, and it is not optional:

- **A peer's summary of what it did is a claim, not a verification.**
  After a dispatched brief comes back "done," `tmux capture-pane` the full
  transcript and re-derive the result yourself: read the actual diff
  (`git show <claimed-commit>`), re-run the actual test command, check
  `git status --short` for a genuinely clean tree, and confirm no
  unintended trailers or scope crept into the commit.
- **Spot-check, don't just skim.** A peer can be right about 90% of a
  report and wrong (or overclaiming) about the one detail that matters —
  the fix is real but the test coverage claim is stale, or the "no other
  repo has this pattern" claim was based on a narrower grep than it
  sounds. Re-run the specific check yourself when the claim is
  load-bearing for a decision.
- **A peer correcting itself, or stopping to ask instead of guessing, is a
  good sign — not a failure to route around.** If a dispatched brief comes
  back with "this turned out more involved than expected, here are the
  options" rather than a forced-through fix, that is the standing
  instruction working as intended. Don't push it back into "just finish
  it" without deciding among the options first.
- **A peer sub-delegating (forking its own agent) for a large dispatched
  task is reasonable**, not scope creep — a 12-repo scan or a
  multi-file refactor is exactly the shape of task a sub-fork is for. What
  still needs verifying afterward doesn't change: the peer that did the
  forking is accountable for consolidating one coherent result, and you
  still independently check that result, not the fork's raw output.
- **Two peers finding the same thing independently is corroboration, not
  duplication to discard.** If two dispatched sessions converge on the
  same root cause via different evidence (e.g. one from real
  infrastructure state, one from reading test assertions), fold both into
  one record rather than picking one and dropping the other's evidence.
