#!/usr/bin/env bash
# tmux-dispatch.sh — paste a brief into a peer agent's pane and submit it.
# ...
set -euo pipefail

die()  { printf '%s\n' "$*" >&2; exit 1; }

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-dispatch.sh [-s SECONDS] [-S SOCKET] [-i PREFIX_KEYS] [-e SUBMIT_KEYS] [-w SECONDS] TARGET BRIEF
	       tmux-dispatch.sh [-s SECONDS] [-S SOCKET] [-i PREFIX_KEYS] [-e SUBMIT_KEYS] [-w SECONDS] -f FILE TARGET

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
	  -w SECONDS   Wait for the agent's reply: if the pane's agent exposes an A2A endpoint
	               (pi with PI_A2A=1), send the brief over A2A instead of pasting, block until the
	               task finishes (at most SECONDS), and print the reply on stdout. Falls back to
	               paste-and-return, with a warning, when the pane has no endpoint. Not used with
	               -S, -i or -e (A2A needs no keystrokes).

	Exit codes:
	  0   Pasted and submitted (or, with -w over A2A, the agent completed; reply on stdout).
	  1   Bad usage, missing file, or tmux command failed.
	  With -w over A2A also: 2 task failed/canceled, 4 agent is waiting on a human (question
	  on stdout), 5 timed out (task id on stderr), 6 endpoint refused or unreachable.
	EOF
    exit 1
}

main() {
    local settle='0.3' socket_args=() brief_file='' prefix_keys='' submit_keys='Enter' wait_secs=''

    while getopts ':f:s:S:i:e:w:' opt; do
        case ${opt} in
            f) brief_file=${OPTARG} ;;
            s) settle=${OPTARG} ;;
            S) socket_args=( -S "${OPTARG}" ) ;;
            i) prefix_keys=${OPTARG} ;;
            e) submit_keys=${OPTARG} ;;
            w) wait_secs=${OPTARG} ;;
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

    if [[ -n ${wait_secs} ]]; then
        [[ ${wait_secs} =~ ^[0-9]+$ ]] || die "tmux-dispatch.sh: -w needs a whole number of seconds"
        if (( ${#socket_args[@]} == 0 )); then
            local script_dir a2a_args=() rc=0
            script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
            a2a_args=( send -t "${wait_secs}" )
            [[ -n ${brief_file} ]] && a2a_args+=( -f "${brief_file}" )
            a2a_args+=( "${target}" )
            [[ -n ${brief_file} ]] || a2a_args+=( "${brief}" )
            python3 "${script_dir}/tmux-a2a.py" "${a2a_args[@]}" || rc=$?
            # 3 = no endpoint for this pane: fall through to the paste path below.
            (( rc == 3 )) || exit "${rc}"
            printf '%s\n' "tmux-dispatch.sh: no A2A endpoint for ${target}; pasting without waiting for a reply" >&2
        else
            printf '%s\n' "tmux-dispatch.sh: -w is not supported with -S; pasting without waiting for a reply" >&2
        fi
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
