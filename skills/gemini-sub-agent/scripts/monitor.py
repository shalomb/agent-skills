#!/usr/bin/env python3
"""
monitor.py — Live dashboard for gemini stream-json JSONL output.

Watches a JSONL stream from `gemini --output-format stream-json --yolo`
and displays a live dashboard.

Gemini JSONL schema:
  {"type":"init","session_id":"...","model":"..."}
  {"type":"message","role":"user","content":"..."}
  {"type":"message","role":"assistant","content":"...","delta":true}   ← streaming chunks
  {"type":"tool_call","name":"...","input":{...}}
  {"type":"tool_result","name":"...","output":"..."}
  {"type":"result","status":"success","stats":{...}}   ← completion signal

Usage:
    python3 monitor.py /tmp/gemini-output.jsonl
    python3 monitor.py /tmp/gemini-output.jsonl --interval 5 --no-clear
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
    assistant_text = ""
    is_done = False
    total_lines = 0
    session_id = ""
    model = ""
    stats = {}

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

            if t == "init":
                session_id = d.get("session_id", "")[:8]
                model = d.get("model", "")

            elif t == "message":
                role = d.get("role", "")
                content = d.get("content", "")
                if role == "assistant":
                    # Accumulate streaming delta chunks
                    if d.get("delta"):
                        assistant_text += content
                    else:
                        assistant_text = content

            elif t == "tool_call":
                name = d.get("name", "?")
                inp = d.get("input", {})
                if name in ("run_shell_command", "execute_bash", "bash", "shell"):
                    cmd = (inp.get("command") or inp.get("cmd") or str(inp))[:100]
                    tools.append(("shell", cmd))
                    if any(w in cmd for w in ("pytest", "just test", "npm test", "cargo test")):
                        test_results.append(f"→ {cmd[:70]}")
                    if "git commit" in cmd:
                        commits.append(cmd[:80])
                elif name in ("write_file", "edit_file", "create_file", "replace_in_file"):
                    p = (inp.get("path") or inp.get("file_path") or "?")
                    short = p.split("/")[-1]
                    edits.append(short)
                    tools.append((name, short))
                elif name in ("read_file", "view_file"):
                    p = (inp.get("path") or inp.get("file_path") or "?")
                    tools.append(("read", p.split("/")[-1]))
                else:
                    tools.append((name, str(inp)[:60]))

            elif t == "tool_result":
                output = d.get("output", "")
                if isinstance(output, str):
                    for rl in output.split("\n"):
                        if any(w in rl for w in ("passed", "failed", "FAILED")):
                            test_results.append(rl.strip()[:80])
                        if any(w in rl for w in ("Error:", "Traceback", "FAIL:")):
                            errors.append(rl.strip()[:80])

            elif t == "result":
                is_done = True
                stats = d.get("stats", {})

    return {
        "total_lines": total_lines,
        "tool_count": len(tools),
        "tools": tools,
        "edits": sorted(set(edits)),
        "commits": commits,
        "test_results": test_results[-5:],
        "errors": errors[-5:],
        "last_text": assistant_text[-200:],
        "is_done": is_done,
        "file_size": os.path.getsize(path),
        "session_id": session_id,
        "model": model,
        "stats": stats,
    }


def render(data: dict, path: str, clear: bool = True):
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
    row(f"Gemini Sub-Agent Monitor                  {done_icon}")
    sep()
    row(f"File: {Path(path).name:<34} {size_kb:>7.0f} KB")
    row(f"Events: {data['total_lines']:<10}  Tool calls: {data['tool_count']}")
    if data["session_id"] or data["model"]:
        row(f"Session: {data['session_id']}  Model: {data['model'][:30]}")

    if data["stats"]:
        s = data["stats"]
        tok_in = s.get("input_tokens", s.get("total_tokens", "?"))
        tok_out = s.get("output_tokens", "?")
        dur = s.get("duration_ms", "?")
        row(f"Tokens in/out: {tok_in}/{tok_out}  Duration: {dur}ms")

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
        icon = {"shell": "⚡", "read": "📖", "edit_file": "✏️ ",
                "write_file": "📝", "create_file": "📝"}.get(name, "🔧")
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
            render(data, path, clear=not args.no_clear)
            if data["is_done"]:
                print("\n  Agent finished.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  Monitor stopped.")


if __name__ == "__main__":
    main()
