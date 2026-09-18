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
	Usage: tmux-exec.sh [-d] [-w PATTERN] [-t TIMEOUT] [-S SOCKET] TARGET COMMAND

	Send COMMAND to a tmux pane and wait for completion.

	TARGET format:
	  {session}:{window}.{pane}   fully qualified
	  {window}.{pane}             current session (from $TMUX)

	Options:
	  -t SEC       Timeout in seconds (default: no timeout — waits forever).
	  -w PATTERN   Interactive mode — send keys and poll for PATTERN regex
	               instead of using wait-for synchronisation.
	  -d           Detached — launch a long-lived foreground process (REPL,
	               debugger, agent CLI) without waiting for it to exit and
	               without marking the pane busy.  Combine with -w to wait
	               for the process to become ready.  Drive it afterwards
	               with -w calls.
	  -S PATH      Custom tmux socket path.

	Examples:
	  # run a command and collect its output + exit code
	  tmux-exec.sh 1.0 'make test'

	  # launch a REPL, waiting until its prompt appears, then drive it
	  tmux-exec.sh -d -w '>>> ' 1.0 'PYTHON_BASIC_REPL=1 python3 -q'
	  tmux-exec.sh -w '>>> ' 1.0 "print('hello')"

	Exit codes:
	  <N>   Command's own exit code (shell mode).
	  0     Pattern matched (interactive mode), or launched (detached).
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

# Does the pane's visible text match PATTERN?
#
# tmux strips trailing whitespace from every captured line, so a natural
# prompt pattern like '>>> ' or '(gdb) ' can NEVER match a bare prompt —
# the space the user typed is exactly the character tmux removed.  It only
# appears to work when something has already been typed after the prompt,
# which makes the failure intermittent and deeply confusing.
#
# A pattern with trailing whitespace is therefore also tried with that
# whitespace anchored to end-of-line.  Patterns without trailing whitespace
# are unaffected.
buffer_matches() {
    local buffer=$1 pattern=$2

    [[ ${buffer} =~ ${pattern} ]] && return 0

    # Pattern has no trailing whitespace → nothing more to try.
    local trimmed=${pattern%"${pattern##*[![:space:]]}"}
    [[ ${trimmed} != "${pattern}" && -n ${trimmed} ]] || return 1

    # Retry anchored at the end of the buffer.  Anchoring matters: a prompt
    # is "ready" only when it is the last thing on screen, so matching it in
    # older scrollback would be a false positive.
    [[ ${buffer} =~ ${trimmed}[[:space:]]*$ ]]
}

pane_alive() {
    local pane_id=$1; shift
    local result
    result=$(tmux "$@" display-message -p -t "${pane_id}" '#{pane_id}' 2>/dev/null) || return 1
    [[ ${result} == "${pane_id}" ]]
}

# ── state management ─────────────────────────────────────────────────────

