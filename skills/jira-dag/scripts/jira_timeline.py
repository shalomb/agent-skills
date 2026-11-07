#!/usr/bin/env python3
"""Timeline of open epics from Target start/end as .svg + interactive .html (read-only).

Soft palette. Orange outline = depends on / blocks another project. Rose arrow = a blocker ends after the
blocked epic starts (a question for the PO, not an error). Dashed line = parent initiative due date.
"""
import argparse, collections, datetime as dt, html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jira_common import ISSUE_FIELDS, app_page, client, collect, critical_path, edges_of

FILL = {"Implementing": ("#bfe3cc", "#7fbf9a"), "In Progress": ("#bfe3cc", "#7fbf9a"), "Analyzing": ("#f9e8a8", "#e0c35c"),
        "Backlog": ("#cfdcef", "#93a9c9"), "Funnel": ("#e7e9ee", "#b6bcc6")}
LEGEND = [("background:#bfe3cc;border-color:#7fbf9a", "Implementing"), ("background:#f9e8a8;border-color:#e0c35c", "Analyzing"),
          ("background:#cfdcef;border-color:#93a9c9", "Backlog"), ("background:#e7e9ee;border-color:#b6bcc6", "Funnel"),
          ("background:#fff;border-color:#f08c4a", "orange outline = depends on / blocks another project"),
          ("background:#ffe3ea;border-color:#e5758f", "rose arrow = blocker ends after blocked epic starts")]
EARLY = {"Funnel", "Backlog", "New", "To Do", "Analyzing"}


def d(s):
    return dt.date.fromisoformat(s)


def e(s):
    return html.escape(str(s), quote=True)


