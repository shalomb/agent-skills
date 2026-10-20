#!/usr/bin/env python3
"""tmux-a2a.py - dispatch a task to the agent in a tmux pane over A2A and wait for its reply.

  tmux-a2a.py send [-t SECONDS] [-f FILE] TARGET [BRIEF]

TARGET is `window.pane` (current session) or `session:window.pane`. The pane's agent is found
through its handshake file (written by the pi `a2a-server` extension when PI_A2A=1):

    $PI_A2A_DIR or $XDG_RUNTIME_DIR/pi/a2a/<sessionId>.a2a.json     {pid, url, token, ...}

The file is matched to the pane by process ancestry (agent pid descends from the pane's shell
pid), never by pane id alone, which is ambiguous across tmux servers. Only loopback http
endpoints in a 0700 directory with 0600 files are used; the token is never printed.

stdout: the agent's reply (exit 0) or the question it is blocked on (exit 4).  stderr: status.
Exit codes: 0 completed | 1 usage | 2 failed/canceled | 3 no endpoint (caller may fall back to
pasting) | 4 input-required | 5 timeout (task id on stderr) | 6 auth/transport error.
Standard library only.
"""
import ipaddress
import json
import os
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

MAX_FILE = 64 * 1024
TERMINAL = {"completed", "failed", "canceled"}


# ---- process ancestry -------------------------------------------------------
def proc_parent(pid, proc_root="/proc"):
    """Parent pid from /proc/<pid>/stat. Fields are parsed after the LAST ')' because the
    command name may contain spaces and parentheses."""
    try:
        with open(os.path.join(proc_root, str(pid), "stat")) as f:
            s = f.read()
        rest = s[s.rindex(")") + 2:].split()
        return int(rest[1])
    except (OSError, ValueError, IndexError):
        return None


def is_descendant(pid, ancestor, parent_of, limit=64):
    seen = set()
    cur = pid
    for _ in range(limit):
        if cur == ancestor:
            return True
        if cur is None or cur <= 1 or cur in seen:
            return False
        seen.add(cur)
        cur = parent_of(cur)
    return False


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# ---- handshake files --------------------------------------------------------
def is_loopback_url(url):
    try:
        u = urllib.parse.urlsplit(url)
        if u.scheme != "http" or u.username or u.password or not u.hostname:
            return False
        if u.hostname == "localhost":
            return True
        return ipaddress.ip_address(u.hostname).is_loopback
    except ValueError:
        return False


def default_dir(env=os.environ):
    if env.get("PI_A2A_DIR", "").startswith("/"):
        return env["PI_A2A_DIR"]
    run = env.get("XDG_RUNTIME_DIR", "")
    base = run if run.startswith("/") else f"/tmp/pi-runtime-{os.getuid()}"
    return os.path.join(base, "pi", "a2a")


def _dir_ok(d):
    try:
        st = os.lstat(d)
    except OSError:
        return False
    return stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid() and (st.st_mode & 0o077) == 0


def load_handshakes(d):
    """Valid handshake records, skipping anything unsafe or malformed."""
    if not _dir_ok(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".a2a.json"):
            continue
        p = os.path.join(d, name)
        try:
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE:
                continue
            if st.st_uid != os.getuid() or (st.st_mode & 0o077) != 0:
                continue
            with open(p) as f:
                h = json.load(f)
        except (OSError, ValueError):
            continue
        if not (isinstance(h, dict) and isinstance(h.get("pid"), int) and isinstance(h.get("url"), str)
                and isinstance(h.get("token"), str) and h["token"] and isinstance(h.get("sessionId"), str)):
            continue
        if not is_loopback_url(h["url"]):
            continue
        out.append(h)
    return out


def find_endpoint(d, pane_pid, parent_of=proc_parent, alive=pid_alive):
    cands = [h for h in load_handshakes(d) if alive(h["pid"]) and is_descendant(h["pid"], pane_pid, parent_of)]
    if not cands:
        return None
    return max(cands, key=lambda h: h.get("startedAt", ""))


# ---- A2A client -------------------------------------------------------------
class TransportError(Exception):
    pass


