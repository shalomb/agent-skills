"""Command line interface for understand_runs: python -m understand_runs.cli [args]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import GitRequiredError, make_report, parse_command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="understand_runs",
        description="Run the /understand discovery and report pipeline",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Repository or directory root to analyze (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON on stdout",
    )
    parser.add_argument(
        "command_args",
        nargs="*",
        help="Lens or command arguments (e.g. 'full', 'topic onboarding', 'pr 123', 'diff main')",
    )

    args = parser.parse_args(argv)

    cmd_text = " ".join(args.command_args).strip()
    lens = parse_command(cmd_text)
    target_path = Path(args.cwd).resolve()

    def on_phase(phase: str) -> None:
        print(f"PHASE:{phase}", flush=True)

    try:
        result = make_report(target_path, lens, on_phase=on_phase)
    except GitRequiredError as exc:
        print(f"ERROR:{exc}", file=sys.stderr, flush=True)
        return 2
    except Exception as exc:
        print(f"ERROR:{exc}", file=sys.stderr, flush=True)
        return 1

    if args.json:
        payload = {
            "run_dir": str(result.run_dir),
            "lens": {"type": result.lens.type, "target": result.lens.target},
            "urls": result.urls,
            "summary": result.summary,
            "end_message": result.end_message,
        }
        print(json.dumps(payload), flush=True)
    else:
        print(f"RUN_DIR:{result.run_dir}", flush=True)
        print(f"END_MESSAGE:\n{result.end_message}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
