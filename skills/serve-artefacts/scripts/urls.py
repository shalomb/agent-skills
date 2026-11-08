#!/usr/bin/env python3
"""Print report-server URLs for files that already live under ~/.cache/agent-skills.

Companion to publish.py for content that is served in place (for example a teach
workspace): nothing is copied, so the page stays live. Reads the running nginx
config (via publish.endpoints), starts nothing, refuses anything outside the
served root, behind a dot segment, or reached through a symlink.
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("publish", os.path.join(HERE, "publish.py"))
_publish = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_publish)
ROOT = os.path.realpath(_publish.ROOT)


def rel_under_root(path, root=ROOT):
    """Relative served path for `path`, or None if it must not be linked.

    The path is judged as given (not resolved): the server refuses a symlink at
    any level below the root and any dot segment, so we do too.
    """
    raw = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(raw):
        return None
    rel = os.path.relpath(raw, root)
    if rel == "." or rel.startswith(".."):
        return None
    cur = root
    for seg in rel.split(os.sep):
        cur = os.path.join(cur, seg)
        if seg.startswith(".") or os.path.islink(cur):
            return None
    return rel + ("/" if os.path.isdir(raw) else "")


def build(rel, endpoints):
    out = []
    for net, host, port in endpoints:
        h = f"[{host}]" if ":" in host and not host.startswith("[") else host
        out.append((net, f"http://{h}:{port}/r/{rel}"))
    return out


def main(argv):
    if not argv:
        sys.exit("usage: urls.py <path under ~/.cache/agent-skills>...")
    eps = _publish.endpoints()
    if not eps:
        sys.exit("no running report server found (is understand-report-server up?). Nothing to link.")
    bad = 0
    for a in argv:
        rel = rel_under_root(a)
        if rel is None:
            print(f"skip (not served: outside root, dot path, symlink or missing): {a}", file=sys.stderr)
            bad += 1
            continue
        print(a)
        for net, url in build(rel, eps):
            print(f"  {net.capitalize()+':':10s} {url}")
    return 1 if bad == len(argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
