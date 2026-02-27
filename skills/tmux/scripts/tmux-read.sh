#!/usr/bin/env bash
# tmux-read.sh: Read the output of the last command in an interactive pane.
# Intelligent prompt detection and output scraping.

set -euo pipefail

usage() {
    printf "Usage: %s [-S socket] [-n lines] <target>\n" "${0##*/}" >&2
    exit 1
}

main() {
    local socket_args=() lines=2000
    while getopts "S:n:" opt; do
        case "${opt}" in
            S) socket_args=("-S" "${OPTARG}") ;;
            n) lines="${OPTARG}" ;;
            *) usage ;;
        esac
    done
    shift $((OPTIND - 1))

    [[ $# -lt 1 ]] && usage
    local target="$1"

    local pane_id
    pane_id=$(tmux "${socket_args[@]}" display-message -p -t "${target}" "#{pane_id}" 2>/dev/null || true)
    [[ -z "${pane_id}" ]] && printf "Error: Target '%s' not found\n" "${target}" >&2 && exit 1

    local python_script="$(dirname "$(realpath "$0")")/tmux-read.py"
    tmux "${socket_args[@]}" capture-pane -t "${pane_id}" -p -S -"${lines}" 2>/dev/null | python3 "${python_script}"
}

main "$@"
