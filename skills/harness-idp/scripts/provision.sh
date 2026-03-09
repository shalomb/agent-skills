#!/bin/bash

# Harness IDP Workflow Execution Wrapper
#
# Convenience script for executing Harness IDP Scaffolder workflows.
# Handles credential validation and delegates to Python implementation.
#
# Usage:
#   ./workflow.sh [-h|--help]
#   ./workflow.sh execute TEMPLATE_NAME [--param-name param-value] [OPTIONS]
#   ./workflow.sh monitor-task TASK_ID [OPTIONS]
#   ./workflow.sh get-task-status TASK_ID [OPTIONS]
#
# Examples:
#   ./workflow.sh execute MyTemplate --workspace-name prod-workspace --owner admin@example.com
#   ./workflow.sh execute MyTemplate --workspace-name prod-workspace --no-watch
#   ./workflow.sh monitor-task task-uuid-1234
#   ./workflow.sh get-task-status task-uuid-1234
#
# Environment Variables:
#   HARNESS_ACCOUNT_ID    Harness account ID (required)
#   HARNESS_API_KEY       Harness API key (required, keep secret)
#   HARNESS_BASE_URL      Optional custom Harness base URL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $*${NC}" >&2
}

log_success() {
    echo -e "${GREEN}✅ $*${NC}" >&2
}

log_warn() {
    echo -e "${YELLOW}⚠️  $*${NC}" >&2
}

log_error() {
    echo -e "${RED}❌ $*${NC}" >&2
}

# Show help
show_help() {
    cat << 'EOF'
Harness IDP Workflow Execution Wrapper

USAGE:
    workflow.sh [-h|--help]
    workflow.sh execute TEMPLATE [--param-name param-value] [OPTIONS]
    workflow.sh monitor-task TASK_ID [OPTIONS]
    workflow.sh get-task-status TASK_ID [OPTIONS]

COMMANDS:
    execute                 Execute a Scaffolder template workflow
    monitor-task            Monitor an existing task until completion
    get-task-status         Get current task status (non-blocking)

OPTIONS:
    --template TEMPLATE     IDP Scaffolder template name (e.g., MyTemplateV3)
    --param-name VALUE      Template parameter (use as many as needed)
    --no-watch              Don't wait for completion (background task)
    --timeout SECONDS       Maximum seconds to wait (default: 3600)
    -v, --verbose           Enable debug output
    -h, --help              Show this help message

ENVIRONMENT VARIABLES (Required):
    HARNESS_ACCOUNT_ID      Harness account ID
    HARNESS_API_KEY         Harness API key (keep this secret!)
    HARNESS_BASE_URL        Optional custom Harness base URL

EXAMPLES:
    # Execute template with parameters
    export HARNESS_ACCOUNT_ID="account-123"
    export HARNESS_API_KEY="xsecretkey"
    ./workflow.sh execute MyTemplate --workspace-name prod --owner admin@example.com

    # Execute in background
    ./workflow.sh execute MyTemplate --workspace-name prod --owner admin@example.com --no-watch

    # Monitor existing task
    ./workflow.sh monitor-task task-uuid-1234567890abcdef

    # Check task status
    ./workflow.sh get-task-status task-uuid-1234567890abcdef
EOF
}

# Validate credentials
validate_credentials() {
    if [[ -z "${HARNESS_ACCOUNT_ID:-}" ]]; then
        log_error "HARNESS_ACCOUNT_ID environment variable not set"
        return 1
    fi

    if [[ -z "${HARNESS_API_KEY:-}" ]]; then
        log_error "HARNESS_API_KEY environment variable not set"
        return 1
    fi

    log_info "Credentials validated"
    return 0
}

# Execute workflow
execute_workflow() {
    local template="$1"
    shift
    local extra_args=("$@")

    python3 "${SCRIPT_DIR}/execute_workflow.py" \
        --template "$template" \
        "${extra_args[@]}"
}

# Monitor task
monitor_task() {
    local task_id="$1"
    shift
    local extra_args=("$@")

    python3 << PYTHON_EOF
import sys
import os
sys.path.insert(0, "${SCRIPT_DIR}")

from harness_idp_client import HarnessScaffolderClient

try:
    client = HarnessScaffolderClient()
    task = client.poll_task("${task_id}", callback=lambda t: print(f"Status: {t.status}"))
    
    if task.is_success():
        print("✅ Task completed successfully")
        sys.exit(0)
    else:
        print(f"❌ Task failed: {task.status}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF
}

# Get task status
get_task_status() {
    local task_id="$1"

    python3 << PYTHON_EOF
import sys
import os
import json
sys.path.insert(0, "${SCRIPT_DIR}")

from harness_idp_client import HarnessScaffolderClient

try:
    client = HarnessScaffolderClient()
    task = client.get_task("${task_id}")
    
    print(f"Task ID:        {task.id}")
    print(f"Status:         {task.status}")
    print(f"Created At:     {task.created_at}")
    print(f"Created By:     {task.created_by}")
    print(f"Last Heartbeat: {task.last_heartbeat_at}")
    print(f"Is Terminal:    {task.is_terminal()}")
    print(f"Is Success:     {task.is_success()}")
    
    if task.spec:
        print(f"Spec Keys:      {', '.join(task.spec.keys())}")
    
    sys.exit(0 if task.is_success() else 1 if task.is_terminal() else 2)
except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF
}

# Main
main() {
    local command="${1:-}"

    case "${command}" in
        -h|--help|help)
            show_help
            exit 0
            ;;
        execute)
            validate_credentials || exit 1
            if [[ $# -lt 2 ]]; then
                log_error "execute requires: TEMPLATE"
                show_help
                exit 1
            fi
            shift
            execute_workflow "$@"
            ;;
        monitor-task)
            validate_credentials || exit 1
            if [[ $# -lt 2 ]]; then
                log_error "monitor-task requires: TASK_ID"
                show_help
                exit 1
            fi
            shift
            monitor_task "$@"
            ;;
        get-task-status)
            validate_credentials || exit 1
            if [[ $# -lt 2 ]]; then
                log_error "get-task-status requires: TASK_ID"
                show_help
                exit 1
            fi
            shift
            get_task_status "$@"
            ;;
        "")
            log_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
