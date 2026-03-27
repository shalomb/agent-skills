#!/usr/bin/env python3
"""
pi-poll.py — Poll a pi agent's JSONL output for completion.

Reads the tmux pane where pi-monitor.py is running, extracts key metrics,
and reports progress. Exits 0 when the agent finishes, 1 on timeout.

Usage:
    python3 pi-poll.py <tmux-target> [--interval 30] [--timeout 600]

Example:
    python3 pi-poll.py "myproject:0.0" --interval 30

Output: one status line per interval, final summary on completion.
"""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime


def read_pane(target: str) -> str:
    """Read the tmux pane content via tmux-read.sh."""
    # Try the skill's tmux-read.sh first, fall back to direct tmux capture
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

    # Direct tmux fallback
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", target, "-p", "-S", "-50"],
        capture_output=True, text=True, timeout=5,
    )
    return result.stdout


def parse_status(pane_text: str) -> dict:
    """Extract metrics from the pi-monitor.py dashboard output."""
    data = {
        "done": "✅ DONE" in pane_text,
        "tools": None,
        "files": "",
        "last_text": "",
    }

    # Tool count
    m = re.search(r"Tool calls:\s*(\d+)", pane_text)
    if m:
        data["tools"] = int(m.group(1))

    # Files edited
    m = re.search(r"Files edited:\s*(.*?)(?:\s*║|$)", pane_text, re.MULTILINE)
    if m:
        data["files"] = m.group(1).strip()[:60]

    # Last agent text (💬 line)
    for line in pane_text.split("\n"):
        if "💬" in line:
            data["last_text"] = line.split("💬")[-1].strip().rstrip("║").strip()[:80]
            break

    return data


def main():
    parser = argparse.ArgumentParser(description="Poll a pi agent for completion.")
    parser.add_argument("target", help="Tmux pane target (e.g. session:window.pane)")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds (default: 30)")
    parser.add_argument("--timeout", type=int, default=1200, help="Max wait time in seconds (default: 1200)")
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
            # Print the full final monitor output
            print("\n--- Final monitor state ---")
            for line in pane_text.split("\n"):
                if any(c in line for c in ("╔", "╠", "╚", "║")):
                    print(line)
            return 0

        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
