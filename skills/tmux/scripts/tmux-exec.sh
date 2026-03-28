#!/usr/bin/env bash
# tmux-exec.sh — send a command to a tmux pane, wait for completion,
#                return its stdout+stderr and exit code.
#
# Synchronisation via tmux wait-for (channel-based, no polling).
# Output captured via file redirection (no markers, no scrollback scraping).
#
# Per-pane state files track outstanding commands so that:
#   • A timed-out invocation leaves the pane marked busy.
#   • A subsequent call detects the busy state and either harvests
#     a late finish or refuses with a clear error.
#
# Requires: bash ≥4.2, tmux ≥1.8 (wait-for), flock, coreutils

set -euo pipefail

# ── state directory (stable, per-user) ───────────────────────────────────
readonly STATE_DIR="${TMPDIR:-/tmp}/tmux-exec-state.${UID}"
if [[ ! -d ${STATE_DIR} ]]; then
    mkdir -p -- "${STATE_DIR}"
    chmod 0700 -- "${STATE_DIR}"
fi

# ── helpers ──────────────────────────────────────────────────────────────

die()  { printf '%s\n' "$*" >&2; exit 1; }
warn() { printf '%s\n' "$*" >&2; }

usage() {
    cat >&2 <<-'EOF'
	Usage: tmux-exec.sh [-w PATTERN] [-t TIMEOUT] [-S SOCKET] TARGET COMMAND

	Send COMMAND to a tmux pane and wait for completion.

	TARGET format:
	  {session}:{window}.{pane}   fully qualified
	  {window}.{pane}             current session (from $TMUX)

	Options:
	  -t SEC       Timeout in seconds (default: no timeout — waits forever).
	  -w PATTERN   Interactive mode — send keys and poll for PATTERN regex
	               instead of using wait-for synchronisation.
	  -S PATH      Custom tmux socket path.

	Exit codes:
	  <N>   Command's own exit code (shell mode).
	  0     Pattern matched (interactive mode).
	  1     Error (target not found, pane busy, self-target, …).
	  124   Timeout.  The command is STILL RUNNING in the pane.
	EOF
    exit 1
}

resolve_target() {
    local target=$1; shift
    local -a sock=( "$@" )

    [[ ${target} == *:* ]] && { printf '%s' "${target}"; return; }

    if [[ -n ${TMUX-} ]]; then
        local session
        session=$(tmux "${sock[@]}" display-message -p '#{session_name}' 2>/dev/null) || true
        if [[ -n ${session} ]]; then
            printf '%s:%s' "${session}" "${target:-0.0}"
            return
        fi
    fi
    printf '%s' "${target:-0.0}"
}

state_file() { printf '%s/%s' "${STATE_DIR}" "${1//%/}"; }

pane_alive() {
    local pane_id=$1; shift
    local result
    result=$(tmux "$@" display-message -p -t "${pane_id}" '#{pane_id}' 2>/dev/null) || return 1
    [[ ${result} == "${pane_id}" ]]
}

# ── state management ─────────────────────────────────────────────────────

write_state() {
    local sf=$1 channel=$2 command=$3 mode=$4 outfile=$5 ecfile=$6
    printf 'channel=%s\ncommand=%s\nmode=%s\noutfile=%s\necfile=%s\nstarted=%(%s)T\npid=%d\n' \
        "${channel}" "${command}" "${mode}" "${outfile}" "${ecfile}" -1 $$ > "${sf}"
}

