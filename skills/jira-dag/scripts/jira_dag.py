#!/usr/bin/env python3
"""Mermaid dependency DAG from Jira Blocks links (read-only), as .mmd + .svg + interactive .html.

Epic view : open epics of a project plus one hop of open linked issues.
Story view: children of one epic plus one hop of open linked issues.
Orange = project-external dependency (incoming, outgoing or both). Red = critical path.
"""
import argparse, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jira_common import DEAD, ISSUE_FIELDS, app_page, client, collect, critical_path, edges_of, esc, search  # noqa: F401

STATUS_CLS = {"Implementing": "impl", "In Progress": "impl", "Analyzing": "ana", "Backlog": "bkl", "Funnel": "fun"}
EARLY = {"Funnel", "Backlog", "New", "To Do", "Analyzing"}
MMDC_CFG = {"securityLevel": "loose", "theme": "base", "flowchart": {"curve": "basis", "htmlLabels": True, "nodeSpacing": 28, "rankSpacing": 70, "wrappingWidth": 330},
            "themeVariables": {"fontFamily": "-apple-system, Segoe UI, Roboto, sans-serif", "fontSize": "17px", "lineColor": "#64748b"}}
LEGEND = [("background:#d6f0df;border-color:#168a4b", "Implementing"), ("background:#fff1b8;border-color:#c99700", "Analyzing"),
          ("background:#e6edf7;border-color:#51657f", "Backlog"), ("background:#f3f4f6;border-color:#9ca3af", "Funnel"),
          ("background:#fff;border-color:#e8590c", "orange ring = depends on / blocks another project"),
          ("background:#fff4e6;border-color:#e8590c;border-style:dashed", "other project"),
          ("background:#fff;border-color:#9ca3af;border-style:dashed", "not an epic of this view"),
          ("background:#fde8ef;border-color:#d6336c", "★ critical path (pink edges)")]


def build(I, a):
    """a needs .project .relates .all .epic. Returns dict with mmd, svg, panel data."""
    E = edges_of(I)
    rel = set()
    if a.relates:
        for k, v in I.items():
            for r in v["relates"]:
                if r["k"] in I:
                    rel.add(tuple(sorted((k, r["k"]))))
    used = {x for e in E for x in e} | {x for e in rel for x in e}
    isolated = sorted(k for k, v in I.items() if v["core"] and k not in used)
    show = {k for k, v in I.items() if k in used or (a.all and v["core"]) or (v["core"] and not E and not rel)}
    path, memo = critical_path(E)
    crit = set(zip(path, path[1:]))
    import collections
    G = collections.defaultdict(set)
    for u, v in E:
        G[u].add(v)

    def down(n, s=None):
        s = s if s is not None else set()
        for m in G[n]:
            if m not in s:
                s.add(m)
                down(m, s)
        return s
    ids = {k: re.sub(r"\W", "_", k) for k in show}
    L = ["flowchart LR"]
    for k in sorted(show):
        v = I[k]
        n = len(down(k))
        meta = " · ".join(x for x in [v["st"], f"WSJF {v['ws']}" if v["ws"] not in (None, "") else "", f"blocks {n}" if n else ""] if x)
        flag = "◀▶ EXTERNAL IN+OUT" if v["ext_in"] and v["ext_out"] else "◀ EXTERNAL IN" if v["ext_in"] else "EXTERNAL OUT ▶" if v["ext_out"] else ""
        star = "★ " if k in path else ""
        lab = f"**{star}{k}**\n{esc(v['sum'])[:56]}\n{meta}" + (f"\n**{flag}**" if flag else "")
        L.append(f'  {ids[k]}["`{lab}`"]')
    for k in sorted(show):
        v = I[k]
        L.append(f"  class {ids[k]} {STATUS_CLS.get(v['st'], 'oth')}")
        if k in path:
            L.append(f"  class {ids[k]} crit")
        if v["ext"]:
            L.append(f"  class {ids[k]} extnode")
        elif not v["core"]:
            L.append(f"  class {ids[k]} nbr")
        elif v["ext_in"] or v["ext_out"]:
            L.append(f"  class {ids[k]} extring")
    style = []
    n = 0
    for u, v in E:
        if u not in show or v not in show:
            continue
        L.append(f"  {ids[u]} ==> {ids[v]}" if (u, v) in crit else f"  {ids[u]} --> {ids[v]}")
        if (u, v) in crit:
            style.append((n, "stroke:#d6336c,stroke-width:4.5px"))
        elif I[u]["ext"] != I[v]["ext"]:
            style.append((n, "stroke:#e8590c,stroke-width:3px"))
        else:
            style.append((n, "stroke:#64748b,stroke-width:1.8px"))
        n += 1
    for u, v in sorted(rel):
        if u in show and v in show:
            L.append(f"  {ids[u]} -.- {ids[v]}")
            style.append((n, "stroke:#cbd5e1,stroke-width:1.4px"))
            n += 1
    for k in sorted(show):
        L.append(f'  click {ids[k]} href "{I[k]["url"]}" _blank')
    L += ["  classDef impl fill:#d6f0df,stroke:#168a4b,stroke-width:2px,color:#12351f",
          "  classDef ana fill:#fff1b8,stroke:#c99700,stroke-width:2px,color:#3d3000",
          "  classDef bkl fill:#e6edf7,stroke:#51657f,stroke-width:2px,color:#1e293b",
          "  classDef fun fill:#f3f4f6,stroke:#9ca3af,stroke-width:2px,color:#374151",
          "  classDef oth fill:#fff,stroke:#9ca3af,color:#374151",
          "  classDef nbr stroke-dasharray:3 3",
          "  classDef extring stroke:#e8590c,stroke-width:5px",
          "  classDef extnode fill:#fff4e6,stroke:#e8590c,stroke-width:3px,stroke-dasharray:6 4,color:#5c2a05",
          "  classDef crit stroke:#d6336c,stroke-width:5px"]
    L += [f"  linkStyle {i} {s}" for i, s in style]
    mmd = "\n".join(L) + "\n"
    with tempfile.TemporaryDirectory() as td:
        cfg, src, out = (os.path.join(td, n) for n in ("c.json", "g.mmd", "g.svg"))
        json.dump(MMDC_CFG, open(cfg, "w"))
        open(src, "w").write(mmd)
        r = subprocess.run(["mmdc", "-q", "-i", src, "-o", out, "-c", cfg, "-b", "white"], capture_output=True, text=True)
        if r.returncode:
            sys.exit("mmdc failed: " + (r.stderr or r.stdout).strip()[:400])
        svg = open(out).read()
    return dict(mmd=mmd, svg=svg, idmap={ids[k]: k for k in show}, edges=[list(e) for e in E if e[0] in show and e[1] in show],
                show=show, path=path, isolated=isolated, E=E)


