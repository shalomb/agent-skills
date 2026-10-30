#!/usr/bin/env bash
# Install the /understand report server as systemd --user units.
#   install.sh --dry-run            print what would be done, change nothing
#   install.sh                      write ~/.config/systemd/user/understand-report-server@.service
#   install.sh --enable             also `systemctl --user enable --now` the parallels and tailnet instances
# Never uses sudo, never touches /etc or the system nginx.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$here${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m report_server install --python "$(command -v python3)" "$@"