read_state() {
    local -n _map=$1; local sf=$2
    local line key val
    while IFS= read -r line; do
        key=${line%%=*}; val=${line#*=}
        _map["${key}"]=${val}
    done < "${sf}"
}

# Check if a previous command finished or is still running.
# Returns 0 = pane free, 1 = still busy.
try_harvest_previous() {
    local sf=$1 pane_id=$2; shift 2
    local -a sock=( "$@" )

    [[ -f ${sf} ]] || return 0

    local -A prev=()
    read_state prev "${sf}"

    [[ -n ${prev[channel]-} ]] || { rm -f -- "${sf}"; return 0; }

    # Pane gone → command died with it.
    if ! pane_alive "${pane_id}" "${sock[@]}"; then
        rm -f -- "${sf}" "${prev[outfile]-}" "${prev[ecfile]-}"
        return 0
    fi

    # Check if the exit code file exists (command finished after we timed out).
    if [[ -n ${prev[ecfile]-} && -s ${prev[ecfile]} ]]; then
        rm -f -- "${sf}" "${prev[outfile]-}" "${prev[ecfile]-}"
        return 0
    fi

    # Still running.
    local now elapsed
    printf -v now '%(%s)T' -1
    (( elapsed = now - prev[started] ))

    local started_fmt
    started_fmt=$(date -d "@${prev[started]}" '+%H:%M:%S' 2>/dev/null) \
        || started_fmt=${prev[started]}

    cat >&2 <<-EOF
	Error: Pane is busy — a previous command is still running.

	  Command:  ${prev[command]}
	  Running:  ${elapsed}s (since ${started_fmt})

	Options:
	  1. Wait and retry later.
	  2. Cancel it:  tmux send-keys -t '${pane_id}' C-c
	  3. Use a different pane.
	EOF
    return 1
}

clear_state() {
    local sf=$1 outfile=$2 ecfile=$3
    rm -f -- "${sf}" "${outfile}" "${ecfile}"
}

# ── main ─────────────────────────────────────────────────────────────────

main() {
    local timeout=0 pattern='' sock=()

    while getopts ':w:t:S:' opt; do
        case ${opt} in
            w) pattern=${OPTARG} ;;
            t) timeout=${OPTARG} ;;
            S) sock=( -S "${OPTARG}" ) ;;
            :) die "Option -${OPTARG} requires an argument." ;;
            *) usage ;;
        esac
    done
    shift $(( OPTIND - 1 ))
    (( $# >= 2 )) || usage

    local target command=$2
    target=$(resolve_target "$1" "${sock[@]}")

    local pane_id
    pane_id=$(tmux "${sock[@]}" display-message -p -t "${target}" '#{pane_id}' 2>/dev/null) \
        || die "Error: Target '${target}' not found." $'\n'"Use tmux-list.sh to see available panes."
    [[ -n ${pane_id} ]] \
        || die "Error: Target '${target}' not found." $'\n'"Use tmux-list.sh to see available panes."

    [[ -z ${TMUX_PANE-} || ${pane_id} != "${TMUX_PANE}" ]] \
        || die "Error: Refusing to target the agent's own pane (${pane_id})." \
               $'\n'"Use a different window/pane."

    local sf lock
    sf=$(state_file "${pane_id}")
    lock="${STATE_DIR}/${pane_id//%/}.lock"

    if [[ -n ${pattern} ]]; then
        exec_interactive "${pane_id}" "${sf}" "${lock}" "${target}" \
                         "${command}" "${pattern}" "${timeout}" "${sock[@]}"
    else
        exec_shell "${pane_id}" "${sf}" "${lock}" "${target}" \
                   "${command}" "${timeout}" "${sock[@]}"
    fi
}

# ── shell mode: wait-for + file redirection ──────────────────────────────

exec_shell() {
    local pane_id=$1 sf=$2 lock=$3 target=$4 command=$5 timeout=$6
    shift 6
    local -a sock=( "$@" )

    (
        flock -x -w 5 200 \
            || die "Error: Another tmux-exec.sh is actively waiting on pane '${target}'."

        try_harvest_previous "${sf}" "${pane_id}" "${sock[@]}" || exit 1

        local id outfile ecfile channel
        id=$(date +%s%N)
        outfile=$(mktemp "${STATE_DIR}/out.XXXXXX")
        ecfile=$(mktemp "${STATE_DIR}/ec.XXXXXX")
        channel="tmux_exec_${id}"

        # Payload: run command with stdout+stderr to file, write exit code,
        # signal the wait-for channel.
        local payload
        # shellcheck disable=SC2016
        printf -v payload \
            '{ %s ; } > %q 2>&1; echo $? > %q; tmux wait-for -S %s' \
            "${command}" "${outfile}" "${ecfile}" "${channel}"

        write_state "${sf}" "${channel}" "${command}" "shell" "${outfile}" "${ecfile}"

        tmux "${sock[@]}" send-keys -t "${pane_id}" C-u
        tmux "${sock[@]}" send-keys -t "${pane_id}" -l -- "${payload}"
        tmux "${sock[@]}" send-keys -t "${pane_id}" C-m

        # Release flock — state file guards against concurrent use now.
        flock -u 200

        # ── wait for completion ──────────────────────────────────────
        # tmux wait-for exits 0 even when killed, so we can't branch on
        # wait's return code.  Instead, after wait returns we check whether
        # the command actually finished (ecfile written) or not (timeout /
        # pane death).
        local wait_pid
        tmux "${sock[@]}" wait-for "${channel}" &
        wait_pid=$!

        if (( timeout > 0 )); then
            # Watchdog: kill the waiter after $timeout seconds.
            (
                sleep "${timeout}"
                kill "${wait_pid}" 2>/dev/null
            ) &
            local watchdog_pid=$!

            wait "${wait_pid}" 2>/dev/null || true
            kill "${watchdog_pid}" 2>/dev/null || true
            wait "${watchdog_pid}" 2>/dev/null || true

            if [[ ! -s ${ecfile} ]]; then
                # Command did not finish — timeout.
                warn "Timeout after ${timeout}s — command is STILL RUNNING in the pane."
                warn "The pane is marked busy until the command finishes."
                warn "Use tmux-read.sh to check progress, or:  tmux send-keys -t '${pane_id}' C-c"
                exit 124
            fi
        else
            # No timeout — monitor liveness so we don't block forever
            # if the pane dies.
            (
                while pane_alive "${pane_id}" "${sock[@]}"; do
                    sleep 2
                done
                kill "${wait_pid}" 2>/dev/null
            ) &
            local liveness_pid=$!

            wait "${wait_pid}" 2>/dev/null || true
            kill "${liveness_pid}" 2>/dev/null || true
            wait "${liveness_pid}" 2>/dev/null || true

            if [[ ! -s ${ecfile} ]]; then
                # Pane died before command finished.
                clear_state "${sf}" "${outfile}" "${ecfile}"
                die "Error: Pane '${target}' (${pane_id}) died while command was running." \
                    $'\n'"Use tmux-list.sh to see available panes."
            fi
        fi

        # ── harvest ──────────────────────────────────────────────────
        local ec=0
        if [[ -s ${ecfile} ]]; then
            ec=$(<"${ecfile}")
        fi

        if [[ -s ${outfile} ]]; then
            cat -- "${outfile}"
        fi

        clear_state "${sf}" "${outfile}" "${ecfile}"
        exit "${ec}"
    ) 200>"${lock}"
}

# ── interactive mode: polling (for REPLs where wait-for can't be used) ───

exec_interactive() {
    local pane_id=$1 sf=$2 lock=$3 target=$4 command=$5 pattern=$6 timeout=$7
    shift 7
    local -a sock=( "$@" )

    (
        flock -x -w 5 200 \
            || die "Error: Another tmux-exec.sh is actively waiting on pane '${target}'."

        try_harvest_previous "${sf}" "${pane_id}" "${sock[@]}" || exit 1

        write_state "${sf}" "" "${command}" "interactive" "" ""

        tmux "${sock[@]}" send-keys -t "${pane_id}" C-u
        tmux "${sock[@]}" send-keys -t "${pane_id}" -l -- "${command}"
        tmux "${sock[@]}" send-keys -t "${pane_id}" C-m

        flock -u 200

        local start_t
        printf -v start_t '%(%s)T' -1

        while true; do
            if (( timeout > 0 )); then
                local now
                printf -v now '%(%s)T' -1
                if (( now - start_t > timeout )); then
                    warn "Timeout after ${timeout}s — interactive command still running."
                    exit 124
                fi
            fi

            if ! pane_alive "${pane_id}" "${sock[@]}"; then
                rm -f -- "${sf}"
                die "Error: Pane '${target}' (${pane_id}) died."
            fi

            local buffer
            buffer=$(tmux "${sock[@]}" capture-pane -t "${pane_id}" -p -S -500 2>/dev/null) || true

            if [[ ${buffer} =~ ${pattern} ]]; then
                rm -f -- "${sf}"
                exit 0
            fi

            sleep 0.2
        done
    ) 200>"${lock}"
}

main "$@"
