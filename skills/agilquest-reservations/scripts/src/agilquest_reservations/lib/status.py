"""Offline status/calendar rendering from the cached reservations table.

Never touches the network or Chrome — reads whatever lib.cache last saved.
"""

import re
import sys
import calendar
from datetime import datetime, timedelta, timezone

STALE_AFTER = timedelta(hours=20)


def _parse_start_date(start: str) -> datetime | None:
    """'September 02, 2026 - 08:51 AM GMT+2' -> datetime(2026, 9, 2)."""
    m = re.match(r"([A-Za-z]+ \d{1,2}, \d{4})", start or "")
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%B %d, %Y")
    except ValueError:
        return None


def index_by_date(reservations: list[dict]) -> dict[str, dict]:
    """Map 'YYYY-MM-DD' -> reservation dict (first match wins per date)."""
    by_date = {}
    for r in reservations:
        d = _parse_start_date(r.get("start", ""))
        if d:
            key = d.strftime("%Y-%m-%d")
            by_date.setdefault(key, r)
    return by_date


STATUS_GLYPH = {
    "checked in": "c",
    "awaiting check in": "b",  # booked, awaiting check-in
    "cancelled": "x",
}


def render_status(cache: dict | None, days_ahead: int = 14, today: datetime | None = None) -> str:
    """Render today's status line plus a cal(1)-style grid for the next
    `days_ahead` days. `cache` is the dict loaded from lib.cache.load_reservations()."""
    today = today or datetime.now()
    lines = []

    if cache is None:
        lines.append("No cached reservation data yet.")
        lines.append("Run `aq checkin` or `aq book` once to populate the cache, then `aq status` will be instant.")
        return "\n".join(lines)

    fetched_at = cache.get("fetched_at", "")
    reservations = cache.get("reservations", [])
    by_date = index_by_date(reservations)

    try:
        fetched_dt = datetime.fromisoformat(fetched_at)
        if fetched_dt.tzinfo is None:
            fetched_dt = fetched_dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - fetched_dt
        stale = age > STALE_AFTER
        age_str = _humanize_age(age)
    except Exception:
        stale = True
        age_str = "unknown"

    today_key = today.strftime("%Y-%m-%d")
    today_resv = by_date.get(today_key)

    lines.append(f"Today ({today.strftime('%a %d %b %Y')}): " + _describe(today_resv))
    if stale:
        lines.append(f"⚠ cache is {age_str} old — run `aq checkin` or `aq book` to refresh")
    else:
        lines.append(f"(cache updated {age_str} ago)")
    lines.append("")
    lines.append(_render_calendar(by_date, today, days_ahead))
    return "\n".join(lines)


def _describe(resv: dict | None) -> str:
    if not resv:
        return "no reservation"
    status = resv.get("status", "unknown")
    return f"{status} ({resv.get('asset', '?')}, id {resv.get('id', '?')})"


def _humanize_age(age: timedelta) -> str:
    secs = int(age.total_seconds())
    if secs < 60:
        return f"{secs}s"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m"
    hrs = mins // 60
    if hrs < 48:
        return f"{hrs}h"
    return f"{hrs // 24}d"


def _render_calendar(by_date: dict[str, dict], today: datetime, days_ahead: int) -> str:
    """A cal(1)-style grid: one or more month blocks, Mon-first weeks,
    each day cell annotated with a status glyph when a reservation exists."""
    start = today.date()
    end = start + timedelta(days=days_ahead - 1)

    months = []
    cursor = start.replace(day=1)
    while cursor <= end:
        months.append((cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    blocks = [_render_month(y, m, by_date, start, end, today.date()) for y, m in months]
    return "\n\n".join(blocks)


CELL_WIDTH = 4  # "NNg " or "[NN]" — every cell renders to exactly this width


def _render_month(year: int, month: int, by_date: dict, range_start, range_end, today_date) -> str:
    """Each day cell is CELL_WIDTH chars: 2-digit day + 1 status glyph,
    space-padded. Today's cell is wrapped in [ ] in place of the glyph slot."""
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    weeks = cal.monthdatescalendar(year, month)
    header = datetime(year, month, 1).strftime("%B %Y").center(CELL_WIDTH * 7)
    dow = "".join(f" {d} " for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"])
    lines = [header, dow]

    for week in weeks:
        cells = []
        for day in week:
            if day.month != month:
                cells.append(" " * CELL_WIDTH)
                continue

            in_range = range_start <= day <= range_end
            key = day.strftime("%Y-%m-%d")
            resv = by_date.get(key) if in_range else None
            glyph = STATUS_GLYPH.get(resv.get("status", "").lower(), "?") if resv else " "

            if day == today_date:
                cells.append(f"[{day.day:>2}]".rjust(CELL_WIDTH))
            else:
                cells.append(f"{day.day:>2}{glyph} ")

        lines.append("".join(cells))

    return "\n".join(lines)
