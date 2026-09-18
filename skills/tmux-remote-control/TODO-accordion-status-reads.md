# TODO: token-efficient, tiered pane reads ("accordion" for tmux status)

## Origin / motivation

Discovered while dogfooding this skill to orchestrate 2+ peer `claude` agents
in other panes over a long session (~2026-09-18). The orchestrator kept
hand-rolling `tmux capture-pane -p -t <target> -S -N` with a guessed `-N`
(commonly `-150`, `-200`, `-2000`) instead of using `tmux-read.sh`, because
`tmux-read.sh` doesn't fit this use case at all — see below. That's the
"dogfooding" gap: we should be using our own skill's tools for this, but the
tools as they exist weren't built for it.

**Goal:** make reading a peer agent's pane for "what's it doing / what did it
conclude" cost roughly 20-30 lines of output by default, with a deliberate,
explicit way to widen the read when more context is actually needed —
borrowing the **test-accordion** skill's own vocabulary and shape
(`~/shalomb/agent-skills/skills/test-accordion/SKILL.md`): aperture, rung,
progressive expansion vs. diagnostic contraction. Read that skill first; this
is the same idea applied to pane output instead of test scope.

## Why `tmux-read.sh` doesn't already do this

`tmux-read.sh` pipes a capture through `tmux-read.py`, which finds the
**previous shell prompt** by pattern (a line ending in a non-alphanumeric
symbol + optional whitespace, e.g. `user@host:~$ `) and returns everything
after it — i.e. "this one command's output." That's the right idea for a
**shell pane**, and works well there.

It does approximately nothing for a `claude` (or other agent-CLI) pane,
because there's no shell prompt in that scrollback at all — it's one
continuous TUI stream. Measured directly: capturing 2030 lines from a live
`claude` pane and piping through `tmux-read.py` returned 2024 lines back
(see session transcript for the exact command). The tool degrades to "return
almost everything," which is the same cost as not using it.

## Design direction (agreed before this was handed off)

- **Separate new script**, not new flags on `tmux-read.sh`. Keep
  `tmux-read.sh` exactly as it is (shell-prompt detection, unchanged
  behavior, no regression risk) and add a new script alongside it purpose-built
  for agent panes. Working name: `tmux-status.sh` — open to a better name.
- **Tiered / accordion output**, at minimum:
  - A small **status** aperture — on the order of 20-30 lines — good enough
    to answer "is it stuck, what's it doing right now, did it just finish."
  - A **full** aperture — today's existing flat `-n LINES` capture — for when
    the status tier isn't enough and real depth is needed.
  - Whether there's a useful **middle** tier ("last turn" / "since the last
    turn boundary") is worth prototyping, but see the open question below
    before committing to it as a fixed rung.
- **No hardcoded per-harness markers** (rejected during design: an earlier
  draft of this hardcoded Claude Code's own transcript glyphs — `●` for an
  assistant turn, `⎿` for a tool-result continuation, `❯` for the prompt line,
  `※` for a recap block — which would silently stop working the moment this
  is pointed at a Copilot CLI, Cursor, Antigravity, or any other harness's
  pane with different glyphs). Whatever detection logic ships needs to work
  across harnesses without a per-tool lookup table.
- **Auto-detection, not hardcoding, is the validated approach.** Prototyped
  and confirmed against a real `claude` pane capture before this was handed
  off: scan non-blank lines for a leading character that is non-alphanumeric
  and not common prose/code punctuation (exclude `# - * . / " ' ( ) { } [ ]`
  at minimum), and count frequency by leading character. On the sample
  captured this session, `●` came back as the clear outlier (17 occurrences)
  against one-off punctuation (`=`, `+`, `─`, `~`, `✻`, `❯` each 1-5
  occurrences) — with zero hardcoded knowledge of Claude Code's UI. This is
  the same principle `tmux-read.py` already applies to shell prompts
  (find a recurring signature, scan backward to its last occurrence),
  generalized one level up to "any recurring structural marker," not tied to
  what produces it. Whoever picks this up should re-verify this holds
  against a genuinely different harness's pane (Copilot CLI, Cursor, etc.)
  before trusting it cross-tool — only Claude Code was available to test
  against this session.
- **Token dedup as a secondary, general-purpose pass**, independent of the
  tiering: collapse runs of blank/whitespace-only lines (keep at most one),
  and collapse adjacent exact-duplicate lines (spinner-frame churn, e.g. a
  "✻ Cogitated for Ns" line updating in place can leave several
  near-identical captured lines). Measured on this session's sample capture:
  low yield in that specific snapshot (1 collapsible blank line, 0 adjacent
  exact dupes out of ~430 lines) — the sample just happened to land between
  spinner updates, not evidence the mechanism is low-value in general. Build
  it as a general pass regardless; don't skip it on the strength of one
  quiet sample.

## Open questions for whoever picks this up

1. **Does the 3-tier shape (status / last-turn / full) actually hold up**, or
   is 2 tiers (status / full) enough once dedup is doing real work? The
   "last-turn" middle tier was proposed but not built or tested — validate
   whether it earns its complexity before committing to it.
2. **What exactly goes in the ~20-30 line status tier** for a busy/idle
   determination that doesn't rely on Claude Code-specific spinner text
   (e.g. "✻ ... done HH:MM") — is there a harness-agnostic signal, or does
   "busy vs idle" necessarily need a per-harness heuristic even if the
   deeper tiering doesn't?
3. **Interaction with existing busy-state tracking**: `tmux-exec.sh` already
   tracks busy/idle for panes *it* launched commands in (state files under
   `${TMPDIR:-/tmp}/tmux-exec-state.${UID}/`). A peer agent's pane wasn't
   launched via `tmux-exec.sh` (it's another long-lived interactive session,
   dispatched into via `tmux-dispatch.sh`), so that state-file mechanism
   doesn't cover it. Does the new script need its own lightweight
   busy-detection, or is "grep the last N lines for a recurring
   in-progress-looking marker" sufficient without persistent state?
4. **Naming**: `tmux-status.sh` was a working name only, not agreed as final.

## Related, already shipped this session (context, not part of this TODO)

- `scripts/tmux-dispatch.sh` — paste-buffer-based dispatch to a peer pane,
  with a documented queueing behavior (a busy peer queues a pasted+submitted
  brief rather than dropping or force-submitting it).
- `references/orchestrating-peer-agents.md` — the broader "never trust a
  peer's self-report, verify independently" discipline this session was
  built around. The accordion/tiered-read work in this TODO is in service of
  that same discipline: cheaper routine status checks, without losing the
  ability to go deep when a claim needs real verification.
