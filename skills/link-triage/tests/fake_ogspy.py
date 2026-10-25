#!/usr/bin/env python3
"""Stand-in for `ogspy inspect --json`, reproducing the real tool's quirks:
errors are printed on STDOUT ahead of the JSON, unreachable URLs are absent from
the JSON, pages with no OG tags map to {}, and any failure makes the exit code 1.

Env: FAKE_OGSPY_DB  json {url: {"og": {...}} | {"error": "HTTP 404: 404 Not Found"}}
     FAKE_OGSPY_LOG optional file; one line is appended per URL actually requested.
"""
import json, os, sys

args = sys.argv[1:]
if not args or args[0] != "inspect":
    sys.exit("usage: fake ogspy inspect [flags] URL...")
urls, skip = [], False
for i, a in enumerate(args[1:], 1):
    if skip: skip = False; continue
    if a in ("-t", "--timeout", "-w", "--workers"): skip = True; continue
    if a.startswith("-") and a != "-": continue
    urls.append(a)
if "-" in urls:
    urls = [u for u in urls if u != "-"] + [l.strip() for l in sys.stdin if l.strip()]
db = json.load(open(os.environ["FAKE_OGSPY_DB"]))
log = os.environ.get("FAKE_OGSPY_LOG")
if log:
    with open(log, "a") as f:
        for u in urls: f.write(u + "\n")
out, failed = {}, False
for u in urls:
    e = db.get(u, {"error": 'Get "%s": dial tcp: lookup nowhere: no such host' % u})
    if "error" in e:
        print(f"Error fetching {u}: {e['error']}"); failed = True
    else:
        out[u] = e["og"]
print(json.dumps(out, indent=2))
if failed:
    print("Error: one or more URLs failed inspection", file=sys.stderr)
    sys.exit(1)
