#!/usr/bin/env python3
"""
monitor.py — Live dashboard for copilot/pi agent JSONL output.

Watches a JSONL stream from `copilot --yolo -p @file` and displays a
live dashboard: tool calls, files edited, commits, test results, errors.

Both copilot and pi share the same JSONL schema (agent_end = done).

Usage:
    python3 monitor.py /tmp/copilot-output.jsonl
    python3 monitor.py /tmp/copilot-output.jsonl --interval 5 --no-clear

Refreshes every 2 seconds. Ctrl+C to exit.
Stops automatically on agent_end event.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


def parse_events(path: str) -> dict:
    tools = []
    edits = []
    commits = []
    test_results = []
    errors = []
    last_text = ""
    is_done = False
    total_lines = 0
    session_id = ""
    model = ""

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

            elif t == "message_start":
                msg = d.get("message", {})
                if msg.get("role") == "assistant" and not model:
                    model = msg.get("model", "")

            elif t == "tool_execution_start":
                name = d.get("toolName", "?")
                args = d.get("args", {})
                if name == "bash":
                    cmd = args.get("command", "")[:100]
                    tools.append(("bash", cmd))
                    if any(w in cmd for w in ("pytest", "just test", "npm test", "cargo test")):
                        test_results.append(f"→ {cmd[:70]}")
                    if "git commit" in cmd:
                        commits.append(cmd[:80])
                elif name in ("edit", "write"):
                    p = args.get("path", "?").split("/")[-1]
                    edits.append(p)
                    tools.append((name, p))
                elif name == "read":
                    tools.append(("read", args.get("path", "?").split("/")[-1]))
                else:
                    tools.append((name, str(args)[:60]))

            elif t == "tool_result":
                content = d.get("content", "")
                if isinstance(content, str):
                    for rl in content.split("\n"):
                        if any(w in rl for w in ("passed", "failed", "FAILED", "error", "Error")):
                            if any(w in rl for w in ("passed", "failed")):
                                test_results.append(rl.strip()[:80])
                            if any(w in rl for w in ("FAIL:", "Error:", "Traceback")):
                                errors.append(rl.strip()[:80])

            elif t == "message_end":
                msg = d.get("message", {})
                for block in msg.get("content", []):
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
        "model": model,
    }


def render(data: dict, path: str, label: str = "Copilot", clear: bool = True):
    if clear:
        os.system("clear")

    done_icon = "✅ DONE" if data["is_done"] else "⏳ RUNNING"
    size_kb = data["file_size"] / 1024
    W = 62

    def row(text):
        text = str(text)[:W - 4]
        print(f"║  {text:<{W - 4}} ║")

    def sep():
        print(f"╠{'═' * W}╣")

    print(f"╔{'═' * W}╗")
    row(f"{label} Sub-Agent Monitor               {done_icon}")
    sep()
    row(f"File: {Path(path).name:<34} {size_kb:>7.0f} KB")
    row(f"Events: {data['total_lines']:<10}  Tool calls: {data['tool_count']}")
    if data["session_id"] or data["model"]:
        row(f"Session: {data['session_id']}  Model: {data['model'][:30]}")
    sep()

    tool_types = {}
    for name, _ in data["tools"]:
        tool_types[name] = tool_types.get(name, 0) + 1
    parts = [f"{k}={v}" for k, v in sorted(tool_types.items())]
    row(f"Tools: {', '.join(parts) or 'none yet'}")
    sep()

    files = ", ".join(data["edits"][:6]) or "none yet"
    row(f"Files edited: {files}")
    sep()

    if data["commits"]:
        for c in data["commits"][-3:]:
            row(f"📦 {c[:W - 7]}")
    else:
        row("📦 No commits yet")
    sep()

    if data["test_results"]:
        for t in data["test_results"][-3:]:
            row(f"🧪 {t[:W - 7]}")
    else:
        row("🧪 No test runs yet")

    if data["errors"]:
        sep()
        for e in data["errors"][-3:]:
            row(f"❌ {e[:W - 7]}")

    sep()
    row("Recent activity:")
    for name, detail in data["tools"][-5:]:
        icon = {"bash": "⚡", "read": "📖", "edit": "✏️ ", "write": "📝"}.get(name, "🔧")
        row(f"  {icon}{name}: {detail[:W - 12]}")
    sep()

    text = data["last_text"].replace("\n", " ")[:W * 2]
    row(f"💬 {text[:W - 7]}")
    if len(text) > W - 7:
        row(f"   {text[W - 7:(W - 7) * 2]}")

    print(f"╚{'═' * W}╝")
    print(f"  Refreshing — Ctrl+C to exit")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl_file")
    parser.add_argument("--interval", type=int, default=2)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--label", default="Copilot")
    args = parser.parse_args()

    path = args.jsonl_file
    if not os.path.exists(path):
        print(f"Waiting for {path}...")
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
            render(data, path, label=args.label, clear=not args.no_clear)
            if data["is_done"]:
                print("\n  Agent finished.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  Monitor stopped.")


if __name__ == "__main__":
    main()
