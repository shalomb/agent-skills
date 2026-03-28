#!/usr/bin/env bash
# tmux-list.sh — JSON inventory of all tmux panes.
#
# Marks the current session and shows per-pane busy/idle state
# sourced from tmux-exec.sh's persistent state files.
#
# Requires: bash ≥4.2, tmux, jq

set -euo pipefail

readonly STATE_DIR="${TMPDIR:-/tmp}/tmux-exec-state.${UID}"

usage() {
    printf 'Usage: %s [-S SOCKET]\n' "${0##*/}" >&2
    exit 1
}

# Build a JSON object mapping pane_id (sans %) → { command, elapsed_s }
# for every pane that has an active state file.
build_busy_map() {
    local now
    printf -v now '%(%s)T' -1

    printf '{'
    local first=true sf
    for sf in "${STATE_DIR}"/*; do
        [[ -f ${sf} ]] || continue

        local -A st=()
        local line key val
        while IFS= read -r line; do
            key=${line%%=*}; val=${line#*=}
            st["${key}"]=${val}
        done < "${sf}"

        [[ -n ${st[started]-} ]] || continue

        local id elapsed
        id=$(basename -- "${sf}")
        (( elapsed = now - st[started] ))

        ${first} || printf ','
        first=false

        # Minimal JSON escaping for the command string.
        local cmd=${st[command]-}
        cmd=${cmd//\\/\\\\}
        cmd=${cmd//\"/\\\"}

        printf '"%s":{"command":"%s","elapsed_s":%d}' \
            "${id}" "${cmd}" "${elapsed}"
    done
    printf '}'
}

main() {
    local -a socket_args=()

    while getopts ':S:' opt; do
        case ${opt} in
            S) socket_args=( -S "${OPTARG}" ) ;;
            *) usage ;;
        esac
    done
    shift $(( OPTIND - 1 ))

    command -v tmux >/dev/null 2>&1 || { printf '[]\n'; exit 0; }

    # Current session for the is_current_session flag.
    local current_session=''
    if [[ -n ${TMUX-} ]]; then
        current_session=$(tmux "${socket_args[@]}" display-message \
                               -p '#{session_name}' 2>/dev/null) || true
    fi

    # Let tmux emit one JSON object per pane.  jq -s slurps into an array.
    # Note: tmux format strings don't need shell escaping — they're literal.
    local tmux_fmt='{"session_name":"#{session_name}","window_index":#{window_index},"window_name":"#{window_name}","pane_index":#{pane_index},"pane_id":"#{pane_id}","pane_current_command":"#{pane_current_command}","pane_mode":"#{pane_mode}","pane_title":"#{pane_title}","pane_active":#{pane_active}}'

    local raw
    raw=$(tmux "${socket_args[@]}" list-panes -a -F "${tmux_fmt}" 2>/dev/null) || true

    if [[ -z ${raw} ]]; then
        printf '[]\n'
        exit 0
    fi

    # Build the busy-state lookup as a JSON object.
    local busy_map
    busy_map=$(build_busy_map)

    # Let jq do the enrichment, sorting, and formatting in one pass.
    printf '%s\n' "${raw}" | jq -s \
        --arg cs "${current_session}" \
        --argjson busy "${busy_map}" \
    '
        [ .[] |
            (.pane_id | ltrimstr("%")) as $pid |
            . + {
                is_current_session: (.session_name == $cs),
                busy: ($busy[$pid] != null)
            } +
            if $busy[$pid] then {
                busy_command:   $busy[$pid].command,
                busy_elapsed_s: $busy[$pid].elapsed_s
            } else {} end
        ]
        | sort_by(
            (if .is_current_session then 0 else 1 end),
            .session_name, .window_index, .pane_index
        )
    '
}

main "$@"
