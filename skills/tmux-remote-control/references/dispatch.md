> Scripts: `$SKILL_SCRIPTS` = `$(dirname <path-to-SKILL.md>)/scripts`. See `SKILL.md`.

# Dispatch (`scripts/tmux-dispatch.sh`)

Paste a brief into a peer pane's input and submit it — for a **different use
case** than the tools above. `tmux-exec.sh`, `tmux-read.sh` and `tmux-list.sh` drive a shell/REPL you own end to
end (send, wait, collect a result). This is for handing a task to a *peer
agent* running in another pane and walking away from the completion contract:
paste the brief, press Enter, and independently verify the outcome later
yourself — you are not waiting on this command to tell you the peer
finished.

```bash
$SKILL_SCRIPTS/tmux-dispatch.sh 0.1 'Please rerun make test and report the diff.'
$SKILL_SCRIPTS/tmux-dispatch.sh -f /path/to/brief.txt 0.0   # quote/backtick-heavy or multi-line
```

### Waiting for the reply: `-w SECONDS` (A2A)

If the peer is a pi started with `PI_A2A=1`, `-w` replaces paste-and-walk-away
with a real request/response: the brief goes over A2A to the pane's agent, the
command **blocks until the task finishes** (at most SECONDS), and the agent's
reply is printed on stdout.

```bash
reply=$($SKILL_SCRIPTS/tmux-dispatch.sh -w 120 0.1 'Run make test; reply with the failing test names.')
```

| Exit | Meaning |
|------|---------|
| 0 | Completed; reply on stdout |
| 2 | Task failed or was canceled (message on stderr) |
| 4 | The agent is **blocked on a human** (a dialog); the question is on stdout. Tell the user; do not retry |
| 5 | Timed out; the task keeps running (task id on stderr) |
| 6 | Endpoint refused (bad token) or unreachable |

The pane is matched to its agent by process ancestry through a handshake file in
`$XDG_RUNTIME_DIR/pi/a2a/` (loopback only, token never printed). With no
endpoint it **falls back to the plain paste with a warning**, so there is then
no wait and no reply: verify the outcome yourself as above. `-w` is ignored for
`-S`; `-i`/`-e` are not needed over A2A. The helper is `scripts/tmux-a2a.py`
(tests: `python3 -m unittest tests/test_tmux_a2a.py` from this directory).

See `references/orchestrating-peer-agents.md` for the full how-to: why this
uses paste-buffer instead of `send-keys -l`, how a busy target queues rather
than drops or force-submits a dispatch, and how to verify a peer's report
instead of trusting it.
