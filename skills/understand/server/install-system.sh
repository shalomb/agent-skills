#!/usr/bin/env bash
# One-time root setup of the report server on the Debian system nginx (ADR 0007).
#   install-system.sh --dry-run     print every step, change nothing (no sudo)
#   install-system.sh               install; sudo prompts once
#   install-system.sh --uninstall   undo it (nginx goes back to masked)
# Run it as yourself, not as root: the config is rendered as you, then installed with sudo.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
conf=/etc/nginx/conf.d/agent-skills.conf
snippets=/etc/nginx/agent-skills.d
sudoers=/etc/sudoers.d/agent-skills-nginx
default_site=/etc/nginx/sites-enabled/default
default_target=/etc/nginx/sites-available/default
nginx=/usr/sbin/nginx
user="$(id -un)"
mode=install dry=0
for a in "$@"; do
  case "$a" in
    --dry-run) dry=1 ;;
    --uninstall) mode=uninstall ;;
    *) echo "usage: $0 [--dry-run] [--uninstall]" >&2; exit 2 ;;
  esac
done
[[ $EUID -ne 0 ]] || { echo "run as your own user, not root" >&2; exit 2; }

run() { echo "+ $*"; [[ $dry -eq 1 ]] || "$@"; }
render() { PYTHONPATH="$here" python3 -m report_server_system "$@"; }

if [[ $mode == uninstall ]]; then
  run sudo rm -f "$conf" "$sudoers"
  [[ ! -e $default_target || -e $default_site ]] || run sudo ln -s "$default_target" "$default_site"
  run sudo systemctl disable --now nginx
  run sudo systemctl mask nginx
  echo "uninstalled (content in $snippets was left alone)"
  exit 0
fi

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
render render >"$tmp/agent-skills.conf"
render sudoers --user "$user" >"$tmp/sudoers"
[[ $dry -eq 1 ]] || sudo true  # prompt once, up front

# Refuse to continue if something other than nginx already holds port 80.
holder="$(ss -ltnH 'sport = :80' 2>/dev/null | head -1 || true)"
if [[ -n $holder ]] && ! systemctl is-active --quiet nginx; then
  echo "port 80 is already in use: $holder" >&2; exit 1
fi

run sudo visudo -cf "$tmp/sudoers"
rollback() {
  echo "nginx -t failed; rolling back" >&2
  sudo rm -f "$conf"
  [[ ! -e $default_target || -e $default_site ]] || sudo ln -s "$default_target" "$default_site"
  exit 1
}
run sudo install -d -o "$user" -g "$(id -gn)" -m 755 "$snippets"
run sudo install -m 644 "$tmp/agent-skills.conf" "$conf"
# The stock default site also claims port 80 as default_server; ours replaces it.
run sudo rm -f "$default_site"
if [[ $dry -eq 1 ]]; then echo "+ sudo $nginx -t"; else sudo "$nginx" -t || rollback; fi
run sudo install -m 440 -o root -g root "$tmp/sudoers" "$sudoers"
run sudo systemctl unmask nginx
if [[ $dry -eq 0 ]] && systemctl is-active --quiet nginx; then
  run sudo systemctl reload nginx
else
  run sudo systemctl enable --now nginx
fi

if [[ $dry -eq 0 ]]; then
  python3 - <<'PY'
import urllib.request
status = urllib.request.urlopen("http://127.0.0.1/r/").status
print(f"check: http://127.0.0.1/r/ -> {status}")
PY
  echo "done. Add a vhost snippet in $snippets, then: sudo $nginx -t && sudo systemctl reload nginx"
fi
