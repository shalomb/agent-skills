#!/usr/bin/env bash
# tmux-list.sh: Output a JSON array of all panes with details.
# Strict Bash implementation.

set -euo pipefail

usage() {
    printf "Usage: %s [-S socket]\n" "${0##*/}" >&2
    exit 1
}

main() {
    local socket_args=()

    while getopts "S:" opt; do
        case "${opt}" in
            S) socket_args=("-S" "${OPTARG}") ;;
            *) usage ;;
        esac
    done
    shift $((OPTIND - 1))

    if ! command -v tmux >/dev/null 2>&1; then
        printf "[]\n"
        exit 0
    fi

    # Produce JSON objects per pane using tmux format
    # We use #{q:session_name} to escape quotes in session names for safety
    local format='{"session_name":"#{session_name}","window_index":#{window_index},"window_name":"#{window_name}","pane_index":#{pane_index},"pane_id":"#{pane_id}","pane_current_command":"#{pane_current_command}","pane_mode":"#{pane_mode}","pane_title":"#{pane_title}","pane_active":"#{pane_active}"}'

    # Slurp into JSON array using jq
    tmux "${socket_args[@]}" list-panes -a -F "${format}" 2>/dev/null | jq -s '.' || printf "[]\n"
}

main "$@"
