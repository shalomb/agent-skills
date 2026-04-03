# Upstream patches applied by lsp-setup.sh

`lsp-setup.sh` applies four patches on every install. They're wiped by
`uv tool upgrade lsp-cli` — re-run the setup script after any upgrade.

## 1. Manager murder-chain (15s per call)

**File**: `lsp_cli/manager/__main__.py`  
**Issue**: https://github.com/lsp-client/lsp-skill/issues/37

Every `lsp` invocation spawns a new manager process. The manager's
`__main__.py` unconditionally sends `POST /shutdown` to any existing manager
on startup (intended to clear stale sockets from crashed editor sessions).
When used as a CLI tool, concurrent invocations race: two processes both see
`is_socket_alive = False`, both spawn a manager, and each new manager kills
the previous. Per-call overhead: ~16s.

**Fix**: Check `is_socket_alive` first and return early if a manager is
already running. Full fix requires a `flock` around socket creation to close
the TOCTOU race window — see the issue for the complete patch.

## 2. OutlineRequest field rename

**File**: `lsp_cli/cli/outline.py`

`lsap-sdk` renamed the field `file_path` → `path` in `OutlineRequest`, but
`lsp-cli@0.4.0` wasn't updated. All `lsp outline` calls fail with a
pydantic validation error.

**Fix**: `sed` patch — `file_path=file_path.resolve()` → `path=file_path.resolve()`

## 3. pyrefly default (Python client exits immediately)

**File**: `lsp_client/clients/lang.py` (in the `lsp-client` submodule)

`lsp-client` main branch switched the Python language client default from
`PyrightClient` to `PyreflyClient`. pyrefly's LSP mode starts and immediately
exits without completing the handshake, causing all Python analysis to fail.

**Fix**: Patch `lang.py` to use `PyrightClient` as the Python default.

## 4. LSAP submodule pin

`lsp-cli@0.4.0` was written against LSAP before the `Symbol` capability was
renamed to `Inspect` (commit `bdd8d2c`). The pinned submodule commit in the
repo (`92b8e45`) isn't publicly accessible. The setup script checks out
`bdd8d2c` from the LSAP submodule's `main` branch.

**When resolved**: When `lsp-cli@0.5.0` targets the new LSAP API, the setup
script can be updated to install from PyPI and drop the submodule pins.
