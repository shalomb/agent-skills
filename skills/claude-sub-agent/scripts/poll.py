#!/usr/bin/env python3
"""
poll.py — Poll a claude agent's tmux pane for completion.

Reads the pane where monitor.py is running, extracts progress metrics,
and reports status. Exits 0 when done, 1 on timeout.

Usage:
    python3 poll.py <tmux-target> [--interval 30] [--timeout 1200]

Example:
    python3 poll.py "myproject:0.0" --interval 30
"""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime


def read_pane(target: str) -> str:
    for script in [
        f"{__import__('pathlib').Path.home()}/.pi/agent/skills/tmux/scripts/tmux-read.sh",
    ]:
        try:
            result = subprocess.run(
                ["bash", script, target],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    result = subprocess.run(
        ["tmux", "capture-pane", "-t", target, "-p", "-S", "-50"],
        capture_output=True, text=True, timeout=5,
    )
    return result.stdout


def parse_status(pane_text: str) -> dict:
    data = {
        "done": "✅ DONE" in pane_text,
        "tools": None,
        "files": "",
        "last_text": "",
    }

    m = re.search(r"Tool calls:\s*(\d+)", pane_text)
    if m:
        data["tools"] = int(m.group(1))

    m = re.search(r"Files edited:\s*(.*?)(?:\s*║|$)", pane_text, re.MULTILINE)
    if m:
        data["files"] = m.group(1).strip()[:60]

    for line in pane_text.split("\n"):
        if "💬" in line:
            data["last_text"] = line.split("💬")[-1].strip().rstrip("║").strip()[:80]
            break

    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Tmux pane target (e.g. session:window.pane)")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()

    start = time.time()
    iteration = 0

    while True:
        elapsed = time.time() - start
        if elapsed > args.timeout:
            print(f"\n⏱️  Timeout after {args.timeout}s — agent may still be running")
            sys.exit(1)

        pane_text = read_pane(args.target)
        status = parse_status(pane_text)
        iteration += 1

        ts = datetime.now().strftime("%H:%M:%S")
        tools = status["tools"] or "?"
        files = status["files"] or "..."
        print(f"[{ts}] tools={tools}  files={files}")
        if status["last_text"]:
            print(f"         {status['last_text'][:70]}")

        if status["done"]:
            print(f"\n✅ Agent finished after {int(elapsed)}s ({iteration} polls)")
            return 0

        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