def build(I, base):
    epics = {k: v for k, v in I.items() if v["core"]}
    dated = {k: v for k, v in epics.items() if v["start"] and v["end"]}
    undated = sorted(set(epics) - set(dated), key=lambda k: int(k.split("-")[-1]))
    if not dated:
        return None
    E = [(u, v) for u, v in edges_of(I) if u in dated and v in dated]
    path, _ = critical_path(E)
    conflicts = [(u, v) for u, v in E if dated[u]["end"] > dated[v]["start"]]
    for u, v in conflicts:
        w = f"starts {dated[v]['start']}, before blocker {u} ends {dated[u]['end']}"
        if w not in I[v]["warn"]:
            I[v]["warn"].append(w)
    lo = min(d(v["start"]) for v in dated.values())
    hi = max([d(v["end"]) for v in dated.values()] + [d(v["pardue"]) for v in dated.values() if v["pardue"]])
    today = dt.date.today()
    lo = lo.replace(day=1)
    hi = (hi.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    PPD, LEFT, TOP, RH, GH = 7.0, 400, 54, 32, 34
    X = lambda x: LEFT + (x - lo).days * PPD
    W = LEFT + (hi - lo).days * PPD + 24
    groups = collections.OrderedDict()
    for k in sorted(dated, key=lambda k: (dated[k]["par"] or "~", dated[k]["start"], k)):
        groups.setdefault(dated[k]["par"] or "no parent", []).append(k)
    y = TOP
    pos, gy = {}, {}
    for g, ks in groups.items():
        gy[g] = y
        y += GH
        for k in ks:
            pos[k] = y
            y += RH
        y += 8
    uy = y + 22
    H = uy + (60 + 34 * ((len(undated) + 3) // 4) if undated else 20)
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
         f'font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13">',
         '<defs><marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L8,4L0,8z" fill="#e5758f"/></marker></defs>',
         f'<rect width="{W:.0f}" height="{H:.0f}" fill="#fff"/>']
    m = lo
    i = 0
    while m < hi:
        n = (m.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
        S.append(f'<rect x="{X(m):.1f}" y="{TOP-24}" width="{(n-m).days*PPD:.1f}" height="{y-TOP+24:.0f}" fill="{"#f8fafc" if i%2 else "#fff"}"/>')
        S.append(f'<text x="{X(m)+8:.1f}" y="{TOP-34+22}" fill="#64748b" font-weight="600">{m.strftime("%b %Y")}</text>')
        S.append(f'<line x1="{X(m):.1f}" x2="{X(m):.1f}" y1="{TOP-24}" y2="{y:.0f}" stroke="#e2e8f0"/>')
        m, i = n, i + 1
    w = lo
    while w < hi:
        if w.weekday() == 0 and w.day != 1:
            S.append(f'<line x1="{X(w):.1f}" x2="{X(w):.1f}" y1="{TOP-4}" y2="{y:.0f}" stroke="#f1f5f9"/>')
        w += dt.timedelta(days=1)
    if lo <= today <= hi:
        S.append(f'<line x1="{X(today):.1f}" x2="{X(today):.1f}" y1="{TOP-24}" y2="{y:.0f}" stroke="#2dd4bf" stroke-width="1.5" stroke-dasharray="5 4"/>'
                 f'<text x="{X(today)+5:.1f}" y="{y+13:.0f}" fill="#0f766e" font-size="11">today</text>')
    for g, ks in groups.items():
        v0 = dated[ks[0]]
        S.append(f'<rect x="8" y="{gy[g]}" width="{W-16:.0f}" height="{GH-6}" rx="6" fill="#eef2f7"/>')
        link = f"{base}/browse/{g}" if g != "no parent" else None
        title = (v0["parsum"] or "")[:70]
        t = f'<text x="18" y="{gy[g]+(GH-6)/2+4}" font-weight="700" fill="#334155">{e(g)} <tspan font-weight="400" fill="#64748b">{e(title)}</tspan></text>'
        S.append(f'<a xlink:href="{e(link)}" target="_blank">{t}</a>' if link else t)
        if v0["pardue"] and lo <= d(v0["pardue"]) <= hi:
            xd = X(d(v0["pardue"]))
            S.append(f'<line x1="{xd:.1f}" x2="{xd:.1f}" y1="{gy[g]+GH-6}" y2="{pos[ks[-1]]+RH-4}" stroke="#d97796" stroke-dasharray="4 4"/>'
                     f'<path d="M{xd:.1f},{gy[g]+4}l7,{(GH-14)/2}l-7,{(GH-14)/2}l-7,-{(GH-14)/2}z" fill="#d97796"/>'
                     f'<text x="{xd-12:.1f}" y="{gy[g]+(GH-6)/2+4}" text-anchor="end" fill="#a8456a" font-size="11">due {e(v0["pardue"])}</text>')
    for u, v in conflicts:
        x1, y1, x2, y2 = X(d(dated[u]["end"])), pos[u] + RH / 2 - 3, X(d(dated[v]["start"])), pos[v] + RH / 2 - 3
        S.append(f'<path data-edge="{e(u)}|{e(v)}" d="M{x1:.1f},{y1:.1f}C{x1+34:.1f},{y1:.1f} {x2-34:.1f},{y2:.1f} {x2:.1f},{y2:.1f}" fill="none" '
                 f'stroke="#e5758f" stroke-opacity=".55" stroke-width="1.6" marker-end="url(#ar)"/>')
    for k, yy in pos.items():
        v = dated[k]
        fill, stroke = FILL.get(v["st"], ("#fff", "#b6bcc6"))
        ext = v["ext_in"] or v["ext_out"]
        x1, x2 = X(d(v["start"])), X(d(v["end"]))
        flag = ("◀▶ " if v["ext_in"] and v["ext_out"] else "◀ " if v["ext_in"] else "▶ " if v["ext_out"] else "")
        star = "★ " if k in path else ""
        ws = f"WSJF {v['ws']}" if v["ws"] not in (None, "") else ""
        tip = f"{k} · {v['sum']} · {v['st']} · {v['start']} → {v['end']}"
        S.append(f'<a xlink:href="{e(v["url"])}" target="_blank"><g data-key="{e(k)}"><title>{e(tip)}</title>'
                 f'<rect x="8" y="{yy-2}" width="{W-16:.0f}" height="{RH-2}" fill="transparent"/>'
                 f'<text x="18" y="{yy+RH/2+1}" fill="#1f2937"><tspan font-weight="700" fill="{"#a8456a" if k in path else "#1f2937"}">{star}{e(k)}</tspan>'
                 f'<tspan fill="#f08c4a" font-weight="700"> {flag}</tspan><tspan fill="#475569"> {e(v["sum"][:42])}{"…" if len(v["sum"])>42 else ""}</tspan></text>'
                 f'<rect x="{x1:.1f}" y="{yy+2}" width="{max(x2-x1,4):.1f}" height="{RH-10}" rx="7" fill="{fill}" stroke="{"#f08c4a" if ext else stroke}" stroke-width="{3 if ext else 1.4}"/>'
                 + (f'<text x="{x1+9:.1f}" y="{yy+RH/2+0}" fill="#374151" font-size="11.5">{e(ws)}</text>' if x2 - x1 > 70 and ws else "") + '</g></a>')
    if undated:
        S.append(f'<rect x="8" y="{uy}" width="{W-16:.0f}" height="{GH-6}" rx="6" fill="#fdf2e9"/>'
                 f'<text x="18" y="{uy+(GH-6)/2+4}" font-weight="700" fill="#9a4a14">No target dates ({len(undated)}) <tspan font-weight="400">not drawn</tspan></text>')
        for n, k in enumerate(undated):
            cx, cy = 18 + (n % 4) * 318, uy + 40 + (n // 4) * 34
            S.append(f'<a xlink:href="{e(epics[k]["url"])}" target="_blank"><g data-key="{e(k)}"><title>{e(epics[k]["sum"])}</title>'
                     f'<rect x="{cx}" y="{cy}" width="306" height="26" rx="13" fill="#fff" stroke="#e5c9ad"/>'
                     f'<text x="{cx+12}" y="{cy+17}" fill="#7a3d0e"><tspan font-weight="700">{e(k)}</tspan> {e(epics[k]["sum"][:30])}…</text></g></a>')
    S.append("</svg>")
    return dict(svg="\n".join(S), E=E, conflicts=conflicts, dated=dated, undated=undated, epics=epics)


def report(I, r):
    dated, undated, conflicts, epics = r["dated"], r["undated"], r["conflicts"], r["epics"]
    print(f"epics={len(epics)} dated={len(dated)} undated={len(undated)}")
    print("\nDATE CONFLICTS (blocker ends after the blocked epic starts):")
    for u, v in conflicts:
        print(f"  {u} ends {dated[u]['end']}  >  {v} starts {dated[v]['start']}   (gap {(d(dated[u]['end'])-d(dated[v]['start'])).days}d)")
    if not conflicts:
        print("  none")
    over = [(k, v["end"], v["pardue"]) for k, v in sorted(dated.items()) if v["pardue"] and v["end"] > v["pardue"]]
    print("\nEND AFTER PARENT DUE DATE:")
    for k, en, du in over:
        print(f"  {k} ends {en}, parent due {du}")
    if not over:
        print("  none")
    print("\nPROJECT-EXTERNAL DEPENDENCIES:", " ".join(f"{k.split('-')[-1]}{'◀' if v['ext_in'] else ''}{'▶' if v['ext_out'] else ''}" for k, v in sorted(epics.items()) if v["ext_in"] or v["ext_out"]) or "none")
    print("NO DATES (not drawn):", " ".join(k.split("-")[-1] for k in undated) or "none")
    print("Only epic-to-epic links are checked for date conflicts.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--out", required=True, help="output .svg path; .html is written beside it")
    a = p.parse_args()
    base = a.url.rstrip("/")
    I = collect(client(base), base, f"project = {a.project} AND issuetype = Epic AND status not in (Done,Discarded)", a.project)
    r = build(I, base)
    if not r:
        sys.exit("no epics with Target start and Target end")
    stem = os.path.splitext(a.out)[0]
    open(stem + ".svg", "w").write(r["svg"])
    keys = set(r["dated"]) | set(r["undated"])
    data = dict(base=base, issues={k: {x: I[k][x] for x in ISSUE_FIELDS} for k in keys})
    open(stem + ".html", "w").write(app_page(f"{a.project} · epic timeline", "Planned dates from Jira, not forecasts · snapshot, not a validated record",
                                             [dict(id="timeline", label="Timeline", svg=r["svg"], legend=LEGEND, edges=r["E"])], data,
                                             sorted({v["st"] for v in I.values() if v["core"]})))
    print(f"-> {stem}.{{svg,html}}")
    report(I, r)


if __name__ == "__main__":
    main()
