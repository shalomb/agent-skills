#!/usr/bin/env python3
"""One interactive page for a Jira project: Dependencies, Timeline and Needs attention (read-only).

Writes <outdir>/index.html (the page), plus epics.svg and timeline.svg (standalone, Jira links, no popups) and
epics.mmd. Fetches the project once. Story views: pass --epic KEY (writes stories-KEY.html in the same shape).
"""
import argparse, html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_dag, jira_timeline, pressure, roadmap
from jira_common import ISSUE_FIELDS, app_page, client, collect, edges_of, search


def attention(I, tl):
    epics = {k: v for k, v in I.items() if v["core"]}
    ws = lambda v: float(v["ws"]) if v["ws"] not in (None, "") else -1
    order = lambda ks: sorted(ks, key=lambda k: (-ws(I[k]), int(k.split("-")[-1])))
    scored = sorted(ws(v) for v in epics.values() if ws(v) >= 0)
    top = scored[int(len(scored) * 0.75)] if scored else 99
    secs = []

    def add(title, why, ks, note=None):
        secs.append((title, why, order(ks), note or {}))
    add("External blockers not ready", "Blocked by another project's issue that is still early (Funnel, Backlog, New, To Do, Analyzing).",
        [k for k, v in epics.items() if v["warn"] and any("external blocker" in w for w in v["warn"])],
        {k: next((w for w in v["warn"] if "external blocker" in w), "") for k, v in epics.items()})
    from jira_common import EARLY
    def enab(v):
        return [r for r in v["blockedBy"] if not r["ext"] and r["k"] in I and not I[r["k"]]["core"] and r["st"] in EARLY]
    add("Blocked by enablers not started", "A task in this project blocks the epic and is still early (Funnel, Backlog, New, To Do, Analyzing). These are the roots to chase.",
        [k for k, v in epics.items() if enab(v)], {k: "waiting on " + ", ".join(r["k"] + " [" + r["st"] + "]" for r in enab(v))[:110] for k, v in epics.items() if enab(v)})
    add("Starts before its blocker ends", "Planned dates overlap with a blocker. May be intended for a thin first slice; the PO decides.",
        sorted({v for _, v in tl["conflicts"]}) if tl else [],
        {v: next((w for w in I[v]["warn"] if w.startswith("starts")), "") for _, v in (tl["conflicts"] if tl else [])})
    add("Priority does not match WSJF", "WSJF is in the top quarter but Priority is Low or Lowest.",
        [k for k, v in epics.items() if ws(v) >= top and v["pr"] in ("Low", "Lowest")], {k: f"WSJF {v['ws']}, Priority {v['pr']}" for k, v in epics.items()})
    add("No owner", "No assignee.", [k for k, v in epics.items() if not v["who"]])
    add("Not sliced", "No child issues.", [k for k, v in epics.items() if not v.get("children")])
    add("No WSJF score", "Business Value, Time Criticality, Risk Reduction or Job Size missing.", [k for k, v in epics.items() if ws(v) < 0])
    add("No parent initiative", "Not under an initiative, so it is not in the plan.", [k for k, v in epics.items() if not v["par"]])
    add("No target dates", "Target start or end missing, so the epic is not on the timeline.", [k for k, v in epics.items() if not (v["start"] and v["end"])])
    return secs


def attention_html(secs, I):
    out = ['<div class=att>']
    for title, why, ks, note in secs:
        out.append(f"<section><h2>{html.escape(title)}<span class=n>{len(ks)}</span></h2><p>{html.escape(why)}</p>")
        if not ks:
            out.append("<div class=none>Nothing to flag.</div></section>")
            continue
        out.append("<ul>")
        for k in ks:
            v = I[k]
            ext = " class=e" if v["ext_in"] or v["ext_out"] else ""
            ws = f" · WSJF {v['ws']}" if v["ws"] not in (None, "") else ""
            n = f' <span class=t>— {html.escape(note[k])}</span>' if note.get(k) else ""
            out.append(f'<li data-k="{html.escape(k)}"{ext}><b>{html.escape(k)}</b> <span class=t>{html.escape(v["sum"][:80])}</span>'
                       f' <span class=mute>[{html.escape(v["st"])}{ws}]</span>{n}</li>')
        out.append("</ul></section>")
    return "".join(out) + "</div>"