write_state() {
    local sf=$1 channel=$2 command=$3 mode=$4 outfile=$5 ecfile=$6
    # command= must stay on ONE line: read_state parses line-by-line, so any
    # embedded newline would be misread as a bogus key=value pair.
    local summary=${command//$'\n'/ }
    (( ${#summary} > 200 )) && summary="${summary:0:197}..."
    printf 'channel=%s\ncommand=%s\nmode=%s\noutfile=%s\necfile=%s\nstarted=%(%s)T\npid=%d\n' \
        "${channel}" "${summary}" "${mode}" "${outfile}" "${ecfile}" -1 $$ > "${sf}"
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

# ── pane-side helper ─────────────────────────────────────────────────────
#
# The pane runs commands as:
#
#   λ (
#     <command>;
#   )
#
# λ is an ALIAS ending in `time`.  That matters: `time` is a bash reserved
# word, not a builtin, so it takes a whole pipeline — including a subshell —
# as its operand in PREFIX position, and passes the operand's exit status
# straight through.  An alias ending in `time` inherits that grammar, which a
# plain function cannot: `λ ( ... )` is a syntax error for a function.
#
# The upshot is that the command appears in the pane as real, executable
# shell syntax — no comment marker, no trailing redirection, nothing to
# mentally strip out.  Everything else is hidden:
#
#   __txo      runs before `time`, points fd1/fd2 at a tee for this job
#   __txprompt runs from PROMPT_COMMAND, restores the fds and records $?
#
# The exit code is taken in PROMPT_COMMAND rather than from a trailing
# element after the command: `time` propagates the subshell's status to the
# prompt hook intact, so the visible line needs no tail to record it.
readonly HELPER_FN='λ'
readonly HELPER_FILE="${STATE_DIR}/helper.sh"

write_helper() {
    cat > "${HELPER_FILE}" <<-'EOF'
	shopt -s expand_aliases

	# Opens capture for the pending job.  The id arrives out-of-band via
	# next.<pane>, so the visible line carries no ids or paths.
	__txo(){
	  local d="${TMUX_EXEC_DIR}" p="${TMUX_PANE//%/}"
	  __TX_ID=$(<"${d}/next.${p}") || return 1
	  exec 3>&1 4>&2
	  exec > >(tee "${d}/out.${__TX_ID}") 2>&1
	}

	# Closes capture and records the exit status.
	__txprompt(){
	  local ec=$?
	  [[ -n ${__TX_ID-} ]] || return 0
	  exec 1>&3 2>&4 3>&- 4>&-
	  echo "${ec}" > "${TMUX_EXEC_DIR}/ec.${__TX_ID}"
	  tmux wait-for -S "tmux_exec_${__TX_ID}" 2>/dev/null
	  unset __TX_ID
	}

	# PREPEND, never clobber: panes often already carry prompt hooks (prompt
	# timing, systemd OSC context).  Going first also means the fds are
	# restored before those hooks emit terminal escapes, which would
	# otherwise be captured into the output file.
	if [[ $(declare -p PROMPT_COMMAND 2>/dev/null) == 'declare -a'* ]]; then
	  PROMPT_COMMAND=(__txprompt "${PROMPT_COMMAND[@]}")
	else
	  PROMPT_COMMAND="__txprompt${PROMPT_COMMAND:+;${PROMPT_COMMAND}}"
	fi

	TIMEFORMAT=''

	# Commands are sent split across lines, so the pane sits in a PS2
	# continuation while reading them.  Blanking PS2 once here keeps the
	# body flush-left instead of prefixed with `>` markers — and avoids
	# save/restore scaffolding on every command line.
	PS2=''

	alias λ='__txo; time'
	EOF
}

# Define the helper in the pane if it is missing.  Re-sent whenever absent,
# so a restarted shell or a fresh pane self-heals with no user setup.
ensure_helper() {
    local pane_id=$1; shift
    local -a sock=( "$@" )

    local probe
    probe=$(mktemp "${STATE_DIR}/probe.XXXXXX")

    # Trailing `clear` keeps this bookkeeping out of the visible pane.
    tmux "${sock[@]}" send-keys -t "${pane_id}" C-u
    tmux "${sock[@]}" send-keys -t "${pane_id}" -l -- \
        "declare -F ${HELPER_FN} >/dev/null 2>&1; echo \$? > ${probe}; clear"
    tmux "${sock[@]}" send-keys -t "${pane_id}" C-m

    # Wait briefly for the probe to land; a busy or wedged pane just falls
    # through to a re-definition, which is harmless.
    local i
    # shellcheck disable=SC2034  # loop counter is intentionally unused
    for i in {1..25}; do
        [[ -s ${probe} ]] && break
        sleep 0.1
    done

    local defined=1
    [[ -s ${probe} ]] && defined=$(<"${probe}")
    rm -f -- "${probe}"

    (( defined == 0 )) && return 0

    write_helper
    tmux "${sock[@]}" send-keys -t "${pane_id}" C-u
    tmux "${sock[@]}" send-keys -t "${pane_id}" -l -- \
        "TMUX_EXEC_DIR=${STATE_DIR}; . ${HELPER_FILE}; clear"
    tmux "${sock[@]}" send-keys -t "${pane_id}" C-m
    return 0
}

# Lay the command out one statement per line, indented two spaces.
#
# Splits ONLY on top-level `;` and existing newlines.  A `;` inside quotes,
# `$( )`, backticks or `${ }` is part of the command's data and must survive
# untouched — splitting there would change what runs, not just how it looks.
# Nothing is added or removed apart from whitespace between statements.
indent_body() {
    local s=$1 out='' line='' c prev='' i
    local sq=0 dq=0 esc=0 depth=0

    for (( i = 0; i < ${#s}; i++ )); do
        c=${s:i:1}

        if (( esc )); then line+=${c}; esc=0; prev=${c}; continue; fi

        case ${c} in
            '\') line+=${c}; (( sq )) || esc=1 ;;
            "'") (( dq )) || sq=$(( ! sq )); line+=${c} ;;
            '"') (( sq )) || dq=$(( ! dq )); line+=${c} ;;
            '(')  (( sq || dq )) || { [[ ${prev} == '$' ]] && (( depth++ )); }
                  line+=${c} ;;
            '`')  (( sq )) || dq=${dq}; line+=${c} ;;
            '{')  (( sq || dq )) || { [[ ${prev} == '$' ]] && (( depth++ )); }
                  line+=${c} ;;
            ')'|'}') (( sq || dq )) || (( depth > 0 )) && (( depth-- )) || :
                  line+=${c} ;;
            ';')
                if (( sq || dq || depth )); then
                    line+=${c}
                else
                    line+=${c}
                    while [[ ${line} == [[:space:]]* ]]; do line=${line#?}; done
                    out+="  ${line}"$'\n'
                    line=''
                fi
                ;;
            $'\n')
                if (( sq || dq || depth )); then
                    line+=${c}
                else
                    while [[ ${line} == [[:space:]]* ]]; do line=${line#?}; done
                    [[ -n ${line} ]] && out+="  ${line}"$'\n'
                    line=''
                fi
                ;;
            *) line+=${c} ;;
        esac
        prev=${c}
    done

    while [[ ${line} == [[:space:]]* ]]; do line=${line#?}; done
    [[ -n ${line} ]] && out+="  ${line}"
    printf '%s' "${out%$'\n'}"
}

clear_state() {
    local sf=$1 outfile=$2 ecfile=$3
    rm -f -- "${sf}" "${outfile}" "${ecfile}"
}

# ── main ─────────────────────────────────────────────────────────────────

main() {
    local timeout=0 pattern='' detach=0 sock=()

    while getopts ':w:t:S:d' opt; do
        case ${opt} in
            w) pattern=${OPTARG} ;;
            t) timeout=${OPTARG} ;;
            d) detach=1 ;;
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

    if (( detach )); then
        exec_detached "${pane_id}" "${sf}" "${lock}" "${target}" \
                      "${command}" "${pattern}" "${timeout}" "${sock[@]}"
    elif [[ -n ${pattern} ]]; then
        exec_interactive "${pane_id}" "${sf}" "${lock}" "${target}" \
                         "${command}" "${pattern}" "${timeout}" "${sock[@]}"
    else
        exec_shell "${pane_id}" "${sf}" "${lock}" "${target}" \
                   "${command}" "${timeout}" "${sock[@]}"
    fi
}

