"""Structured result logging shared across entry points."""

import json
import sys


def log_result(result: dict):
    """Print JSON to stdout, then a single scannable RESULT: line to stderr."""
    print(json.dumps(result, indent=2))
    status = result.get("status", "unknown")
    parts = [f"RESULT: {status}"]
    if asset := result.get("asset_id"):
        parts.append(f"asset={asset}")
    if date := result.get("target_date"):
        parts.append(f"date={date}")
    if rid := result.get("reservation_id") or result.get("id"):
        parts.append(f"id={rid}")
    if status not in ("success", "already_exists", "ok") and (msg := result.get("message", "")):
        parts.append(f"— {msg.splitlines()[0]}")
    print(" ".join(parts), file=sys.stderr)
