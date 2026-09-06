#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Lazygit Tmux Popup Launcher for agent code review and git management."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple


def get_git_context(cwd: Optional[Path] = None) -> Optional[Tuple[Path, str, str]]:
    """Inspects the current working directory or given path for git repository context.

    Returns:
        (repo_root, repo_name, current_branch) if inside a git repository, else None.
    """
    target_dir = cwd or Path.cwd()

    try:
        res_root = subprocess.run(
            ["git", "-C", str(target_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res_root.returncode != 0:
            return None

        repo_root = Path(res_root.stdout.strip())
        repo_name = repo_root.name

        res_branch = subprocess.run(
            ["git", "-C", str(target_dir), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        branch = res_branch.stdout.strip() if res_branch.returncode == 0 else "HEAD"
        if branch == "HEAD":
            # Check if detached HEAD, extract short SHA
            res_sha = subprocess.run(
                ["git", "-C", str(target_dir), "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res_sha.returncode == 0:
                branch = f"detached:{res_sha.stdout.strip()}"

        return repo_root, repo_name, branch
    except Exception:
        return None


def find_lazygit_binary() -> Optional[str]:
    """Locates the lazygit binary in system PATH or standard install directories."""
    found = shutil.which("lazygit")
    if found:
        return found

    # Fallback locations (e.g. Go installs, user local bins)
    fallbacks = [
        Path.home() / ".local/share/go/bin/lazygit",
        Path.home() / ".local/bin/lazygit",
        Path.home() / "go/bin/lazygit",
        Path("/usr/local/bin/lazygit"),
        Path("/usr/bin/lazygit"),
    ]

    for p in fallbacks:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    return None


def build_tmux_command(
    repo_root: Path,
    repo_name: str,
    branch: str,
    lazygit_bin: str,
    extra_args: Optional[List[str]] = None,
) -> List[str]:
    """Constructs the tmux display-popup command."""
    title = f" Lazygit: {repo_name} ({branch}) "
    args = extra_args or []
    return [
        "tmux",
        "display-popup",
        "-E",
        "-d",
        str(repo_root),
        "-w",
        "90%",
        "-h",
        "90%",
        "-T",
        title,
        lazygit_bin,
    ] + args


def launch_lazygit(
    cwd: Optional[Path] = None,
    extra_args: Optional[List[str]] = None,
    no_popup: bool = False,
) -> int:
    """Launches lazygit in a tmux popup window, interactive terminal, or reports status."""
    target_dir = cwd or Path.cwd()
    ctx = get_git_context(target_dir)

    if not ctx:
        print(f"❌ Not a git repository: {target_dir}")
        print("   The /lazygit command must be executed inside a git repository.")
        return 1

    repo_root, repo_name, branch = ctx

    lazygit_bin = find_lazygit_binary()
    if not lazygit_bin:
        print("❌ 'lazygit' binary not found on this system.")
        print("   Please install lazygit via one of the following methods:")
        print("   • Linux / macOS: brew install lazygit")
        print("   • Go:            go install github.com/jesseduffield/lazygit@latest")
        print("   • Ubuntu / Debian: sudo apt install lazygit (or via GitHub releases)")
        return 1

    tmux_socket = os.environ.get("TMUX")

    # 1. Tmux Popup Window (Preferred agent UX)
    if tmux_socket and not no_popup:
        cmd = build_tmux_command(repo_root, repo_name, branch, lazygit_bin, extra_args)
        try:
            res = subprocess.run(cmd, check=False)
            if res.returncode == 0:
                print(
                    f"✅ Closed lazygit for [{repo_name}](file://{repo_root}) on branch `{branch}`."
                )

                # Show status summary if working tree has changes
                try:
                    stat = subprocess.run(
                        ["git", "-C", str(repo_root), "status", "--short"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    lines = stat.stdout.strip().splitlines() if stat.stdout else []
                    if lines:
                        print(
                            f"📊 Working tree status ({len(lines)} item{'s' if len(lines) > 1 else ''}):"
                        )
                        for line in lines[:8]:
                            print(f"   {line}")
                        if len(lines) > 8:
                            print(f"   ... and {len(lines) - 8} more changes.")
                    else:
                        print("✨ Working tree clean.")
                except Exception:
                    pass

                return 0
            else:
                print(f"⚠️ Tmux popup exited with status {res.returncode}.")
                return res.returncode
        except Exception as e:
            print(f"⚠️ Failed to spawn tmux popup: {e}")
            return 1

    # 2. Interactive Terminal Fallback
    is_interactive = sys.stdin.isatty() and os.environ.get("TERM", "") != "dumb"
    if is_interactive:
        cmd = [lazygit_bin, "-p", str(repo_root)] + (extra_args or [])
        try:
            res = subprocess.run(cmd, cwd=str(repo_root), check=False)
            return res.returncode
        except Exception as e:
            print(f"⚠️ Failed to launch lazygit in terminal: {e}")
            return 1

    # 3. Headless / Non-Interactive Warning
    print("⚠️ No active tmux session or interactive TTY detected.")
    print(
        "   Lazygit is an interactive TUI application and requires a terminal or tmux."
    )
    print(
        f"   To review changes in [{repo_name}](file://{repo_root}) on branch `{branch}`, run:"
    )
    print(f"   $ cd {repo_root} && lazygit")
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for lazygit launcher."""
    parser = argparse.ArgumentParser(
        prog="lazygit-popup",
        description="Launch lazygit in a blocking tmux popup for agent review",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=None,
        help="Target git repository directory (defaults to cwd)",
    )
    parser.add_argument(
        "--no-popup",
        action="store_true",
        help="Bypass tmux popup and launch directly in terminal",
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Optional arguments forwarded to lazygit (e.g. log, branch, status, -f)",
    )

    args = parser.parse_args(argv)
    return launch_lazygit(
        cwd=args.path,
        extra_args=args.extra_args,
        no_popup=args.no_popup,
    )


if __name__ == "__main__":
    sys.exit(main())