def report(I, r, a):
    show = r["show"]
    ne = sum(1 for k in show if I[k]["ext_in"] or I[k]["ext_out"])
    print(f"nodes={len(show)} blocks_edges={len(r['E'])} critical_path_len={max(len(r['path'])-1,0)} external_ring={ne}")
    print("critical path:", " -> ".join(r["path"]))
    for k in sorted(show):
        v = I[k]
        if v["core"] and (v["ext_in"] or v["ext_out"]):
            print(f"  external: {k} {'in ' if v['ext_in'] else ''}{'out' if v['ext_out'] else ''}  {v['warn'][0] if v['warn'] else ''}")
    if r["isolated"] and not a.all:
        print(f"{len(r['isolated'])} epics with no links hidden (use --all): " + " ".join(k.split('-')[-1] for k in r["isolated"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--epic")
    p.add_argument("--relates", action="store_true")
    p.add_argument("--all", action="store_true", help="also draw epics with no links")
    p.add_argument("--out", required=True, help="output .mmd path; .svg and .html are written beside it")
    a = p.parse_args()
    base = a.url.rstrip("/")
    jql = f"parent = {a.epic}" if a.epic else f"project = {a.project} AND issuetype = Epic AND status not in (Done,Discarded)"
    I = collect(client(base), base, jql, a.project)
    if not I:
        open(a.out, "w").write('flowchart LR\n  empty["no issues match"]\n')
        print(f"nodes=0 -> {a.out} (no issues match; epic has no children?)")
        return
    r = build(I, a)
    stem = os.path.splitext(a.out)[0]
    open(a.out, "w").write(r["mmd"])
    open(stem + ".svg", "w").write(r["svg"])
    title = f"{a.project} · stories of {a.epic}" if a.epic else f"{a.project} · epic dependencies"
    data = dict(base=base, issues={k: {x: v[x] for x in ISSUE_FIELDS} for k, v in I.items() if k in r["show"]})
    open(stem + ".html", "w").write(app_page(title, "Live from Jira · snapshot, not a validated record",
                                             [dict(id="dag", label="Dependencies", svg=r["svg"], legend=LEGEND, idmap=r["idmap"], edges=r["edges"])],
                                             data, sorted({v["st"] for v in I.values() if v["core"]})))
    print(f"-> {stem}.{{mmd,svg,html}}")
    report(I, r, a)


if __name__ == "__main__":
    main()
