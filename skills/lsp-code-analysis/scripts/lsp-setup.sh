#!/usr/bin/env bash
# lsp-setup.sh — install and patch lsp-cli for use with Mason-installed language servers.
#
# Applies local workarounds for upstream bugs in lsp-cli@0.4.0:
#   1. manager/__main__.py: manager murder-chain (every lsp invocation kills the previous manager)
#   2. cli/outline.py:      OutlineRequest field rename (file_path → path) in newer lsap-sdk
#   3. lsp-client/lang.py:  pyrefly default broken; use pyright instead
#   4. LSAP submodule:      pinned to bdd8d2c (before Symbol→Inspect rename breaks lsp-cli@0.4.0)
#
# PRs filed upstream:
#   lsp-client/lsp-skill#XXX  — manager murder-chain + outline field rename
#   lsp-client/lsp-client#XXX — pyrefly default
#
# Re-run after: uv tool upgrade lsp-cli

set -euo pipefail

MASON_BIN="${HOME}/.local/share/nvim/mason/bin"
LSP_SKILL_REPO="${HOME}/.cache/checkouts/github.com/lsp-client/lsp-skill"
LSAP_DIR="${LSP_SKILL_REPO}/packages/LSAP"
LSP_CLIENT_DIR="${LSP_SKILL_REPO}/packages/lsp-client"

die()  { printf 'Error: %s\n' "$*" >&2; exit 1; }
info() { printf '  %s\n' "$*"; }

# ── Step 1: ensure Mason's pyright-langserver is on PATH ─────────────────────
export PATH="${MASON_BIN}:${PATH}"
command -v pyright-langserver >/dev/null 2>&1 \
    || die "pyright-langserver not found in ${MASON_BIN}. Install via Mason: :MasonInstall pyright"
info "pyright-langserver: OK ($(readlink -f "$(command -v pyright-langserver)" 2>/dev/null || echo found))"

# ── Step 2: ensure repo + submodules are checked out ─────────────────────────
if [[ ! -d ${LSP_SKILL_REPO}/.git ]]; then
    die "lsp-skill repo not found at ${LSP_SKILL_REPO}. Run: librarian checkout lsp-client/lsp-skill"
fi

# LSAP: pin to bdd8d2c (last commit before Symbol→Inspect rename, compatible with lsp-cli@0.4.0)
if [[ ! -f ${LSAP_DIR}/pyproject.toml ]]; then
    git -C "${LSP_SKILL_REPO}" submodule update --init packages/LSAP packages/lsp-client
fi
LSAP_HEAD=$(git -C "${LSAP_DIR}" rev-parse HEAD 2>/dev/null || true)
if [[ ${LSAP_HEAD} != bdd8d2c* ]]; then
    info "Checking out LSAP@bdd8d2c (pre Symbol→Inspect rename)..."
    git -C "${LSAP_DIR}" fetch origin 2>/dev/null || true
    git -C "${LSAP_DIR}" checkout bdd8d2c
fi

# lsp-client: ensure pyright (not pyrefly) is the Python default
LC_LANG="${LSP_CLIENT_DIR}/src/lsp_client/clients/lang.py"
if grep -q '"python": PyreflyClient' "${LC_LANG}" 2>/dev/null; then
    info "Patching lsp-client/lang.py: PyreflyClient → PyrightClient..."
    sed -i 's/from .pyrefly import PyreflyClient/from .pyrefly import PyreflyClient\nfrom .pyright import PyrightClient/' "${LC_LANG}"
    sed -i 's/PythonClient = PyreflyClient/PythonClient = PyrightClient/' "${LC_LANG}"
    sed -i 's/"python": PyreflyClient/"python": PyrightClient/' "${LC_LANG}"
fi

# ── Step 3: install lsp-cli from source with patched submodules ───────────────
printf 'Installing lsp-cli from source...\n'
uv tool install --python 3.13 \
    "${LSP_SKILL_REPO}" \
    --with "lsap-sdk @ ${LSAP_DIR}" \
    --with "lsp-client @ ${LSP_CLIENT_DIR}" \
    --force 2>&1 | tail -3

