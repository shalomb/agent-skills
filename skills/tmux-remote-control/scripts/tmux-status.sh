#!/usr/bin/env bash
# tmux-status.sh — token-efficient, tiered pane reads for agent TUIs.
#
# Unlike tmux-read.sh (which expects shell prompts), this reads agent CLIs
# by detecting structural markers and extracting exactly the required tier
# of output (status, turn, or full).
#
# Requires: bash ≥4.2, tmux, python3

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly SCRIPT_DIR
readonly STATE_DIR="${TMPDIR:-/tmp}/tmux-exec-state.${UID}"

# ── helpers ──────────────────────────────────────────────────────────────

die()  { printf '%s\n' "$*" >&2; exit 1; }
warn() { printf '%s\n' "$*" >&2; }

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-status.sh [-S SOCKET] [-n LINES] [-t TIER] TARGET

	Read agent TUI output from a tmux pane with token deduplication.

	TARGET format:
	  {session}:{window}.{pane}   fully qualified
	  {window}.{pane}             current session (from $TMUX)

	Tiers:
	  status  - Small aperture: the last ~30 lines of deduped output
	  turn    - Default: Auto-detects prompt boundaries to isolate the complete last turn
	  full    - Full aperture: the entire deduped capture

	Options:
	  -t TIER    Tier to extract: status, turn, or full (default: turn)
	  -n LINES   History depth to capture before deduplication (default: 2000)
	  -S PATH    Custom tmux socket path
	EOF
    exit 1
}

resolve_target() {
    local target=$1; shift
    local -a socket_args=( "$@" )

    if [[ ${target} == *:* ]]; then
        printf '%s' "${target}"
        return
    fi

    if [[ -n ${TMUX-} ]]; then
        local session
        session=$(tmux "${socket_args[@]}" display-message -p '#{session_name}' 2>/dev/null) || true
        if [[ -n ${session} ]]; then
            printf '%s:%s' "${session}" "${target:-0.0}"
            return
        fi
    fi

    printf '%s' "${target:-0.0}"
}

# ── main ─────────────────────────────────────────────────────────────────

main() {
    local -a socket_args=()
    local lines=2000
    local tier="turn"

    while getopts ':S:n:t:' opt; do
        case ${opt} in
            S) socket_args=( -S "${OPTARG}" ) ;;
            n) lines=${OPTARG} ;;
            t) 
                if [[ ${OPTARG} != "status" && ${OPTARG} != "turn" && ${OPTARG} != "full" ]]; then
                    die "Error: Invalid tier '${OPTARG}'. Must be status, turn, or full."
                fi
                tier=${OPTARG} 
                ;;
            :) die "Option -${OPTARG} requires an argument." ;;
            *) usage ;;
        esac
    done
    shift $(( OPTIND - 1 ))

    (( $# >= 1 )) || usage
    local target
    target=$(resolve_target "$1" "${socket_args[@]}")

    local pane_id
    pane_id=$(tmux "${socket_args[@]}" display-message -p \
                   -t "${target}" '#{pane_id}' 2>/dev/null) \
        || die "Error: Target '${target}' not found." \
               $'\n'"Use tmux-list.sh to see available panes."

    [[ -n ${pane_id} ]] \
        || die "Error: Target '${target}' not found." \
               $'\n'"Use tmux-list.sh to see available panes."

    tmux "${socket_args[@]}" capture-pane -t "${pane_id}" \
         -p -S "-${lines}" 2>/dev/null \
    | python3 "${SCRIPT_DIR}/tmux-status.py" --tier "${tier}"
}

main "$@"
