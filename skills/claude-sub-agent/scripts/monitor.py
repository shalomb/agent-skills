#!/usr/bin/env python3
"""
monitor.py — Live dashboard for claude stream-json JSONL output.

Watches a JSONL stream from `claude -p --output-format stream-json`
and displays a live dashboard.

Claude stream-json schema (subset):
  {"type":"system","subtype":"init","session_id":"..."}
  {"type":"assistant","message":{"content":[...]}}       ← text/tool_use blocks
  {"type":"tool_result","tool_use_id":"...","content":"..."} 
  {"type":"result","subtype":"success","result":"...","total_cost_usd":N,"usage":{...}}  ← done

Completion signal: {"type":"result"} line.

Usage:
    python3 monitor.py /tmp/claude-output.jsonl
    python3 monitor.py /tmp/claude-output.jsonl --interval 5 --no-clear
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
    cost_usd = None
    usage = {}
    num_turns = None

    # Track pending tool_use blocks by id to correlate with tool_result
    pending_tools: dict = {}

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

            if t == "system" and d.get("subtype") == "init":
                session_id = d.get("session_id", "")[:8]

            elif t == "assistant":
                msg = d.get("message", {})
                # model appears in assistant messages
                if not model:
                    model = msg.get("model", "")
                for block in msg.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        last_text = block.get("text", "")[-200:]
                    elif btype == "tool_use":
                        tid = block.get("id", "")
                        name = block.get("name", "?")
                        inp = block.get("input", {})
                        pending_tools[tid] = (name, inp)

                        if name == "Bash":
                            cmd = inp.get("command", "")[:100]
                            tools.append(("bash", cmd))
                            if any(w in cmd for w in ("pytest", "just test", "npm test", "cargo test")):
                                test_results.append(f"→ {cmd[:70]}")
                            if "git commit" in cmd:
                                commits.append(cmd[:80])
                        elif name in ("Edit", "Write", "MultiEdit"):
                            p = inp.get("file_path") or inp.get("path") or "?"
                            short = p.split("/")[-1]
                            edits.append(short)
                            tools.append((name, short))
                        elif name == "Read":
                            p = inp.get("file_path") or inp.get("path") or "?"
                            tools.append(("Read", p.split("/")[-1]))
                        else:
                            tools.append((name, str(inp)[:60]))

            elif t == "tool_result":
                content = d.get("content", "")
                if isinstance(content, str):
                    for rl in content.split("\n"):
                        if any(w in rl for w in ("passed", "failed", "FAILED")):
                            test_results.append(rl.strip()[:80])
                        if any(w in rl for w in ("Error:", "Traceback", "FAIL:")):
                            errors.append(rl.strip()[:80])
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            txt = block.get("text", "")
                            for rl in txt.split("\n"):
                                if any(w in rl for w in ("passed", "failed", "FAILED")):
                                    test_results.append(rl.strip()[:80])
                                if any(w in rl for w in ("Error:", "Traceback", "FAIL:")):
                                    errors.append(rl.strip()[:80])

            elif t == "result":
                is_done = True
                cost_usd = d.get("total_cost_usd")
                usage = d.get("usage", {})
                num_turns = d.get("num_turns")
                # Also capture final text if present
                if d.get("result"):
                    last_text = d["result"][-200:]

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
        "cost_usd": cost_usd,
        "usage": usage,
        "num_turns": num_turns,
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
    row(f"Claude Sub-Agent Monitor                  {done_icon}")
    sep()
    row(f"File: {Path(path).name:<34} {size_kb:>7.0f} KB")
    row(f"Events: {data['total_lines']:<10}  Tool calls: {data['tool_count']}")
    if data["session_id"] or data["model"]:
        row(f"Session: {data['session_id']}  Model: {data['model'][:30]}")

    if data["cost_usd"] is not None:
        u = data["usage"]
        tok_in = u.get("input_tokens", "?")
        tok_out = u.get("output_tokens", "?")
        turns = data["num_turns"] or "?"
        row(f"Cost: ${data['cost_usd']:.4f}  Tokens: {tok_in}in/{tok_out}out  Turns: {turns}")

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
        icon = {"bash": "⚡", "Bash": "⚡", "Read": "📖",
                "Edit": "✏️ ", "Write": "📝", "MultiEdit": "✏️ "}.get(name, "🔧")
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
