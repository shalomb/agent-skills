#!/usr/bin/env python3
"""
supervisor-watch.py — adaptive polling supervisor for agent-mux.

Watches a set of JSONL output files. Polls frequently when agents are young,
backs off exponentially as they mature, wakes immediately when a file stops
growing (stalled) or a terminal event appears (agent_end / result).

Usage:
    python3 /tmp/supervisor-watch.py

Exit: prints summary when all agents reach terminal state.
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── Agent registry ────────────────────────────────────────────────────────────

@dataclass
class Agent:
    label: str
    jsonl: Path
    role: str          # "ralph" | "bart"
    # adaptive poll state
    last_size: int = 0
    last_change_ts: float = field(default_factory=time.time)
    poll_interval: float = 5.0   # seconds, grows with inactivity
    done: bool = False
    status: str = "starting"     # starting | running | stalled | done | error
    verdict: str = ""            # APPROVED | REJECTED | DONE | ""
    iterations: int = 0          # how many times we've polled

    def check(self) -> bool:
        """Read JSONL, update state. Returns True if newly terminal."""
        p = Path(self.jsonl)
        if not p.exists():
            self.status = "starting"
            return False

        size = p.stat().st_size
        now = time.time()

        # Detect stall: size unchanged for >120s
        if size == self.last_size and size > 0:
            stall_secs = now - self.last_change_ts
            if stall_secs > 120:
                self.status = "stalled"
        else:
            self.last_size = size
            self.last_change_ts = now
            self.status = "running"

        # Adaptive interval: grows from 5s → 60s as agent matures
        age = now - self.last_change_ts
        self.poll_interval = min(60.0, max(5.0, age / 10))

        # Scan for terminal events
        try:
            for line in p.read_text(errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue

                t = d.get("type", "")

                # pi agent terminal
                if t == "agent_end":
                    self.done = True
                    self.status = "done"
                    self._extract_verdict(p)
                    return True

                # gemini terminal
                if t == "result":
                    self.done = True
                    self.status = d.get("status", "done")
                    self._extract_verdict(p)
                    return True

        except Exception:
            pass

        self.iterations += 1
        return False

    def _extract_verdict(self, p: Path):
        """Scan for BART:/RALPH: verdict line in full text."""
        import re
        try:
            text = p.read_text(errors="replace")
            m = re.search(r"(BART|RALPH):\s*(APPROVED|REJECTED|DONE)[^\n]*", text)
            if m:
                self.verdict = m.group(0)[:80]
        except Exception:
            pass

    def status_line(self) -> str:
        size_kb = self.last_size // 1024
        stall = ""
        if self.status == "stalled":
            stall_s = int(time.time() - self.last_change_ts)
            stall = f" ⚠ stalled {stall_s}s"
        verdict = f" → {self.verdict}" if self.verdict else ""
        state = "✅" if self.done else ("⚠" if self.status == "stalled" else "🔄")
        return (
            f"  {state} [{self.role:5}] {self.label:<32} "
            f"{self.status:<10} {size_kb:>5}KB "
            f"poll={self.poll_interval:.0f}s{stall}{verdict}"
        )


# ── Agent list (edit to match current wave) ───────────────────────────────────

AGENTS = [
    Agent("ralph/api-access-pattern v3", "/tmp/pi-api-access-pattern-v3.jsonl", "ralph"),
    Agent("bart/quick-wins v2",          "/tmp/pi-bart-quick-wins-v2.jsonl",    "bart"),
    Agent("bart/raw-flag v2",            "/tmp/pi-bart-raw-flag-v2.jsonl",      "bart"),
    Agent("bart/run-wait v2",            "/tmp/pi-bart-run-wait-v2.jsonl",      "bart"),
    Agent("bart/cli-ux v2",              "/tmp/pi-bart-cli-ux-v2.jsonl",        "bart"),
    Agent("bart/code-quality-1 v2",      "/tmp/pi-bart-code-quality-1-v2.jsonl","bart"),
]


# ── PR summary ────────────────────────────────────────────────────────────────

def pr_summary() -> str:
    try:
        out = subprocess.check_output(
            ["gh", "pr", "list", "--json", "number,headRefName,title"],
            cwd="/home/unop/shalomb/terrapyne",
            text=True, stderr=subprocess.DEVNULL
        )
        prs = json.loads(out)
        lines = [f"  #{p['number']} {p['headRefName']}: {p['title'][:50]}" for p in prs]
        return "\n".join(lines) if lines else "  (none)"
    except Exception:
        return "  (gh unavailable)"


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    print("supervisor-watch starting — adaptive polling, Ctrl+C to exit")
    print()
    newly_done = []

    while True:
        active = [a for a in AGENTS if not a.done]
        if not active:
            break

        # Check each active agent
        for agent in active:
            was_done = agent.done
            terminal = agent.check()
            if terminal and not was_done:
                newly_done.append(agent)

        # Print dashboard
        ts = time.strftime("%H:%M:%S")
        print(f"\r\033[K[{ts}] ── Agent Status ─────────────────────────────────────────")
        for agent in AGENTS:
            print(agent.status_line())

        if newly_done:
            print()
            print("── Newly completed ─────────────────────────────────────")
            for a in newly_done:
                print(f"  🏁 {a.label}: {a.verdict or a.status}")
            newly_done.clear()

        # Show PRs every 5 minutes
        if int(time.time()) % 300 < 10:
            print()
            print("── PRs ─────────────────────────────────────────────────")
            print(pr_summary())

        print()

        # Sleep = minimum poll interval across all active agents
        if active:
            sleep_secs = min(a.poll_interval for a in active)
            sleep_secs = max(5.0, sleep_secs)
            print(f"  next check in {sleep_secs:.0f}s ...", end="", flush=True)
            time.sleep(sleep_secs)
            # Clear the "next check" line
            print(f"\r\033[K", end="", flush=True)

    print()
    print("═" * 60)
    print("ALL AGENTS COMPLETE")
    print("═" * 60)
    for a in AGENTS:
        print(f"  {a.label}: {a.verdict or a.status}")
    print()
    print("── PRs ─────────────────────────────────────────────────")
    print(pr_summary())
    print()
    print("Next: run bash /tmp/accumulate-feedback.sh to triage")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nsupervisor interrupted — agents continue in background")
        sys.exit(0)
