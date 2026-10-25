#!/usr/bin/env python3
"""Annotate links in markdown notes with Open Graph "link cards" (stdlib only; needs `ogspy`).

  triage.py annotate FILE... [--refresh] [--dry-run] [--workers N] [--timeout S]
  triage.py cards    FILE... [--json] [--status S] [--all]

A link card is a foldable Obsidian callout of Dataview `key:: value` fields placed directly
under a link line (see references/CARD.md). `annotate` writes only the fact fields; any other
field in the card (priority, tags, ...) belongs to later stages and is preserved.
Exit codes: 0 ok (dead links are data, not failure), 2 usage or ogspy unavailable/unusable.
"""
import argparse, datetime, json, math, os, re, shutil, subprocess, sys
from pathlib import Path

INSTALL_HINT = "install with: go install github.com/vincenzomaritato/ogspy@main"
# Order the fact fields are written in; everything else in a card is left to other stages.
FACTS = ["status", "title", "description", "site", "type", "image", "canonical", "http", "error", "checked"]
OG_MAP = {"title": "title", "description": "description", "site_name": "site", "type": "type",
          "image": "image", "url": "canonical"}
DEAD, BLOCKED = {404, 410}, {401, 403, 429}
SETTLED = {"ok", "no-og", "dead", "blocked"}      # error cards are retried
MAX_DESC, MAX_ERR = 400, 160

LINE = re.compile(r"^(?P<indent>\s*)(?P<bullet>(?:[-*+]|\d+[.)])\s+)?(?:\[[ xX]\]\s+)?(?P<rest>.*)$")
MDLINK = re.compile(r"^\[(?P<text>[^\]]*)\]\((?P<url>https?://[^)\s]+)\)")
BARE = re.compile(r"^(?P<url>https?://\S+)")
FIELD = re.compile(r"^>\s*(?P<key>[A-Za-z][\w-]*)::\s*(?P<val>.*)$")


class Link:
    def __init__(self, idx, pad, text, url):
        self.idx, self.pad, self.text, self.url = idx, pad, text, url
        self.card = None            # (start, end) line range, end exclusive
        self.fields = {}

    @property
    def status(self): return self.fields.get("status")


def parse(lines):
    """Link lines (outside frontmatter, code fences and callouts) with any card beneath them."""
    links, i, n = [], 0, len(lines)
    if lines and lines[0].strip() == "---":
        i = next((j + 1 for j in range(1, n) if lines[j].strip() == "---"), 0)
    fence = False
    while i < n:
        raw, s = lines[i], lines[i].strip()
        if s.startswith(("```", "~~~")): fence = not fence
        if fence or s.startswith((">", "```", "~~~")) or not s:
            i += 1; continue
        m = LINE.match(raw)
        rest = m["rest"].lstrip()
        hit = MDLINK.match(rest) or BARE.match(rest)
        if hit:
            url = hit["url"].rstrip(".,;:!?") if hit.re is BARE else hit["url"]
            text = hit.groupdict().get("text") or ""
            pad = m["indent"] + " " * len(m["bullet"] or "")
            link = Link(i, pad, text, url)
            j = i + 1
            if j < n and lines[j].strip().startswith("> [!link-card]"):
                while j < n and lines[j].strip().startswith(">"):
                    f = FIELD.match(lines[j].strip())
                    if f: link.fields[f["key"]] = f["val"].strip()
                    j += 1
                link.card = (i + 1, j)
            links.append(link)
        i += 1
    return links


def clean(v, limit=None):
    v = " ".join(str(v).split())
    return v[: limit - 1] + "…" if limit and len(v) > limit else v


def run_ogspy(ogspy, urls, timeout, workers):
    exe = shutil.which(ogspy) or (ogspy if os.access(ogspy, os.X_OK) else None)
    if not exe:
        die(f"ogspy not found ({ogspy}); {INSTALL_HINT}")
    budget = timeout * (math.ceil(len(urls) / max(workers, 1)) + 1) + 10
    try:
        p = subprocess.run([exe, "inspect", "--json", "-t", str(timeout), "-w", str(workers), "-"],
                           input="\n".join(urls) + "\n", capture_output=True, text=True, timeout=budget)
    except subprocess.TimeoutExpired:
        die(f"ogspy did not finish within {budget}s")
    errors, body = {}, []
    for line in p.stdout.splitlines():      # ogspy prints per-URL errors on stdout, ahead of the JSON
        m = re.match(r"^Error fetching (\S+):\s+(.*)$", line)
        if m: errors[m[1]] = m[2]
        else: body.append(line)
    try:
        data = json.loads("\n".join(body))
        assert isinstance(data, dict)
    except (ValueError, AssertionError):
        die(f"ogspy output was not JSON (exit {p.returncode}): {p.stdout[:120]!r} {p.stderr[:120]!r}")
    return data, errors


