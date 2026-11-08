#!/usr/bin/env python3
"""Copy artefacts into the shared report server's /r/ root and print their URLs.

Reuses the user-level nginx the `understand` skill runs (read from its generated
config under $XDG_RUNTIME_DIR). Starts nothing. Copies files (the server refuses
symlinks) and writes an index.html. Address and port are discovered, not fixed.
"""
import argparse, glob, html, os, re, shutil, socket, sys

ROOT = os.path.expanduser("~/.cache/agent-skills")
PREFIX = "po"  # sub-folder under /r/ for artefacts published by this tool
OK_EXT = {".html", ".htm", ".svg", ".png", ".jpg", ".jpeg", ".md", ".txt", ".json", ".css", ".js", ".mmd"}


SYSTEM_CONF = "/etc/nginx/conf.d/agent-skills.conf"  # installed once by understand's install-system.sh (ADR 0007)


def _answering(port):
    try:
        socket.create_connection(("127.0.0.1", int(port)), timeout=0.5).close()
        return True
    except OSError:
        return False


def system_endpoint(conf=SYSTEM_CONF, host=None, probe=_answering):
    """One canonical endpoint when the system nginx serves /r/; [] otherwise."""
    try:
        t = open(conf).read()
    except OSError:
        return []
    m = re.search(r"^\s*listen\s+(\d+)\s+default_server;", t, re.M)
    if not m or "location /r/" not in t or not probe(m.group(1)):
        return []
    return [("url", host or socket.gethostname(), m.group(1))]


def endpoints():
    """The system nginx (one name, port 80) if installed, else the per-network user instances."""
    system = system_endpoint()
    if system:
        return system
    run = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    out = []
    for conf in sorted(glob.glob(f"{run}/agent-skills/understand-server/*/nginx.conf")):
        t = open(conf).read()
        m = re.search(r"listen\s+([\w.:\[\]]+):(\d+);", t)
        if m and "location /r/" in t:
            out.append((os.path.basename(os.path.dirname(conf)), m.group(1), m.group(2)))
    return out


def slug(s):
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-.")
    return s or "x"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="folder name, e.g. <project>-<worktree>")
    p.add_argument("--title", default="")
    p.add_argument("files", nargs="+")
    a = p.parse_args()
    eps = endpoints()
    if not eps:
        sys.exit("no running report server found (is understand-report-server up?). Nothing published.")
    name = slug(a.name)
    dest = os.path.join(ROOT, PREFIX, name)
    os.makedirs(dest, exist_ok=True)
    kept = []
    for f in a.files:
        if os.path.islink(f) or not os.path.isfile(f):
            print(f"skip (not a regular file): {f}", file=sys.stderr)
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext not in OK_EXT:
            print(f"skip (type not allowed): {f}", file=sys.stderr)
            continue
        b = slug(os.path.basename(f))
        shutil.copyfile(f, os.path.join(dest, b))
        kept.append(b)
    for old in os.listdir(dest):  # keep the folder equal to this publish
        if old not in kept and not (old == "index.html" and "index.html" not in kept):
            os.remove(os.path.join(dest, old))
    rows = []
    for b in sorted(kept):
        ext = os.path.splitext(b)[1].lower()
        body = f'<img src="{html.escape(b)}" style="max-width:100%">' if ext in {".svg", ".png", ".jpg", ".jpeg"} else ""
        rows.append(f'<h3><a href="{html.escape(b)}">{html.escape(b)}</a></h3>{body}')
    if "index.html" not in kept:  # a caller-supplied landing page is never overwritten
        open(os.path.join(dest, "index.html"), "w").write(
            f"<!doctype html><meta charset=utf-8><title>{html.escape(a.title or name)}</title>"
            f"<body style='font-family:sans-serif;margin:1.5em'><h2>{html.escape(a.title or name)}</h2>"
            "<p>Snapshot of live data. Not a validated record.</p>" + "".join(rows))
    print(f"published {len(kept)} file(s) to {dest}")
    for net, host, port in eps:
        base = f"http://{host}{'' if port == '80' else ':' + port}/r/{PREFIX}/{name}/"
        label = "" if net == "url" else net
        print(f"{label:10s} {base}")
        for b in sorted(kept):
            print(f"{'':10s}   {base}{b}")


if __name__ == "__main__":
    main()
