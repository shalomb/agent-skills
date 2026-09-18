#!/usr/bin/env bash
# tmux-dispatch.sh — paste a brief into a peer agent's pane and submit it.
#
# Built for dispatching work to another interactive CLI agent (claude, etc.)
# running in its own pane: a task brief, often long and multi-line with
# quotes/backticks/parens, needs to land in that pane's input box exactly as
# written and then be submitted — without going through the target shell's
# own quoting/interpretation the way `tmux send-keys -l TEXT` would.
#
# Uses the tmux paste-buffer mechanism instead of send-keys -l:
#   1. Load BRIEF verbatim into a tmux buffer (set-buffer for short inline
#      text, load-buffer from a file for anything with shell metacharacters
#      or spanning multiple lines).
#   2. paste-buffer -p into the target pane — this types the buffer's bytes
#      into whatever has focus there (a shell prompt, or another agent's
#      input box), with no shell re-interpretation.
#   3. A short settle delay, then Enter — separated from the paste because
#      some TUIs (agent input boxes in particular) need a moment to finish
#      rendering pasted text before they'll treat the next keystroke as
#      "submit" rather than "still part of the paste."
#
# This also works to QUEUE a brief while the target is mid-task (e.g.
# running /compact): the paste lands in the input box, and if the agent is
# busy, sending Enter does not force it through — the harness queues the
# message (visible in the pane as "[Pasted text #N]" with a
# "Press up to edit queued messages" prompt) and fires it automatically
# once the agent is free. Nothing about this script needs to change for
# that case; it is a property of the target agent's own input handling,
# not of how the paste was delivered.
#
# Requires: bash ≥4.2, tmux

set -euo pipefail

die()  { printf '%s\n' "$*" >&2; exit 1; }

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-dispatch.sh [-s SECONDS] [-S SOCKET] TARGET BRIEF
	       tmux-dispatch.sh [-s SECONDS] [-S SOCKET] -f FILE TARGET

	Paste BRIEF (or the contents of FILE) into TARGET's input and submit it
	with Enter.

	TARGET format:
	  {session}:{window}.{pane}   fully qualified
	  {window}.{pane}             current session (from $TMUX)

	Options:
	  -f FILE      Read the brief from FILE instead of an inline argument.
	               Use this whenever the brief contains backticks, parens,
	               single/double quotes, or spans multiple lines — anything
	               that would otherwise need careful shell escaping to pass
	               as a single inline argument.
	  -s SECONDS   Settle delay between paste and Enter (default: 0.3).
	               Increase for slow-rendering TUIs if Enter seems to land
	               before the paste has finished appearing.
	  -S PATH      Custom tmux socket.

	Examples:
	  # short inline brief
	  tmux-dispatch.sh 0.1 'Please rerun make test and report the diff.'

	  # long, quote-heavy brief — write it to the skill's scratch dir first
	  cat > "$SCRATCH/brief.txt" <<'BRIEF'
	  Fix the coalesce() in main.tf:42 — it reads `var.foo` but should read
	  `var.bar` (see ADR-003's "why" section). Use Farley-TDD: red, fix, green.
	  BRIEF
	  tmux-dispatch.sh -f "$SCRATCH/brief.txt" 0.0

	Exit codes:
	  0   Pasted and Enter sent (does not confirm the target accepted it —
	      capture-pane and read the result yourself before trusting it).
	  1   Bad usage, missing file, or tmux command failed.
	EOF
    exit 1
}

main() {
    local settle='0.3' socket_args=() brief_file=''

    while getopts ':f:s:S:' opt; do
        case ${opt} in
            f) brief_file=${OPTARG} ;;
            s) settle=${OPTARG} ;;
            S) socket_args=( -S "${OPTARG}" ) ;;
            *) usage ;;
        esac
    done
    shift $(( OPTIND - 1 ))

    local target brief=''
    if [[ -n ${brief_file} ]]; then
        [[ $# -eq 1 ]] || usage
        target=$1
        [[ -f ${brief_file} ]] || die "tmux-dispatch.sh: no such file: ${brief_file}"
    else
        [[ $# -eq 2 ]] || usage
        target=$1
        brief=$2
    fi

    # Resolve {window}.{pane} against the current session, same convention
    # as tmux-exec.sh / tmux-read.sh.
    if [[ ${target} != *:* ]]; then
        [[ -n ${TMUX-} ]] || die "tmux-dispatch.sh: bare '${target}' needs \$TMUX set (current session), or pass session:window.pane"
        local current_session
        current_session=$(tmux "${socket_args[@]}" display-message -p '#{session_name}') \
            || die "tmux-dispatch.sh: could not resolve current session"
        target="${current_session}:${target}"
    fi

    # Refuse to dispatch into our own pane — same guard tmux-exec.sh applies.
    if [[ -n ${TMUX_PANE-} ]]; then
        local target_pane_id
        target_pane_id=$(tmux "${socket_args[@]}" list-panes -t "${target%%.*}" \
                              -F '#{pane_index} #{pane_id}' 2>/dev/null \
                          | awk -v idx="${target##*.}" '$1==idx{print $2}')
        [[ ${target_pane_id} != "${TMUX_PANE}" ]] \
            || die "tmux-dispatch.sh: refusing to dispatch into the agent's own pane (${target})"
    fi

    if [[ -n ${brief_file} ]]; then
        tmux "${socket_args[@]}" load-buffer -- "${brief_file}"
    else
        tmux "${socket_args[@]}" set-buffer -- "${brief}"
    fi

    tmux "${socket_args[@]}" paste-buffer -p -t "${target}"
    sleep "${settle}"
    tmux "${socket_args[@]}" send-keys -t "${target}" Enter
}

main "$@"
