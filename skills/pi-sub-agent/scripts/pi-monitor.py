#!/usr/bin/env python3
"""
pi-monitor.py — Live dashboard for pi agent JSONL output.

Watches a JSONL output file from `pi --mode json` and displays a live
dashboard: tool calls, files edited, commits, test results, errors.

Usage:
    python3 pi-monitor.py /tmp/task-output.jsonl
    python3 pi-monitor.py /tmp/task-output.jsonl --interval 5
    python3 pi-monitor.py /tmp/task-output.jsonl --no-clear

Refreshes every 2 seconds (configurable). Ctrl+C to exit.
Stops automatically when the agent finishes (agent_end event).
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


def parse_events(path: str) -> dict:
    """Parse JSONL and extract summary."""
    tools = []
    edits = []
    commits = []
    test_results = []
    errors = []
    last_text = ""
    is_done = False
    total_lines = 0
    session_id = ""
    start_time = ""

    with open(path) as f:
        for line in f:
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = d.get("type", "")

            if t == "session":
                session_id = d.get("id", "")[:8]
                start_time = d.get("timestamp", "")[:19]

            elif t == "tool_execution_start":
                name = d.get("toolName", "?")
                args = d.get("args", {})
                if name == "bash":
                    cmd = args.get("command", "")[:100]
                    tools.append(("bash", cmd))
                    if "pytest" in cmd or "just test" in cmd:
                        test_results.append(f"→ {cmd[:70]}")
                    if "git commit" in cmd:
                        commits.append(cmd[:80])
                elif name == "edit":
                    p = args.get("path", "?")
                    short = p.split("/")[-1]
                    edits.append(short)
                    tools.append(("edit", short))
                elif name == "write":
                    p = args.get("path", "?")
                    short = p.split("/")[-1]
                    edits.append(short)
                    tools.append(("write", short))
                elif name == "read":
                    p = args.get("path", "?")
                    tools.append(("read", p.split("/")[-1]))
                else:
                    tools.append((name, str(args)[:60]))

            elif t == "tool_result":
                content = d.get("content", "")
                if isinstance(content, str):
                    for result_line in content.split("\n"):
                        if "passed" in result_line and ("failed" in result_line or "passed" in result_line):
                            if any(w in result_line for w in ("passed", "failed", "error")):
                                test_results.append(result_line.strip()[:80])
                        if any(w in result_line for w in ("FAIL:", "Error:", "Traceback")):
                            errors.append(result_line.strip()[:80])

            elif t == "message_end":
                msg = d.get("message", {})
                content = msg.get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        last_text = block.get("text", "")[-200:]

            elif t in ("agent_end", "session_end"):
                is_done = True

    return {
        "total_lines": total_lines,
        "tool_count": len(tools),
        "tools": tools,
        "edits": sorted(set(edits)),
        "commits": commits,
        "test_results": test_results[-5:],
        "errors": errors[-5:],
        "last_text": last_text,
        "is_done": is_done,
        "file_size": os.path.getsize(path),
        "session_id": session_id,
        "start_time": start_time,
    }


def render(data: dict, path: str, clear: bool = True):
    """Render the dashboard."""
    if clear:
        os.system("clear")

    done_icon = "✅ DONE" if data["is_done"] else "⏳ RUNNING"
    size_kb = data["file_size"] / 1024
    W = 62  # box width

    def row(text):
        text = str(text)[:W - 4]
        print(f"║  {text:<{W - 4}} ║")

    def sep():
        print(f"╠{'═' * W}╣")

    print(f"╔{'═' * W}╗")
    row(f"Pi Sub-Agent Monitor                      {done_icon}")
    sep()
    row(f"File: {Path(path).name:<36} {size_kb:>7.0f} KB")
    row(f"Events: {data['total_lines']:<10}  Tool calls: {data['tool_count']}")
    if data["session_id"]:
        row(f"Session: {data['session_id']}  Started: {data['start_time']}")
    sep()

    # Tool summary
    tool_types = {}
    for name, _ in data["tools"]:
        tool_types[name] = tool_types.get(name, 0) + 1
    parts = [f"{k}={v}" for k, v in sorted(tool_types.items())]
    row(f"Tools: {', '.join(parts)}")
    sep()

    # Files edited
    files = ", ".join(data["edits"][:6]) or "none yet"
    row(f"Files edited: {files}")
    sep()

    # Commits
    if data["commits"]:
        for c in data["commits"][-3:]:
            row(f"📦 {c[:W - 7]}")
    else:
        row("📦 No commits yet")
    sep()

    # Test results
    if data["test_results"]:
        for t in data["test_results"][-3:]:
            row(f"🧪 {t[:W - 7]}")
    else:
        row("🧪 No test runs yet")

    # Errors
    if data["errors"]:
        sep()
        for e in data["errors"][-3:]:
            row(f"❌ {e[:W - 7]}")

    sep()

    # Recent activity
    row("Recent activity:")
    for name, detail in data["tools"][-5:]:
        icon = {"bash": "⚡", "read": "📖", "edit": "✏️ ", "write": "📝"}.get(name, "🔧")
        row(f"  {icon}{name}: {detail[:W - 12]}")
    sep()

    # Last agent text
    text = data["last_text"].replace("\n", " ")[:W * 2]
    row(f"💬 {text[:W - 7]}")
    if len(text) > W - 7:
        row(f"   {text[W - 7:(W - 7) * 2]}")

    print(f"╚{'═' * W}╝")
    print(f"  Refreshing — Ctrl+C to exit")


def main():
    parser = argparse.ArgumentParser(description="Monitor pi agent JSONL output.")
    parser.add_argument("jsonl_file", help="Path to the JSONL output file")
    parser.add_argument("--interval", type=int, default=2, help="Refresh interval in seconds (default: 2)")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear screen between refreshes")
    args = parser.parse_args()

    path = args.jsonl_file
    if not os.path.exists(path):
        print(f"Waiting for {path} to appear...")
        for _ in range(60):
            if os.path.exists(path):
                break
            time.sleep(1)
        else:
            print(f"Timed out waiting for {path}")
            sys.exit(1)

    try:
        while True:
            data = parse_events(path)
            render(data, path, clear=not args.no_clear)
            if data["is_done"]:
                print(f"\n  Agent finished. Final state above.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\n  Monitor stopped.")


if __name__ == "__main__":
    main()