SITE=$(find "${HOME}/.local/share/uv/tools/lsp-cli" \
    -name 'site-packages' -type d 2>/dev/null | head -1)
[[ -n ${SITE} ]] || die "Could not find lsp-cli site-packages"

# ── Step 4: patch manager/__main__.py (murder-chain fix) ─────────────────────
MANAGER_MAIN="${SITE}/lsp_cli/manager/__main__.py"
if grep -q 'shutdown previous manager' "${MANAGER_MAIN}" 2>/dev/null; then
    info "Patching manager/__main__.py: remove manager murder-chain..."
    cat > "${MANAGER_MAIN}" << 'PYEOF'
import anyio
import uvicorn

from lsp_cli.settings import MANAGER_UDS_PATH
from lsp_cli.utils.socket import is_socket_alive
from lsp_cli.utils.uds import open_uds

from .manager import app


async def main() -> None:
    # Guard: if a manager is already running, do nothing.
    # Without this, concurrent lsp invocations each spawn a manager that kills
    # the previous one (murder chain), causing every call to take ~15s.
    # See: https://github.com/lsp-client/lsp-skill/issues/XXX
    if await is_socket_alive(MANAGER_UDS_PATH):
        return

    async with open_uds(MANAGER_UDS_PATH):
        config = uvicorn.Config(app, uds=str(MANAGER_UDS_PATH), loop="asyncio")
        server = uvicorn.Server(config)
        await server.serve()


if __name__ == "__main__":
    anyio.run(main)
PYEOF
fi

# ── Step 5: patch cli/outline.py (OutlineRequest field rename) ───────────────
OUTLINE="${SITE}/lsp_cli/cli/outline.py"
if grep -q 'file_path=file_path.resolve()' "${OUTLINE}" 2>/dev/null; then
    info "Patching cli/outline.py: file_path → path in OutlineRequest..."
    sed -i 's/file_path=file_path.resolve()/path=file_path.resolve()/' "${OUTLINE}"
fi

# ── Step 6: write user config ─────────────────────────────────────────────────
CONFIG="${HOME}/.config/lsp-cli/config.toml"
if [[ ! -f ${CONFIG} ]]; then
    info "Writing ~/.config/lsp-cli/config.toml..."
    mkdir -p "$(dirname "${CONFIG}")"
    cat > "${CONFIG}" << 'TOML'
# No artificial delay before serving requests
warmup_time = 0.0

# Keep pyright warm for 30s after last request
idle_timeout = 30
TOML
fi

# ── Verify ────────────────────────────────────────────────────────────────────
printf '\nVerifying...\n'
export PATH="${MASON_BIN}:${PATH}"
lsp server shutdown 2>/dev/null || true
sleep 0.3

# Smoke test: find any Python file in the current directory tree
TEST_FILE=$(find . -name '*.py' ! -path '*/test*' ! -path '*/__pycache__/*' \
    -type f 2>/dev/null | { head -1; cat > /dev/null; } || true)

if [[ -n ${TEST_FILE} ]]; then
    result=$(timeout 15 lsp outline "${TEST_FILE}" 2>&1) || true
    if printf '%s\n' "${result}" | grep -q '^#'; then
        printf '  lsp outline: OK\n'
    else
        printf '  lsp outline: FAILED (no Python files in current dir, or lsp error)\n'
        printf '%s\n' "${result}" >&2
    fi
else
    printf '  lsp outline: SKIPPED (no Python files in current directory)\n'
    printf '  Test manually: lsp outline <file.py> --project <project_root>\n'
fi

printf '\nDone. lsp-cli is ready. Average response time: ~2s\n'
# shellcheck disable=SC2016
printf 'Add to PATH: export PATH="%s:$PATH"\n' "${MASON_BIN}"