class A2AClient:
    def __init__(self, url, token, timeout=30):
        self.url, self.token, self.timeout = url, token, timeout
        self._n = 0
        # No proxies: this only ever talks to loopback.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def rpc(self, method, params):
        self._n += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._n, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "content-type": "application/json", "authorization": f"Bearer {self.token}"})
        try:
            with self._opener.open(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            raise TransportError("unauthorized (bad token)" if code == 401 else f"http {code}") from None
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise TransportError(f"endpoint unreachable ({type(e).__name__})") from None
        if "error" in data:
            raise TransportError(f"rpc error: {data['error'].get('message', data['error'])}")
        return data["result"]


@dataclass
class Result:
    state: str
    text: str
    exit_code: int
    task_id: str = ""


def _text_of(parts):
    return "\n".join(p.get("text", "") for p in (parts or []) if isinstance(p, dict) and p.get("kind") == "text")


def _reply(task):
    arts = task.get("artifacts") or []
    return _text_of(arts[0].get("parts")) if arts else ""


def _status_text(task):
    msg = (task.get("status") or {}).get("message") or {}
    return _text_of(msg.get("parts"))


def send_and_wait(client, text, deadline=300.0, poll=0.3):
    end = time.monotonic() + deadline
    try:
        task = client.rpc("message/send", {"message": {"role": "user", "parts": [{"kind": "text", "text": text}]}})
        tid = task["id"]
        while True:
            state = task["status"]["state"]
            if state == "completed":
                return Result(state, _reply(task), 0, tid)
            if state in ("failed", "canceled"):
                return Result(state, _status_text(task) or state, 2, tid)
            if state == "input-required":
                return Result(state, _status_text(task), 4, tid)
            if time.monotonic() >= end:
                return Result(state, "", 5, tid)
            time.sleep(poll)
            task = client.rpc("tasks/get", {"id": tid})
    except TransportError as e:
        return Result("error", str(e), 6)


def cli_send(d, pane_pid, text, deadline, parent_of=proc_parent, alive=pid_alive):
    """Returns (exit_code, stdout, stderr). Pure enough to test without tmux."""
    h = find_endpoint(d, pane_pid, parent_of, alive)
    if not h:
        return 3, "", "no a2a endpoint for this pane"
    r = send_and_wait(A2AClient(h["url"], h["token"]), text, deadline=deadline)
    if r.exit_code in (0, 4):
        return r.exit_code, r.text, ("" if r.exit_code == 0 else f"input-required (task {r.task_id}): the agent is waiting on a human")
    if r.exit_code == 5:
        return 5, "", f"timed out in state {r.state} (task {r.task_id})"
    return r.exit_code, "", r.text


# ---- tmux + main ------------------------------------------------------------
def resolve_pane(target):
    if ":" not in target:
        cur = subprocess.run(["tmux", "display-message", "-p", "#{session_name}"], capture_output=True, text=True)
        if cur.returncode != 0:
            raise SystemExit("tmux-a2a.py: bare target needs a running tmux server")
        target = f"{cur.stdout.strip()}:{target}"
    r = subprocess.run(["tmux", "display-message", "-p", "-t", target, "#{pane_pid} #{pane_id}"], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise SystemExit(f"tmux-a2a.py: no such pane: {target}")
    pid, pane_id = r.stdout.split()
    return int(pid), pane_id


def main(argv):
    args = argv[1:]
    if not args or args[0] != "send":
        print(__doc__, file=sys.stderr)
        return 1
    args = args[1:]
    deadline, brief_file, rest = 300.0, None, []
    i = 0
    while i < len(args):
        if args[i] == "-t" and i + 1 < len(args):
            try:
                deadline = float(args[i + 1])
            except ValueError:
                print("tmux-a2a.py: -t needs a number of seconds", file=sys.stderr)
                return 1
            i += 2
        elif args[i] == "-f" and i + 1 < len(args):
            brief_file = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    if brief_file:
        if len(rest) != 1:
            print("usage: tmux-a2a.py send [-t SEC] -f FILE TARGET", file=sys.stderr)
            return 1
        text = open(brief_file).read()
    elif len(rest) == 2:
        text = rest[1]
    else:
        print("usage: tmux-a2a.py send [-t SEC] [-f FILE] TARGET [BRIEF]", file=sys.stderr)
        return 1
    pane_pid, pane_id = resolve_pane(rest[0])
    if pane_id == os.environ.get("TMUX_PANE"):
        print("tmux-a2a.py: refusing to dispatch into the agent's own pane", file=sys.stderr)
        return 1
    code, out, err = cli_send(default_dir(), pane_pid, text, deadline)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