def facts_for(url, data, errors, today):
    og = data.get(url) if url in data else data.get(url.rstrip("/"), data.get(url + "/"))
    f = {}
    if url in errors or og is None:
        msg = errors.get(url, "no result returned by ogspy")
        code = re.search(r"HTTP (\d{3})", msg)
        code = int(code[1]) if code else None
        f["status"] = "dead" if code in DEAD else "blocked" if code in BLOCKED else "error"
        if code: f["http"] = str(code)
        if f["status"] == "error": f["error"] = clean(msg, MAX_ERR)
    else:
        for src, dst in OG_MAP.items():
            if og.get(src): f[dst] = clean(og[src], MAX_DESC if dst == "description" else None)
        f = {"status": "ok" if f.get("title") else "no-og", **f}
    f["checked"] = today
    return {k: f[k] for k in FACTS if k in f}


def title_line(f):
    s = f["status"]
    if s == "ok": return f["title"]
    return {"no-og": "no Open Graph tags", "dead": f"dead link (HTTP {f.get('http', '?')})",
            "blocked": f"blocked (HTTP {f.get('http', '?')})", "error": "unreachable"}[s]


def render(link, facts):
    extras = {k: v for k, v in link.fields.items() if k not in FACTS}
    body = [f"> [!link-card]- {title_line(facts)}"]
    body += [f"> {k}:: {v}" for k, v in {**facts, **extras}.items()]
    return [link.pad + b for b in body]


def die(msg):
    print(f"triage: {msg}", file=sys.stderr); sys.exit(2)


def cmd_annotate(a):
    files = {p: Path(p).read_text().split("\n") for p in a.files}
    parsed = {p: parse(ls) for p, ls in files.items()}
    todo = {p: [l for l in ls if l.card is None or l.status not in SETTLED or a.refresh] for p, ls in parsed.items()}
    urls = list(dict.fromkeys(l.url for ls in todo.values() for l in ls))
    n_links = sum(len(v) for v in todo.values())
    if a.dry_run:
        print(f"would annotate {n_links} link(s) in {sum(1 for v in todo.values() if v)} file(s); "
              f"{len(urls)} distinct URL(s) to fetch")
        for u in urls: print(f"  {u}")
        return 0
    if not urls:
        print("nothing to do: every link already has a settled card"); return 0
    data, errors = run_ogspy(a.ogspy, urls, a.timeout, a.workers)
    counts = {}
    for p, ls in todo.items():
        if not ls: continue
        lines = files[p]
        for link in sorted(ls, key=lambda l: -l.idx):          # bottom-up keeps indexes valid
            f = facts_for(link.url, data, errors, a.today)
            counts[f["status"]] = counts.get(f["status"], 0) + 1
            start, end = link.card or (link.idx + 1, link.idx + 1)
            lines[start:end] = render(link, f)
        Path(p).write_text("\n".join(lines))
    print(f"annotated {n_links} link(s): " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return 0


def cmd_cards(a):
    out = []
    for p in a.files:
        for l in parse(Path(p).read_text().split("\n")):
            if l.card is None and not a.all: continue
            if a.status and l.status != a.status: continue
            out.append({"file": p, "line": l.idx + 1, "url": l.url, "text": l.text,
                        "annotated": l.card is not None, "fields": l.fields})
    if a.json: print(json.dumps(out, indent=2))
    else:
        for c in out: print(f"{c['fields'].get('status', '-'):8} {c['url']}  {c['fields'].get('title', '')}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    an = sub.add_parser("annotate", help="insert or refresh link cards")
    an.add_argument("files", nargs="+")
    an.add_argument("--refresh", action="store_true", help="re-fetch every link, not only new or errored ones")
    an.add_argument("--dry-run", action="store_true")
    an.add_argument("--workers", type=int, default=4)
    an.add_argument("--timeout", type=int, default=10)
    an.add_argument("--ogspy", default=os.environ.get("OGSPY", "ogspy"))
    an.add_argument("--today", default=datetime.date.today().isoformat())
    an.set_defaults(fn=cmd_annotate)
    cd = sub.add_parser("cards", help="list link cards as data for later stages")
    cd.add_argument("files", nargs="+")
    cd.add_argument("--json", action="store_true")
    cd.add_argument("--status")
    cd.add_argument("--all", action="store_true", help="include links that have no card yet")
    cd.set_defaults(fn=cmd_cards)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
