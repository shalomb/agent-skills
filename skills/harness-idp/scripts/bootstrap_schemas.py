#!/usr/bin/env python3
"""
Bootstrap / cache Harness IDP & Backstage official schemas for harness-idp.
Downloads schemas idempotently on first use or on demand.
"""

import sys
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = SKILL_DIR / "schemas"

SCHEMAS = {
    "harness-entities-api.yaml": "https://raw.githubusercontent.com/api-evangelist/harness/main/openapi/harness-entities-api-openapi.yml",
    "backstage-catalog-schema.json": "https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/Entity.schema.json",
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
    print("✨ IDP schemas bootstrap complete.")
