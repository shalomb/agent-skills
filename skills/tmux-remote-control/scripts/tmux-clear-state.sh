#!/usr/bin/env bash
# tmux-clear-state.sh — forcibly clear stuck/stale tmux-exec state for a pane.
#
# Use when a pane's command was killed, OOM-ed, or hung and tmux-exec.sh
# refuses to run because it thinks the pane is still busy.
#
# Clears:
#   • The state file (the "busy" lock)           → <STATE_DIR>/<pane_num>
#   • The lock file                              → <STATE_DIR>/<pane_num>.lock
#   • Any orphaned out/ec temp files it referenced
#
# With no TARGET, lists all panes with their current state so you can pick.
#
# Usage:
#   tmux-clear-state.sh                    # list all pane states
#   tmux-clear-state.sh 1.0               # clear state for window 1 pane 0 (current session)
#   tmux-clear-state.sh myses:2.1         # fully-qualified target
#   tmux-clear-state.sh --all             # clear ALL stale state (dead panes + orphaned files)
#   tmux-clear-state.sh --orphans         # clear only orphaned out/ec files
#
# Requires: bash ≥4.2, tmux

set -euo pipefail

readonly STATE_DIR="${TMPDIR:-/tmp}/tmux-exec-state.${UID}"

# ── helpers ──────────────────────────────────────────────────────────────

die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
info() { printf '%s\n' "$*"; }

resolve_pane_id() {
    local target=$1

    # Qualify with current session if no session name given
    if [[ ${target} != *:* && -n ${TMUX-} ]]; then
        local session
        session=$(tmux display-message -p '#{session_name}' 2>/dev/null) || true
        [[ -n ${session} ]] && target="${session}:${target}"
    fi

    local pane_id
    pane_id=$(tmux display-message -p -t "${target}" '#{pane_id}' 2>/dev/null) \
        || die "Target '${target}' not found — use tmux-list.sh or run with no args to list panes."
    [[ -n ${pane_id} ]] \
        || die "Target '${target}' not found."

    printf '%s' "${pane_id}"
}

state_file() { printf '%s/%s'      "${STATE_DIR}" "${1//%/}"; }
lock_file()  { printf '%s/%s.lock' "${STATE_DIR}" "${1//%/}"; }

read_state() {
    local sf=$1
    [[ -f ${sf} ]] || return 0
    local line key val
    while IFS= read -r line; do
        key=${line%%=*}; val=${line#*=}
        case ${key} in
            command) printf '  command : %s\n' "${val}" ;;
            mode)    printf '  mode    : %s\n' "${val}" ;;
            started)
                local age fmt
                printf -v age '%(%s)T' -1
                (( age = age - val ))
                fmt=$(date -d "@${val}" '+%H:%M:%S' 2>/dev/null) || fmt="${val}"
                printf '  started : %s (%ds ago)\n' "${fmt}" "${age}"
                ;;
            outfile) printf '  outfile : %s\n' "${val}" ;;
            ecfile)  printf '  ecfile  : %s\n' "${val}" ;;
        esac
    done < "${sf}"
}

clear_pane_state() {
    local pane_id=$1 dry_run=${2:-false}
    local sf lf

    sf=$(state_file "${pane_id}")
    lf=$(lock_file  "${pane_id}")

    local removed=0

    # Read referenced temp files from state before deleting it
    local outfile='' ecfile=''
    if [[ -f ${sf} ]]; then
        while IFS= read -r line; do
            case ${line%%=*} in
                outfile) outfile=${line#*=} ;;
                ecfile)  ecfile=${line#*=}  ;;
            esac
        done < "${sf}"
    fi

    for f in "${sf}" "${lf}" "${outfile}" "${ecfile}"; do
        [[ -n ${f} && -e ${f} ]] || continue
        if ${dry_run}; then
            info "  [dry-run] would remove: ${f}"
        else
            rm -f -- "${f}"
            info "  removed: ${f}"
        fi
        (( removed++ )) || true
    done

    (( removed > 0 )) || info "  (nothing to clear)"
}

clear_orphaned_files() {
    local dry_run=${1:-false}
    local count=0

    [[ -d ${STATE_DIR} ]] || { info "(state directory does not exist)"; return; }

    # Collect all pane_ids that have a state file
    local -A active_panes=()
    for sf in "${STATE_DIR}"/[0-9]*; do
        [[ -f ${sf} ]] || continue
        [[ ${sf} == *.lock ]] && continue
        active_panes["$(basename "${sf}")"]=1
    done

    # out.* and ec.* files that aren't referenced by any state file
    for f in "${STATE_DIR}"/out.* "${STATE_DIR}"/ec.*; do
        [[ -e ${f} ]] || continue

        # Check if any state file references this file
        local referenced=false
        for sf in "${STATE_DIR}"/[0-9]*; do
            [[ -f ${sf} && ! ${sf} == *.lock ]] || continue
            if grep -qF "$(basename "${f}")" "${sf}" 2>/dev/null; then
                referenced=true
                break
            fi
        done

        ${referenced} && continue

        if ${dry_run}; then
            info "  [dry-run] would remove orphan: ${f}"
        else
            rm -f -- "${f}"
            info "  removed orphan: ${f}"
        fi
        (( count++ )) || true
    done

    (( count > 0 )) || info "  (no orphaned files)"
}

