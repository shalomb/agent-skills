#!/usr/bin/env bash
# tmux-exec.sh: The unified "Active" tool for sending keys and waiting.

set -euo pipefail

usage() {
    printf "Usage: %s [-w pattern] [-t timeout] [-S socket] <target> <command>\n" "${0##*/}" >&2
    exit 1
}

main() {
    local timeout=30 pattern="" socket_args=()
    while getopts "w:t:S:" opt; do
        case "${opt}" in
            w) pattern="${OPTARG}" ;;
            t) timeout="${OPTARG}" ;;
            S) socket_args=("-S" "${OPTARG}") ;;
            *) usage ;;
        esac
    done
    shift $((OPTIND - 1))

    [[ $# -lt 2 ]] && usage
    local target="$1" command="$2"

    local pane_id
    pane_id=$(tmux "${socket_args[@]}" display-message -p -t "${target}" "#{pane_id}" 2>/dev/null || true)
    [[ -z "${pane_id}" ]] && printf "Error: Target '%s' not found\n" "${target}" >&2 && exit 1

    local lock="/tmp/tmux-exec-${pane_id//%/}.lock"

    (
        if ! flock -x -w 60 200; then
            printf "Error: Pane %s is busy\n" "${target}" >&2
            exit 1
        fi

        local payload start_m="" end_m=""
        
        if [[ -z "${pattern}" ]]; then
            # SHELL MODE: Use markers and exit code capture
            local id=$(date +%s%N)
            start_m="S_$id" end_m="E_$id"
            payload=$(printf "echo \"%s\"; %s; ec=\$?; echo \"%s:\$ec\"" "${start_m}" "${command}" "${end_m}")
            pattern="${end_m}:([0-9]+)"
        else
            # INTERACTIVE MODE: Send literal command
            payload="${command}"
        fi

        tmux "${socket_args[@]}" set-buffer "${payload}"
        tmux "${socket_args[@]}" send-keys -t "${pane_id}" C-u
        tmux "${socket_args[@]}" paste-buffer -p -d -t "${pane_id}"
        tmux "${socket_args[@]}" send-keys -t "${pane_id}" C-m

        local start_t=$(date +%s)
        while true; do
            (( $(date +%s) - start_t > timeout )) && printf "Timeout after %ds\n" "${timeout}" >&2 && exit 124
            
            local buffer=$(tmux "${socket_args[@]}" capture-pane -t "${pane_id}" -p -S -100 2>/dev/null)
            
            if [[ "${buffer}" =~ ${pattern} ]]; then
                if [[ -n "${start_m}" ]]; then
                    # Shell Mode: Return exact output and exit code
                    local ec="${BASH_REMATCH[1]}"
                    tmux "${socket_args[@]}" capture-pane -t "${pane_id}" -p -S -32768 2>/dev/null | \
                    awk -v s="${start_m}" -v e="${end_m}" '$0 ~ s { f=1; next } $0 ~ e { f=0; exit } f { print }'
                    exit "${ec}"
                else
                    # Interactive Mode: Just return success
                    exit 0
                fi
            fi
            sleep 0.2
        done
    ) 200>"${lock}"
}

main "$@"
