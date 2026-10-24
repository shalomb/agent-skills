> Scripts: `$SKILL_SCRIPTS` = `$(dirname <path-to-SKILL.md>)/scripts`. See `SKILL.md`.

# Execute (`scripts/tmux-exec.sh`)

Primary tool.  Sends a command, waits for completion, returns output + exit code.

### Shell Mode (default)
```bash
# SKILL_SCRIPTS = $(dirname <path-to-this-SKILL.md>)/scripts
$SKILL_SCRIPTS/tmux-exec.sh "1.0" "ls -la"
```

### Interactive Mode (`-w PATTERN`)
Sends keys and waits for a regex (e.g. a REPL prompt):
```bash
$SKILL_SCRIPTS/tmux-exec.sh -w '>>> ' "1.0" "print('hello')"
```

### Detached Mode (`-d`) — REPLs, debuggers, agent CLIs
Launches a long-lived foreground process without waiting for it to exit and
without marking the pane busy.  Combine with `-w` to wait until the process
is actually ready:

```bash
# launch, confirming the prompt appears
$SKILL_SCRIPTS/tmux-exec.sh -d -t 20 -w '>>> ' "1.0" 'PYTHON_BASIC_REPL=1 python3 -q'

# then drive it
$SKILL_SCRIPTS/tmux-exec.sh -w '>>> ' "1.0" "print('hello')"
```

Use `-d` for anything that takes over the pane and is not expected to return
(`python3`, `lldb`, `claude`, `sqlite3`).  Without it, shell mode waits
forever for an exit code the process never produces, and the pane stays
marked busy.

### Options
| Flag | Default | Meaning |
|------|---------|---------|
| `-t SEC` | none (wait forever) | Timeout.  On expiry the command is **still running** and the pane is marked busy. |
| `-w PATTERN` | — | Interactive mode: wait for regex instead of exit-code markers. |
| `-d` | off | Detached: launch a long-lived process; don't wait, don't mark busy. |
| `-S PATH` | — | Custom tmux socket. |

> **Prompt patterns and trailing spaces.** tmux strips trailing whitespace
> from captured lines, so `-w '>>> '` cannot match a *bare* prompt on its own.
> `tmux-exec.sh` compensates by retrying such patterns anchored to the end of
> the buffer, so `'>>> '` and `'(gdb) '` work as written.  Note that patterns
> are regexes: `(gdb)` is a capture group matching `gdb`, so prefer
> `-w '\(gdb\) '` if you need the parentheses matched literally.

### Busy-pane protection

If a previous command is still running (e.g. after a timeout), the script detects this from its state file before proceeding:
- **Command finished** → state is cleared, new command proceeds.
- **Command still running** → error with command name, elapsed time, and recovery options.

## ⚠️ Critical Limitation: tmux-exec.sh Runs in a Subshell

`tmux-exec.sh` wraps every command in a **new subshell** inside the pane. This means:

- Environment variables set inside the command (`export FOO=bar`) **do not persist** to the pane's parent shell after the command exits.
- Commands that `source` credentials into the shell (e.g. `aws-login`, `eval $(...)`, `. ~/.env`) will appear to succeed but **have no effect** on subsequent `tmux-exec.sh` calls.

**Rule:** For any command that must mutate the pane's shell environment, use raw
`tmux send-keys` to type directly into the pane's own shell, then scrape the output
with `tmux-read.sh` once the prompt returns:

```bash
# WRONG — tmux-exec.sh ALWAYS uses a subshell, even with -w.
# aws-login sources creds into that subshell, which exits immediately.
# The pane's parent shell never sees the credentials.
$SKILL_SCRIPTS/tmux-exec.sh "1.0" "aws-login my-account"       # subshell, creds lost
$SKILL_SCRIPTS/tmux-exec.sh -w '\$' "1.0" "aws-login my-account"  # still a subshell!

# CORRECT — type directly into the pane's own shell via send-keys
SESSION=$(tmux display-message -p '#{session_name}')
tmux send-keys -t "${SESSION}:1.0" "aws-login my-account" Enter
sleep 5   # allow login to complete (adjust for slow SSO)
$SKILL_SCRIPTS/tmux-read.sh "1.0"   # scrape output to confirm success
```

After the pane's shell has credentials set via send-keys, subsequent `tmux-exec.sh`
calls for AWS CLI queries work fine — those subshells inherit the pane's exported
env vars. Only the credential-sourcing step itself requires send-keys.

## Pane Rendering

Commands appear in the pane as ordinary shell syntax, one statement per line:

```
λ (
  echo building;
  make --version | head -2;
  echo done
)
building
GNU Make 4.4.1
done
```

`λ` is an alias ending in `time` (a reserved word, so it accepts a subshell as
a prefix operand and propagates its exit status). Output capture and exit-code
recording are handled by the alias and a `PROMPT_COMMAND` hook installed once
per pane — so nothing but the command itself is on the line. The helper is
injected lazily and re-injected if a pane's shell restarts; no setup required.