def facets(I, project, get, names):
    import collections
    cons, prov, lab = collections.Counter(), collections.Counter(), collections.Counter()
    for v in I.values():
        if not v["core"]:
            continue
        for key, bucket in (("blocks", cons), ("blockedBy", prov)):
            for pk in {r["k"].split("-")[0] for r in v[key] if r["ext"]}:
                bucket[pk] += 1
        for l in v.get("labels") or []:
            lab[l] += 1

    def nm(k):
        if k not in names:
            try:
                names[k] = get(f"/rest/api/3/project/{k}")["name"].replace("\u200b", "").strip() if get else k
            except Exception:
                names[k] = k
        return names[k]
    f = lambda c: [dict(k=k, name=f"{k} · {nm(k)}" if nm(k) != k else k, n=n) for k, n in sorted(c.items(), key=lambda x: (-x[1], x[0]))]
    return dict(cons=f(cons), prov=f(prov), labels=[dict(k=k, name=k, n=n) for k, n in sorted(lab.items(), key=lambda x: (-x[1], x[0]))])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url")
    p.add_argument("--project")
    p.add_argument("--outdir", required=True)
    p.add_argument("--synthetic", action="store_true", help="use built-in fake data; no Jira access at all")
    p.add_argument("--epic", help="story view for one epic instead of the project overview")
    p.add_argument("--relates", action="store_true")
    p.add_argument("--all", action="store_true")
    a = p.parse_args()
    if not a.synthetic and not (a.url and a.project):
        p.error("--url and --project are required unless --synthetic")
    os.makedirs(a.outdir, exist_ok=True)
    if a.synthetic:
        import synth
        a.project, base, get = synth.P, synth.BASE, None
    else:
        base = a.url.rstrip("/")
        get = client(base)
    if a.epic:
        I = collect(get, base, f"parent = {a.epic}", a.project)
        if not I:
            sys.exit(f"{a.epic} has no children (not sliced yet); nothing to draw")
        r = jira_dag.build(I, a)
        name = f"stories-{a.epic}"
        data = dict(base=base, issues={k: {x: v[x] for x in ISSUE_FIELDS if x in v} for k, v in I.items() if k in r["show"]})
        open(os.path.join(a.outdir, name + ".html"), "w").write(app_page(
            f"{a.project} · stories of {a.epic}", "Live from Jira · snapshot, not a validated record",
            [dict(id="dag", label="Dependencies", svg=r["svg"], legend=jira_dag.LEGEND, idmap=r["idmap"], edges=r["edges"])], data, sorted({v["st"] for v in I.values()})))
        open(os.path.join(a.outdir, name + ".svg"), "w").write(r["svg"])
        jira_dag.report(I, r, a)
        print(f"-> {a.outdir}/{name}.html")
        return
    if a.synthetic:
        I = synth.build()
    else:
        I = collect(get, base, f"project = {a.project} AND issuetype = Epic AND status not in (Done,Discarded)", a.project)
        epics = [k for k, v in I.items() if v["core"]]
        cnt = {k: 0 for k in epics}
        for i in range(0, len(epics), 40):
            for it in search(get, "parent in (%s)" % ",".join(epics[i:i + 40]), "parent"):
                cnt[it["fields"]["parent"]["key"]] += 1
        for k, v in I.items():
            v["children"] = cnt.get(k) if v["core"] else None
    dag = jira_dag.build(I, a)
    tl = jira_timeline.build(I, base)
    secs = attention(I, tl)
    fac = facets(I, a.project, get, dict(synth.NAMES) if a.synthetic else {})
    N = synth.flow() if a.synthetic else pressure.from_jira(get, base, a.project)
    names = {x["k"]: x["name"] for x in fac["cons"] + fac["prov"]}
    phtml, pmd, pflag = pressure.render(N, a.project, base, names)
    panels = [dict(id="pressure", label="Pressure", badge=pflag or None, html=phtml), dict(id="roadmap", label="Roadmap", html=roadmap.PANEL + ""), dict(id="brief", label="Briefing", html=roadmap.BRIEF), dict(id="dag", label="Dependencies", svg=dag["svg"], legend=jira_dag.LEGEND, idmap=dag["idmap"], edges=dag["edges"])]
    if tl:
        panels.append(dict(id="timeline", label="Timeline", svg=tl["svg"], legend=jira_timeline.LEGEND, edges=tl["E"]))
    nflag = sum(len(s[2]) for s in secs[:4])
    panels.append(dict(id="attention", label="Needs attention", badge=nflag or None, html=attention_html(secs, I)))
    data = dict(base=base, project=a.project, facets=fac, pressure=dict(md=pmd), alledges=[list(e) for e in edges_of(I)], issues={k: {x: v[x] for x in ISSUE_FIELDS} for k, v in I.items()})
    sub = ("SYNTHETIC DATA, not Jira · try things freely, nothing is written anywhere" if a.synthetic
           else "Live from Jira · snapshot, not a validated record · planned dates, not forecasts")
    page = app_page(f"{a.project} · portfolio" + (" (synthetic)" if a.synthetic else ""), sub, panels, data,
                    sorted({v["st"] for v in I.values() if v["core"]}), roadmap.CSS + pressure.CSS, roadmap.JS + pressure.JS)
    out = lambda n: os.path.join(a.outdir, n)
    open(out("index.html"), "w").write(page)
    open(out("epics.html"), "w").write('<!doctype html><meta charset=utf-8><meta http-equiv=refresh content="0;url=index.html#tab=dag"><a href="index.html#tab=dag">moved to index.html</a>')
    open(out("timeline.html"), "w").write('<!doctype html><meta charset=utf-8><meta http-equiv=refresh content="0;url=index.html#tab=timeline"><a href="index.html#tab=timeline">moved to index.html</a>')
    open(out("epics.mmd"), "w").write(dag["mmd"])
    open(out("epics.svg"), "w").write(dag["svg"])
    if tl:
        open(out("timeline.svg"), "w").write(tl["svg"])
    jira_dag.report(I, dag, a)
    if tl:
        print()
        jira_timeline.report(I, tl)
    print("\nNEEDS ATTENTION:")
    for title, _, ks, _ in secs:
        print(f"  {title}: {len(ks)}" + (f"  ({' '.join(k.split('-')[-1] for k in ks[:12])}{' …' if len(ks) > 12 else ''})" if ks else ""))
    print(f"\n-> {a.outdir}/index.html")


if __name__ == "__main__":
    main()
