#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Todo Navigator - Command-line entrypoint.

Executable runner that invokes todo_navigator package.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path for direct script execution
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Re-export key modules and functions for backward compatibility with existing tests
from todo_navigator.cli import (  # noqa: E402
    build_parser,
    cmd_add,
    cmd_dep,
    cmd_edit,
    cmd_graph,
    cmd_list,
    cmd_next,
    cmd_prev,
    cmd_replan,
    cmd_status,
    cmd_view,
    main,
)
from todo_navigator.dag import (  # noqa: E402
    add_dependency,
    compute_waves,
    detect_cycle,
    find_matching_targets,
    get_all_task_ids,
    remove_dependency,
    sort_tasks_wsjf,
)
from todo_navigator.editor import (  # noqa: E402
    handle_express_edit,
    launch_editor,
    stage_card_as_artifact,
)
from todo_navigator.models import Task  # noqa: E402
from todo_navigator.parser import (  # noqa: E402
    add_task_to_todo,
    generate_task_id,
    get_active_todo_path,
    get_repo_root,
    get_repo_slug,
    get_shadow_dir,
    parse_todo_file,
    parse_todo_line,
    scaffold_task_card,
)

__all__ = [
    "Task",
    "add_dependency",
    "add_task_to_todo",
    "build_parser",
    "cmd_add",
    "cmd_dep",
    "cmd_edit",
    "cmd_graph",
    "cmd_list",
    "cmd_next",
    "cmd_prev",
    "cmd_replan",
    "cmd_status",
    "cmd_view",
    "compute_waves",
    "detect_cycle",
    "find_matching_targets",
    "generate_task_id",
    "get_active_todo_path",
    "get_all_task_ids",
    "get_repo_root",
    "get_repo_slug",
    "get_shadow_dir",
    "handle_express_edit",
    "launch_editor",
    "main",
    "parse_todo_file",
    "parse_todo_line",
    "remove_dependency",
    "scaffold_task_card",
    "sort_tasks_wsjf",
    "stage_card_as_artifact",
]

if __name__ == "__main__":
    sys.exit(main())
