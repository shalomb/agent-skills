#!/usr/bin/env bash
# tmux-dispatch.sh — paste a brief into a peer agent's pane and submit it.
# ...
set -euo pipefail

die()  { printf '%s\n' "$*" >&2; exit 1; }

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-dispatch.sh [-s SECONDS] [-S SOCKET] [-i PREFIX_KEYS] [-e SUBMIT_KEYS] TARGET BRIEF
	       tmux-dispatch.sh [-s SECONDS] [-S SOCKET] [-i PREFIX_KEYS] [-e SUBMIT_KEYS] -f FILE TARGET

	Paste BRIEF (or the contents of FILE) into TARGET's input and submit it.

	TARGET format:
	  {session}:{window}.{pane}   fully qualified
	  {window}.{pane}             current session (from $TMUX)

	Options:
	  -f FILE      Read the brief from FILE instead of an inline argument.
	  -s SECONDS   Settle delay between paste and submit (default: 0.3).
	  -S PATH      Custom tmux socket.
	  -i KEYS      Keys to send BEFORE pasting (e.g., 'Escape i' for vim mode).
	  -e KEYS      Keys to send AFTER pasting to submit (default: 'Enter').

	Exit codes:
	  0   Pasted and submitted.
	  1   Bad usage, missing file, or tmux command failed.
	EOF
    exit 1
}

main() {
    local settle='0.3' socket_args=() brief_file='' prefix_keys='' submit_keys='Enter'

    while getopts ':f:s:S:i:e:' opt; do
        case ${opt} in
            f) brief_file=${OPTARG} ;;
            s) settle=${OPTARG} ;;
            S) socket_args=( -S "${OPTARG}" ) ;;
            i) prefix_keys=${OPTARG} ;;
            e) submit_keys=${OPTARG} ;;
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

    if [[ ${target} != *:* ]]; then
        [[ -n ${TMUX-} ]] || die "tmux-dispatch.sh: bare '${target}' needs \$TMUX set (current session), or pass session:window.pane"
        local current_session
        current_session=$(tmux "${socket_args[@]}" display-message -p '#{session_name}') \
            || die "tmux-dispatch.sh: could not resolve current session"
        target="${current_session}:${target}"
    fi

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

    if [[ -n ${prefix_keys} ]]; then
        # Word-split prefix_keys intentionally so "Escape i" becomes two arguments
        # shellcheck disable=SC2086
        tmux "${socket_args[@]}" send-keys -t "${target}" ${prefix_keys}
    fi

    tmux "${socket_args[@]}" paste-buffer -t "${target}"
    sleep "${settle}"
    
    if [[ -n ${submit_keys} ]]; then
        # shellcheck disable=SC2086
        tmux "${socket_args[@]}" send-keys -t "${target}" ${submit_keys}
    fi
}

main "$@"
