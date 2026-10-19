"""Claim / release / complete tasks safely across concurrent agents.

Claims live on the task line itself (`[wip: owner] [since: ISO]`), so they are
visible in TODO.md, survive restarts, and need no extra store. Every
read-modify-write runs under an exclusive fcntl lock on a per-backlog lock file
(outside the repo), so concurrent `claim_next` calls never hand out one task twice.
Only the touched task line is rewritten; headings, prose and other lines stay as-is.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from todo_navigator.models import Task
from todo_navigator.parser import parse_todo_file

DEFAULT_STALE = timedelta(hours=4)
DEFAULT_LOCK_DIR = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp") / "todo-navigator-locks"


def _iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _parse_iso(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@contextmanager
def _locked(todo_path: Path, lock_dir: Optional[Path]) -> Iterator[None]:
    d = lock_dir or DEFAULT_LOCK_DIR
    d.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(str(todo_path.resolve()).encode()).hexdigest()[:16]
    with open(d / f"{key}.lock", "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _write_line(todo_path: Path, task: Task) -> None:
    lines = todo_path.read_text(encoding="utf-8").splitlines()
    lines[task.line_no] = task.to_markdown_line()
    tmp = todo_path.with_name(f".{todo_path.name}.tmp-{os.getpid()}")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, todo_path)


def _find(tasks: List[Task], task_id: str) -> Optional[Task]:
    return next((t for t in tasks if t.id == task_id), None)


def _held_by_other(t: Task, owner: str, now: datetime, stale_after: timedelta) -> bool:
    if not t.wip or t.wip == owner:
        return False
    since = _parse_iso(t.wip_since)
    return since is None or now - since < stale_after


def _ready(tasks: List[Task]) -> List[Task]:
    done = {t.id for t in tasks if t.completed}
    ready = [t for t in tasks if not t.completed and all(d in done for d in t.depends_on)]
    return sorted(ready, key=lambda t: (-t.wsjf_score, t.priority))


def claim(
    todo_path: Path,
    task_id: str,
    owner: str,
    *,
    now: Optional[datetime] = None,
    lock_dir: Optional[Path] = None,
    stale_after: timedelta = DEFAULT_STALE,
) -> Tuple[bool, str]:
    now = now or datetime.now(timezone.utc)
    with _locked(todo_path, lock_dir):
        _, tasks, _ = parse_todo_file(todo_path)
        t = _find(tasks, task_id)
        if not t:
            return False, f"No task with id '{task_id}'."
        if t.completed:
            return False, f"Task '{task_id}' is already done."
        if _held_by_other(t, owner, now, stale_after):
            return False, f"Task '{task_id}' is claimed by {t.wip} since {t.wip_since}."
        t.wip, t.wip_since = owner, _iso(now)
        _write_line(todo_path, t)
        return True, f"Claimed '{task_id}' for {owner}."


def claim_next(
    todo_path: Path,
    owner: str,
    *,
    now: Optional[datetime] = None,
    lock_dir: Optional[Path] = None,
    stale_after: timedelta = DEFAULT_STALE,
) -> Optional[Task]:
    """Your current claim if any, else the top ready task nobody else holds (claimed atomically)."""
    now = now or datetime.now(timezone.utc)
    with _locked(todo_path, lock_dir):
        _, tasks, _ = parse_todo_file(todo_path)
        ready = _ready(tasks)
        mine = next((t for t in ready if t.wip == owner), None)
        pick = mine or next((t for t in ready if not _held_by_other(t, owner, now, stale_after)), None)
        if pick and pick.wip != owner:
            pick.wip, pick.wip_since = owner, _iso(now)
            _write_line(todo_path, pick)
        return pick


def release(
    todo_path: Path, task_id: str, owner: str, *, lock_dir: Optional[Path] = None, force: bool = False
) -> Tuple[bool, str]:
    with _locked(todo_path, lock_dir):
        _, tasks, _ = parse_todo_file(todo_path)
        t = _find(tasks, task_id)
        if not t:
            return False, f"No task with id '{task_id}'."
        if t.wip and t.wip != owner and not force:
            return False, f"Task '{task_id}' is claimed by {t.wip}, not {owner} (use --force)."
        t.wip = t.wip_since = ""
        _write_line(todo_path, t)
        return True, f"Released '{task_id}'."


def complete(
    todo_path: Path, task_id: str, *, now: Optional[datetime] = None, commit: str = "", lock_dir: Optional[Path] = None
) -> Tuple[bool, str]:
    now = now or datetime.now(timezone.utc)
    with _locked(todo_path, lock_dir):
        _, tasks, _ = parse_todo_file(todo_path)
        t = _find(tasks, task_id)
        if not t:
            return False, f"No task with id '{task_id}'."
        t.completed = True
        t.wip = t.wip_since = ""
        t.done_at = _iso(now)
        t.commit = commit or t.commit
        _write_line(todo_path, t)
        return True, f"Done '{task_id}'" + (f" ({commit})." if commit else ".")


def brief(todo_path: Path, owner: str) -> dict:
    """Small summary for injecting backlog awareness into an agent session."""
    _, tasks, _ = parse_todo_file(todo_path)
    open_tasks = [t for t in tasks if not t.completed]
    claimed = [{"id": t.id, "owner": t.wip, "since": t.wip_since} for t in open_tasks if t.wip and t.wip != owner]
    mine = [{"id": t.id, "title": t.title} for t in open_tasks if t.wip == owner]
    nxt = next((t for t in _ready(tasks) if not t.wip), None)
    return {
        "todo": str(todo_path),
        "open": len(open_tasks),
        "claimed": claimed,
        "mine": mine,
        "next": {"id": nxt.id, "title": nxt.title, "priority": nxt.priority} if nxt else None,
    }
