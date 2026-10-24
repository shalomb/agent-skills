#!/usr/bin/env python3
"""
Bootstrap / cache Harness official JSON schemas for harness-pipeline.
Downloads schemas idempotently on first use or on demand.
"""

import sys
import urllib.request
from pathlib import Path

SCHEMA_BASE = "https://raw.githubusercontent.com/harness/harness-schema/main/v0"
SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = SKILL_DIR / "schemas"

SCHEMAS = {
    "pipeline.json": f"{SCHEMA_BASE}/pipeline.json",
    "template.json": f"{SCHEMA_BASE}/template.json",
    "trigger.json": f"{SCHEMA_BASE}/trigger.json",
}


def ensure_schemas(force: bool = False) -> None:
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in SCHEMAS.items():
        dest = SCHEMAS_DIR / filename
        if not force and dest.exists() and dest.stat().st_size > 0:
            continue
        print(f"↓ Fetching {filename} from {url}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                with open(dest, "wb") as f:
                    f.write(data)
            print(f"  ✓ {filename} cached successfully ({len(data)} bytes)")
        except Exception as e:
            print(f"  ⚠️ Warning: Failed to download {filename}: {e}", file=sys.stderr)


if __name__ == "__main__":
    force_download = "--force" in sys.argv
    ensure_schemas(force=force_download)
    print("✨ Schemas bootstrap complete.")