# ── shell mode: poll-based (resilient to caller interruption) ────────────
#
# Replaces the tmux wait-for blocking approach with ecfile polling.
# The pane still emits `tmux wait-for -S` in its payload (harmless if
# nobody listens), but the caller polls the ecfile every POLL_INTERVAL
# seconds instead of blocking.  This means:
#
#   • The pi tool-caller can kill this process at any point without
#     leaving a "busy" pane — the next call auto-harvests via
#     try_harvest_previous once the pane writes the ecfile.
#   • No more "Command aborted" false-negatives for long-running commands.

exec_shell() {
    local pane_id=$1 sf=$2 lock=$3 target=$4 command=$5 timeout=$6
    shift 6
    local -a sock=( "$@" )
    local POLL_INTERVAL=2

    (
        flock -x -w 5 200 \
            || die "Error: Another tmux-exec.sh is actively waiting on pane '${target}'."

        try_harvest_previous "${sf}" "${pane_id}" "${sock[@]}" || exit 1

        # One short id names both files; the pane never sees either path.
        local id outfile ecfile channel
        outfile=$(mktemp "${STATE_DIR}/out.XXXXXX")
        id=${outfile##*/out.}
        [[ -n ${id} && ${id} != "${outfile}" ]] \
            || { rm -f -- "${outfile}"; die "Error: could not derive job id from '${outfile}'."; }
        ecfile="${STATE_DIR}/ec.${id}"
        channel="tmux_exec_${id}"
        : > "${ecfile}"

        ensure_helper "${pane_id}" "${sock[@]}"

        # Hand the job id to the pane out-of-band so the visible line needs
        # no arguments.  Written under the flock, before the keys are sent.
        printf '%s' "${id}" > "${STATE_DIR}/next.${pane_id//%/}"

        # The command goes into the pane verbatim as `time`'s operand — real
        # syntax, executed as typed.
        #
        # A SUBSHELL `( … )`, not a brace group: the skill documents that
        # tmux-exec.sh always runs commands in a subshell, so `cd`/`export`
        # must not leak into the pane.  `{ … }` runs in the current shell,
        # which also means a command ending in `exit` would kill the pane
        # outright.  `( … )` keeps `time`'s exit-status propagation while
        # containing both hazards.  No terminator needed before `)`.
        #
        # Laid out one statement per line — newline after `(`, after each
        # top-level `;`, and before `)` — so long commands stay readable in
        # a narrow split.  PS2 is blanked by the helper, so the body renders
        # flush-left with no continuation markers.
        local payload
        printf -v payload '%s (\n%s\n)' "${HELPER_FN}" "$(indent_body "${command}")"

        write_state "${sf}" "${channel}" "${command}" "shell" \
                    "${outfile}" "${ecfile}"

        tmux "${sock[@]}" send-keys -t "${pane_id}" C-u
        tmux "${sock[@]}" send-keys -t "${pane_id}" -l -- "${payload}"
        tmux "${sock[@]}" send-keys -t "${pane_id}" C-m

        # Release flock — state file guards against concurrent use now.
        flock -u 200

        # ── poll for completion ──────────────────────────────────────
        # Poll ecfile every POLL_INTERVAL seconds.  If this process is
        # killed by the caller (e.g. pi tool timeout), the pane keeps
        # running and writes ecfile on completion.  The NEXT call to
        # tmux-exec.sh will auto-harvest via try_harvest_previous.
        local start_t
        printf -v start_t '%(%s)T' -1

        while true; do
            # Done?
            [[ -s ${ecfile} ]] && break

            # Timeout?
            if (( timeout > 0 )); then
                local now; printf -v now '%(%s)T' -1
                if (( now - start_t >= timeout )); then
                    warn "Timeout after ${timeout}s — command is STILL RUNNING in the pane."
                    warn "Call tmux-exec.sh again on the same pane to auto-harvest the result."
                    warn "Or check progress:  tmux-read.sh '${target}'"
                    exit 124
                fi
            fi

            # Pane died?
            if ! pane_alive "${pane_id}" "${sock[@]}"; then
                [[ -s ${ecfile} ]] && break
                clear_state "${sf}" "${outfile}" "${ecfile}"
                die "Error: Pane '${target}' (${pane_id}) died while command was running." \
                    $'\n'"Use tmux-list.sh to see available panes."
            fi

            sleep "${POLL_INTERVAL}"
        done

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

# ── detached mode: launch a long-lived foreground process ────────────────
#
# For REPLs, debuggers and agent CLIs — anything that takes over the pane and
# is not expected to exit.  Shell mode cannot express this: it waits for the
# exit code, which a process that never returns to the prompt never writes,
# so the launcher blocks and the pane stays marked busy forever.
#
# Differences from shell mode:
#   • The command is sent RAW, not wrapped in `λ ( … )`.  The process must own
#     the pane's foreground and keep its stdin attached to the terminal, so it
#     can be driven afterwards with -w.  Wrapping would also capture output
#     into a file that is never closed.
#   • No state file is written, so the pane is never marked busy and later
#     -w calls are free to drive the process.
#   • Nothing is harvested: there is no exit code to collect.
#
# With -w, waits for PATTERN to confirm the process came up before returning,
# which turns "launch and hope" into a checked step.
exec_detached() {
    local pane_id=$1 sf=$2 lock=$3 target=$4 command=$5 pattern=$6 timeout=$7
    shift 7
    local -a sock=( "$@" )

    (
        flock -x -w 5 200 \
            || die "Error: Another tmux-exec.sh is actively waiting on pane '${target}'."

        # Refuse to launch on top of a command that is still running.
        try_harvest_previous "${sf}" "${pane_id}" "${sock[@]}" || exit 1

        tmux "${sock[@]}" send-keys -t "${pane_id}" C-u
        tmux "${sock[@]}" send-keys -t "${pane_id}" -l -- "${command}"
        tmux "${sock[@]}" send-keys -t "${pane_id}" C-m

        flock -u 200

        [[ -n ${pattern} ]] || exit 0

        # Readiness check: wait for the process to announce itself.
        local start_t now buffer
        printf -v start_t '%(%s)T' -1

        while true; do
            if (( timeout > 0 )); then
                printf -v now '%(%s)T' -1
                if (( now - start_t >= timeout )); then
                    warn "Timeout after ${timeout}s waiting for '${pattern}' in pane '${target}'."
                    warn "The process may still be starting.  Check:  tmux-read.sh '${target}'"
                    exit 124
                fi
            fi

            if ! pane_alive "${pane_id}" "${sock[@]}"; then
                die "Error: Pane '${target}' (${pane_id}) died during launch."
            fi

            buffer=$(tmux "${sock[@]}" capture-pane -t "${pane_id}" -p -S -500 2>/dev/null) || true
            buffer_matches "${buffer}" "${pattern}" && exit 0

            sleep 0.2
        done
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

            if buffer_matches "${buffer}" "${pattern}"; then
                rm -f -- "${sf}"
                exit 0
            fi

            sleep 0.2
        done
    ) 200>"${lock}"
}

main "$@"
