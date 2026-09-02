"""Local on-disk cache of the last scraped reservations table.

Lets `aq status` render instantly without launching Chrome. Written as a
side effect every time get_reservations() does a live fetch; read-only
consumers (status) never touch the browser.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from agilquest_reservations.lib.browser import get_state_dir

CACHE_FILE = "reservations_cache.json"


def cache_path() -> Path:
    return get_state_dir() / CACHE_FILE


def save_reservations(reservations: list[dict]) -> None:
    """Write reservations to the cache with a fetched_at timestamp.
    Best-effort — cache write failures never break the calling script."""
    try:
        payload = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "reservations": reservations,
        }
        cache_path().write_text(json.dumps(payload, indent=2))
    except Exception:
        pass


def load_reservations() -> dict | None:
    """Return {'fetched_at': iso_str, 'reservations': [...]} or None if no
    cache exists yet or it's unreadable."""
    path = cache_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None
