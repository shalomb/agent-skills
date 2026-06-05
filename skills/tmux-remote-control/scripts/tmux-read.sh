#!/usr/bin/env bash
# tmux-read.sh — scrape the last command's output from a tmux pane.
#
# Uses tmux-read.py for intelligent prompt detection.  Warns if the pane
# is marked busy by tmux-exec.sh so the caller knows the output may be
# from an incomplete command.
#
# Requires: bash ≥4.2, tmux, python3, coreutils

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly SCRIPT_DIR
readonly STATE_DIR="${TMPDIR:-/tmp}/tmux-exec-state.${UID}"

# ── helpers ──────────────────────────────────────────────────────────────

die()  { printf '%s\n' "$*" >&2; exit 1; }
warn() { printf '%s\n' "$*" >&2; }

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-read.sh [-S SOCKET] [-n LINES] TARGET

	Read the last command's output from a tmux pane.

	TARGET format:
	  {session}:{window}.{pane}   fully qualified
	  {window}.{pane}             current session (from $TMUX)

	Options:
	  -n LINES   History depth to capture (default: 2000).
	  -S PATH    Custom tmux socket path.
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

check_busy() {
    local pane_id=$1
    local sf="${STATE_DIR}/${pane_id//%/}"

    [[ -f ${sf} ]] || return 0

    local -A st=()
    local line key val
    while IFS= read -r line; do
        key=${line%%=*}
        val=${line#*=}
        st[${key}]=${val}
    done < "${sf}"

    [[ -n ${st[started]-} ]] || return 0

    local now elapsed
    printf -v now '%(%s)T' -1
    (( elapsed = now - st[started] ))

    warn "Warning: Pane is busy — a command has been running for ${elapsed}s."
    warn "  Command: ${st[command]-}"
    warn "  Output below may be incomplete."
    warn ""
}

# ── main ─────────────────────────────────────────────────────────────────

main() {
    local -a socket_args=()
    local lines=2000

    while getopts ':S:n:' opt; do
        case ${opt} in
            S) socket_args=( -S "${OPTARG}" ) ;;
            n) lines=${OPTARG} ;;
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

    # Warn (but don't block) if the pane has an outstanding command.
    check_busy "${pane_id}"

    tmux "${socket_args[@]}" capture-pane -t "${pane_id}" \
         -p -S "-${lines}" 2>/dev/null \
    | python3 "${SCRIPT_DIR}/tmux-read.py"
}

main "$@"