list_state() {
    if [[ ! -d ${STATE_DIR} ]]; then
        info "State directory does not exist: ${STATE_DIR}"
        return
    fi

    local -a state_files=()
    for sf in "${STATE_DIR}"/[0-9]*; do
        [[ -f ${sf} && ! ${sf} == *.lock ]] && state_files+=( "${sf}" )
    done

    if (( ${#state_files[@]} == 0 )); then
        info "No busy panes recorded in ${STATE_DIR}"
    else
        info "Busy panes recorded in ${STATE_DIR}:"
        for sf in "${state_files[@]}"; do
            local pane_num pane_id alive
            pane_num=$(basename "${sf}")
            pane_id="%${pane_num}"
            alive=$(tmux display-message -p -t "${pane_id}" '#{pane_id}' 2>/dev/null || echo "DEAD")
            if [[ ${alive} == "DEAD" ]]; then
                info "  pane ${pane_id} [DEAD — safe to clear]"
            else
                local session window pane cmd
                session=$(tmux display-message -p -t "${pane_id}" '#{session_name}' 2>/dev/null || echo '?')
                window=$(tmux  display-message -p -t "${pane_id}" '#{window_index}' 2>/dev/null || echo '?')
                pane=$(tmux    display-message -p -t "${pane_id}" '#{pane_index}'   2>/dev/null || echo '?')
                cmd=$(tmux     display-message -p -t "${pane_id}" '#{pane_current_command}' 2>/dev/null || echo '?')
                info "  pane ${pane_id}  ${session}:${window}.${pane}  [current cmd: ${cmd}]"
            fi
            read_state "${sf}"
            echo
        done
    fi

    # Orphaned out/ec files
    local orphan_count=0
    for f in "${STATE_DIR}"/out.* "${STATE_DIR}"/ec.*; do
        [[ -e ${f} ]] || continue
        local referenced=false
        for sf in "${STATE_DIR}"/[0-9]*; do
            [[ -f ${sf} && ! ${sf} == *.lock ]] || continue
            if grep -qF "$(basename "${f}")" "${sf}" 2>/dev/null; then
                referenced=true; break
            fi
        done
        ${referenced} || (( orphan_count++ )) || true
    done
    (( orphan_count > 0 )) && info "${orphan_count} orphaned out/ec file(s) — run with --orphans to clear"

    return 0
}

clear_all_stale() {
    local dry_run=${1:-false}

    [[ -d ${STATE_DIR} ]] || { info "(state directory does not exist — nothing to clear)"; return; }

    local cleared=0

    # Clear state for dead panes
    for sf in "${STATE_DIR}"/[0-9]*; do
        [[ -f ${sf} && ! ${sf} == *.lock ]] || continue
        local pane_num pane_id alive
        pane_num=$(basename "${sf}")
        pane_id="%${pane_num}"
        alive=$(tmux display-message -p -t "${pane_id}" '#{pane_id}' 2>/dev/null || echo "DEAD")
        if [[ ${alive} == "DEAD" ]]; then
            info "Clearing state for dead pane ${pane_id}:"
            clear_pane_state "${pane_id}" "${dry_run}"
            (( cleared++ )) || true
        fi
    done

    # Also clear orphaned temp files
    info "Clearing orphaned out/ec files:"
    clear_orphaned_files "${dry_run}"

    (( cleared == 0 )) && info "(no stale state for dead panes found)"
}

# ── usage ─────────────────────────────────────────────────────────────────

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-clear-state.sh [OPTIONS] [TARGET]

	Clear stuck/stale tmux-exec state so a pane can accept new commands.

	TARGET format (same as tmux-exec.sh):
	  {window}.{pane}             current session (from $TMUX)
	  {session}:{window}.{pane}   fully qualified

	Options:
	  --all        Clear state for all dead panes + orphaned temp files.
	  --orphans    Clear only orphaned out/ec temp files (no state file found).
	  --dry-run    Show what would be removed without deleting anything.
	  -h, --help   Show this help.

	With no arguments, lists all panes that have recorded busy state.

	Examples:
	  tmux-clear-state.sh               # list busy pane state
	  tmux-clear-state.sh 1.0           # clear state for window 1, pane 0
	  tmux-clear-state.sh myses:2.1     # clear state for named session target
	  tmux-clear-state.sh --all         # clear all stale (dead panes + orphans)
	  tmux-clear-state.sh --orphans     # clear only orphaned temp files
	  tmux-clear-state.sh --dry-run --all
	EOF
    exit 0
}

# ── main ──────────────────────────────────────────────────────────────────

main() {
    local target='' do_all=false do_orphans=false dry_run=false

    while (( $# > 0 )); do
        case $1 in
            --all)      do_all=true    ;;
            --orphans)  do_orphans=true ;;
            --dry-run)  dry_run=true   ;;
            -h|--help)  usage          ;;
            -*)         die "Unknown option: $1" ;;
            *)          target=$1      ;;
        esac
        shift
    done

    if ${do_all}; then
        clear_all_stale "${dry_run}"
        return
    fi

    if ${do_orphans}; then
        info "Clearing orphaned out/ec files:"
        clear_orphaned_files "${dry_run}"
        return
    fi

    if [[ -z ${target} ]]; then
        list_state
        return
    fi

    local pane_id
    pane_id=$(resolve_pane_id "${target}")

    local sf
    sf=$(state_file "${pane_id}")

    if [[ ! -f ${sf} ]]; then
        info "Pane ${pane_id} (${target}): no state recorded — already clear."
        return
    fi

    info "Clearing state for pane ${pane_id} (${target}):"
    read_state "${sf}"
    echo
    clear_pane_state "${pane_id}" "${dry_run}"
    info "Done. Pane is now free for tmux-exec.sh."
}

main "$@"
