# TFC: use the CLI first

Read before any Terraform Cloud read or write.

## Order

1. **A `tfc` subcommand.** `tfc` is the CLI of [terrapyne](https://github.com/shalomb/terrapyne). Install: `uv tool install git+https://github.com/shalomb/terrapyne`.
2. **`tfc api <endpoint>`** only when no subcommand does the job. It reuses the `tfc` token and organisation.
3. **`http` (httpie) or `curl`** only when `tfc` is not installed.

Use the subcommands, not `tfc api` as a router. Subcommands resolve names to IDs, check input, and know traps such as VCS-run queueing. Raw JSON:API bodies do not.

## Habits

- Find with a server-side search: `tfc -q workspace list -o <org> -s <text>`. Do not list all and filter.
- `-q` gives data only. Piped output is JSON: use `jq`.
- `tfc <group> <cmd> --help` lists the options. Read it before you fall back.
- Dry run where offered (`tfc vcs set-repo --dry-run`).

## Map: job to command

| Job | Command |
|---|---|
| Find workspaces | `tfc -q workspace list -o <org> -s <text>` |
| Show one workspace, its variables | `tfc workspace show <ws> -o <org>` · `tfc workspace variables <ws>` |
| Clone a workspace | `tfc workspace clone <src> <dst> -o <org> [--no-with-variables] [--no-with-vcs]` |
| Rename, working directory, Terraform version, execution mode, project | `tfc workspace update <ws> -n <new> --working-dir <dir> --tf-version <v> -m agent --project-name <p>` |
| Connect VCS, set branch | `tfc vcs set-repo <ws> <org/repo> --dry-run` · `tfc workspace set-branch <ws> <branch>` |
| Set, remove, copy a variable | `tfc workspace var set <ws> -k <key> -v <value> -c env [--sensitive]` · `tfc workspace var-rm <ws> <key>` · `tfc workspace var-copy <src> <dst>` |
| Variable sets | `tfc varset list` · `tfc varset show <name>` |
| Lock, unlock | `tfc workspace lock <ws>` · `tfc workspace unlock <ws>` |
| Run triggers between workspaces | `tfc workspace triggers list/add/remove` |
| List runs | `tfc -q run list -w <ws> -o <org> -f json` |
| Start a plan | `tfc run trigger <ws> -o <org> -m "<why>" --no-wait` |
| Wait for a run | `tfc run watch <run-id>` · after a push: `tfc run watch -w <ws> --wait-vcs` |
| Read a failure | `tfc run logs <run-id> --stage plan -d` · `tfc run diagnostics <run-id>` · `tfc run errors <project>` |
| Health of a workspace | `tfc workspace health <ws>` |
| State and outputs | `tfc state outputs -w <ws>` |

## Gaps: use `tfc api`

No subcommand sets these today:

- Workspace tags: `POST` or `DELETE /workspaces/<id>/relationships/tags`.
- Description, `auto-apply`, `queue-all-runs`: `PATCH /workspaces/<id>`.

When you fill a gap, raise an issue on terrapyne so the gap closes.

## Traps

- **A VCS-connected workspace refuses `run trigger`.** Push to the branch, then `tfc run watch -w <ws> --wait-vcs`.
- **A new workspace has `queue-all-runs` off.** Pushes queue no run until a first run exists. Start the first one with `tfc run trigger <ws> --force`.
- **A workspace variable overrides a variable set of the same key.** Do not copy variables such as `TFC_VAULT_*` from a clone source when a variable set provides them.
- **`workspace clone` drops tags.** Add them again after the clone.
