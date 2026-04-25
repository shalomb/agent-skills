#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""
monitor.py — Live dashboard for Claude CLI stream-json JSONL output.

Watches a JSONL stream from `claude --print --output-format stream-json`
and displays a live dashboard: tool calls, files edited, commits, test
results, errors, cost.

Claude CLI stream-json schema:
  {"type":"system","subtype":"init","session_id":"...","model":"...",...}
  {"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{...}},...],...}}
  {"type":"user","tool_use_result":{"content":[{"type":"text","text":"..."}],...}}
  {"type":"result","subtype":"success","is_error":false,"duration_ms":...,"total_cost_usd":...,"result":"..."}

Completion signal: {"type":"result"} line.

Usage:
    python3 monitor.py /tmp/claude-output.jsonl
    python3 monitor.py /tmp/claude-output.jsonl --interval 5
    python3 monitor.py /tmp/claude-output.jsonl --no-clear
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def parse_events(path: str) -> dict:
    """Parse Claude CLI JSONL and extract summary."""
    tools = []
    edits = []
    commits = []
    test_results = []
    errors = []
    last_text = ""
    thinking_history: list[str] = []  # rolling last N agent thought snippets
    is_done = False
    is_error = False
    total_lines = 0
    session_id = ""
    model = ""
    cost_usd = None
    duration_ms = None
    num_turns = 0
    agent_cwd = ""  # CWD of the agent process, from init event

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
                model = d.get("model", "")
                agent_cwd = d.get("cwd", "").rstrip("/") + "/"

            elif t == "assistant":
                msg = d.get("message", {})
                for block in msg.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")

                    if btype == "tool_use":
                        name = block.get("name", "?")
                        inp = block.get("input", {})

                        # Claude Code uses file_path; older schema used path
                        fpath = inp.get("file_path") or inp.get("path") or ""
                        # Strip agent CWD prefix for display
                        if agent_cwd and fpath.startswith(agent_cwd):
                            rel = fpath[len(agent_cwd):]
                        else:
                            rel = fpath or "?"

                        if name == "Bash":
                            cmd = inp.get("command", "")[:200]
                            tools.append(("bash", cmd))
                            if any(w in cmd for w in ("pytest", "just test", "uv run pytest")):
                                test_results.append(f"→ {cmd[:120]}")
                            if "git commit" in cmd:
                                commits.append(cmd[:120])

                        elif name in ("Edit", "MultiEdit"):
                            edits.append(rel)
                            tools.append(("edit", rel))

                        elif name == "Write":
                            edits.append(rel)
                            tools.append(("write", rel))

                        elif name == "Read":
                            tools.append(("read", rel))

                        elif name == "Grep":
                            pat = inp.get("pattern", "?")[:60]
                            gpath = inp.get("path", "").replace("/home/unop/shalomb/terrapyne/", "")
                            tools.append(("grep", f"{pat}  @ {gpath}" if gpath else pat))

                        else:
                            tools.append((name.lower(), str(inp)[:80]))

                    elif btype == "text":
                        snippet = block.get("text", "").strip()
                        if snippet:
                            # Keep last sentence / meaningful chunk (up to 200 chars)
                            snippet = snippet.replace("\n", " ")[-200:].strip()
                            last_text = snippet
                            thinking_history.append(snippet)
                            if len(thinking_history) > 6:
                                thinking_history.pop(0)

            elif t == "user":
                # tool results live in message.content[].type == "tool_result"
                msg = d.get("message", {})
                raw_content = msg.get("content", [])
                if isinstance(raw_content, str):
                    raw_content = [{"type": "tool_result", "content": raw_content}]
                for block in raw_content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_result":
                        continue
                    inner = block.get("content", "")
                    if isinstance(inner, list):
                        text = " ".join(c.get("text", "") for c in inner if isinstance(c, dict))
                    else:
                        text = str(inner)
                    for result_line in text.split("\n"):
                        stripped = result_line.strip()
                        if any(w in stripped for w in ("passed", "failed", "error")) and (
                            "passed" in stripped or "failed" in stripped
                        ):
                            test_results.append(stripped[:80])
                        if any(w in stripped for w in
                               ("FAILED", "ERROR", "Traceback", "AssertionError")):
                            errors.append(stripped[:80])

            elif t == "result":
                is_done = True
                is_error = d.get("is_error", False)
                cost_usd = d.get("total_cost_usd")
                duration_ms = d.get("duration_ms")
                num_turns = d.get("num_turns", 0)
                # Final text result
                result_text = d.get("result", "")
                if result_text:
                    snippet = result_text.replace("\n", " ").strip()[-200:]
                    last_text = snippet
                    thinking_history.append(snippet)
                    if len(thinking_history) > 6:
                        thinking_history.pop(0)

    return {
        "total_lines": total_lines,
        "tool_count": len(tools),
        "tools": tools,
        "edits": sorted(set(edits)),
        "commits": commits,
        "test_results": test_results[-5:],
        "errors": errors[-5:],
        "last_text": last_text,
        "thinking_history": thinking_history,
        "is_done": is_done,
        "is_error": is_error,
        "file_size": os.path.getsize(path),
        "session_id": session_id,
        "model": model,
        "cost_usd": cost_usd,
        "duration_ms": duration_ms,
        "num_turns": num_turns,
        "agent_cwd": agent_cwd,
    }


def terminal_width() -> int:
    """Get usable terminal width, clamped to a sensible range."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    # Leave 2 chars for the border characters (║ + ║)
    return max(60, min(cols - 2, 220))


def wrap_text(text: str, width: int, indent: str = "   ") -> list[str]:
    """Wrap text to fit within width, returning list of lines."""
    text = text.replace("\n", " ").strip()
    if not text:
        return [""]
    lines = []
    while text:
        if len(text) <= width:
            lines.append(text)
            break
        # Break at last space within width
        cut = text[:width].rfind(" ")
        if cut <= 0:
            cut = width
        lines.append(text[:cut])
        text = indent + text[cut:].lstrip()
    return lines


def render(data: dict, path: str, clear: bool = True):
    """Render the dashboard."""
    if clear:
        os.system("clear")

    W = terminal_width()  # inner content width (between ║  and  ║)
    PAD = 2               # spaces inside each border
    INNER = W - PAD * 2   # usable text width

    if data["is_done"]:
        done_icon = "❌ ERROR" if data["is_error"] else "✅ DONE"
    else:
        done_icon = "⏳ RUNNING"

    size_kb = data["file_size"] / 1024

    def row(text: str, icon: str = ""):
        """Print one row, wrapping if needed."""
        prefix = f"{icon} " if icon else ""
        lines = wrap_text(prefix + str(text), INNER)
        for line in lines:
            print(f"║  {line:<{INNER}} ║")

    def sep():
        print(f"╠{'═' * W}╣")

    def header(text: str):
        """Centred header text."""
        print(f"║  {text:<{INNER}} ║")

    # ── Top border ──────────────────────────────────────────────
    print(f"╔{'═' * W}╗")

    # Title + status (right-aligned)
    title = "Claude Sub-Agent Monitor"
    status_pad = INNER - len(title)
    row(f"{title}{done_icon:>{status_pad}}")
    sep()

    # Meta
    row(f"File: {Path(path).name}   {size_kb:.0f} KB   "
        f"Events: {data['total_lines']}   Tool calls: {data['tool_count']}")
    if data["session_id"]:
        model_short = data["model"].replace("claude-", "").replace("-latest", "")
        row(f"Session: {data['session_id']}   Model: {model_short}")
    sep()

    # Tool summary
    tool_types: dict[str, int] = {}
    for name, _ in data["tools"]:
        tool_types[name] = tool_types.get(name, 0) + 1
    parts = [f"{k}={v}" for k, v in sorted(tool_types.items())]
    row(f"Tools: {', '.join(parts) or 'none yet'}")
    sep()

    # Files edited — show all, wrapped
    files = ", ".join(data["edits"]) or "none yet"
    for line in wrap_text(f"Files edited: {files}", INNER):
        print(f"║  {line:<{INNER}} ║")
    sep()

    # Commits
    if data["commits"]:
        for c in data["commits"][-5:]:
            for line in wrap_text(f"📦 {c}", INNER):
                print(f"║  {line:<{INNER}} ║")
    else:
        row("📦 No commits yet")
    sep()

    # Test results — show last 5, full width
    if data["test_results"]:
        for t in data["test_results"][-5:]:
            for line in wrap_text(f"🧪 {t}", INNER):
                print(f"║  {line:<{INNER}} ║")
    else:
        row("🧪 No test runs yet")

    # Errors
    if data["errors"]:
        sep()
        for e in data["errors"][-5:]:
            for line in wrap_text(f"❌ {e}", INNER):
                print(f"║  {line:<{INNER}} ║")

    sep()

    # Recent activity — last 8 tool calls, full command shown
    row("Recent activity:")
    icons = {"bash": "⚡", "read": "📖", "edit": "✏️ ", "write": "📝"}
    for name, detail in data["tools"][-8:]:
        ic = icons.get(name, "🔧")
        for line in wrap_text(f"  {ic} {name}: {detail}", INNER, indent="       "):
            print(f"║  {line:<{INNER}} ║")

    sep()

    # Cost / duration
    if data["is_done"] and data["cost_usd"] is not None:
        dur_s = (data["duration_ms"] or 0) / 1000
        row(f"💰 Cost: ${data['cost_usd']:.4f}   "
            f"Duration: {dur_s:.1f}s   Turns: {data['num_turns']}")
        sep()

    # Thinking / agent narration — last 3 snippets, each wrapped
    thinking = data["thinking_history"][-3:]
    if thinking:
        sep()
        for i, thought in enumerate(thinking):
            prefix = "💬 " if i == len(thinking) - 1 else "   "
            for line in wrap_text(prefix + thought, INNER, indent="     "):
                print(f"║  {line:<{INNER}} ║")

    print(f"╚{'═' * W}╝")
    if not data["is_done"]:
        print("  Refreshing — Ctrl+C to exit")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Claude CLI stream-json JSONL output."
    )
    parser.add_argument("jsonl_file", help="Path to the JSONL output file")
    parser.add_argument(
        "--interval", type=int, default=2,
        help="Refresh interval in seconds (default: 2)",
    )
    parser.add_argument(
        "--no-clear", action="store_true",
        help="Don't clear screen between refreshes",
    )
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
                print("\n  Agent finished. Final state above.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  Monitor stopped.")


if __name__ == "__main__":
    main()
