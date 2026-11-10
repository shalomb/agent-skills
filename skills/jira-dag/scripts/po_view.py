#!/usr/bin/env python3
"""One interactive page for a Jira project: Dependencies, Timeline and Needs attention (read-only).

Writes <outdir>/index.html (the page), plus epics.svg and timeline.svg (standalone, Jira links, no popups) and
epics.mmd. Fetches the project once.
"""
import argparse, html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_dag, jira_timeline, pressure, roadmap, rules, topology
from jira_common import ISSUE_FIELDS, app_page, client, collect, edges_of, search


def attention(I, tl, tcfg=None):
    """Needs-attention sections, built from the data-quality rule set (rules.py)."""
    return rules.run(I, dict(conflicts=tl["conflicts"] if tl else [], topology=tcfg))


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
    p.add_argument("--topology", help="config blob (JSON/YAML) mapping PODs, interface and products to Jira projects; default ~/.config/jira-dag/topology.{yaml,json}")
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
    fac = facets(I, a.project, get, dict(synth.NAMES) if a.synthetic else {})
    N = synth.flow() if a.synthetic else pressure.from_jira(get, base, a.project)
    names = {x["k"]: x["name"] for x in fac["cons"] + fac["prov"]}
    phtml, pmd, pflag = pressure.render(N, a.project, base, names)
    panels = [dict(id="pressure", label="Pressure", badge=pflag or None, html=phtml), dict(id="roadmap", label="Roadmap", html=roadmap.PANEL + ""), dict(id="brief", label="Briefing", html=roadmap.BRIEF), dict(id="dag", label="Dependencies", svg=dag["svg"], legend=jira_dag.LEGEND, idmap=dag["idmap"], edges=dag["edges"])]
    if tl:
        panels.append(dict(id="timeline", label="Timeline", svg=tl["svg"], legend=jira_timeline.LEGEND, edges=tl["E"]))
    topo_issues, tp = {}, None
    tcfg0 = topology.load_config(a.topology) if a.topology else (None if a.synthetic else (lambda p: topology.load_config(p) if p else None)(topology.default_config_path()))
    tcfg = topology.load_config(a.topology) if a.topology else ({"art": "Synthetic ART", "pods": [{"id": a.project, "projects": [a.project]}]} if a.synthetic
                                                              else (lambda p: topology.load_config(p) if p else None)(topology.default_config_path()))
    secs = attention(I, tl, tcfg)
    if tcfg:
        if a.synthetic:
            TI = I
        else:
            pj = lambda ps: ",".join(ps)
            pods = [x for p in tcfg.get("pods", []) for x in p.get("projects", [])]
            rest = [x for g in ([tcfg.get("interface")] if tcfg.get("interface") else []) + tcfg.get("products", []) for x in g.get("projects", [])]
            jql = f"((project in ({pj(pods)}) AND issuetype = Epic)" + (f" OR project in ({pj(rest)})" if rest else "") + ") AND status not in (Done,Discarded)"
            TI = collect(get, base, jql, a.project)
        tp = topology.render(TI, tcfg)
        panels.append(dict(id="topology", label="Topologies", svg=tp["svg"], legend=topology.LEGEND, edges=tp["edges"]))
        topo_issues = {k: {x: v.get(x) for x in ISSUE_FIELDS} for k, v in TI.items() if k in tp["layout"]["nodes"]}
    for v in list(I.values()) + list(topo_issues.values()):
        v["tl"] = topology.card_groups(v.get("labels"), tcfg0)
    nflag = sum(len(s[2]) for s in secs[:4])
    panels.append(dict(id="attention", label="Needs attention", badge=nflag or None, html=attention_html(secs, I)))
    data = dict(base=base, project=a.project, facets=fac, pressure=dict(md=pmd), alledges=[list(e) for e in edges_of(I)], issues=dict({k: {x: v[x] for x in ISSUE_FIELDS} for k, v in I.items()}, **{k: t for k, t in topo_issues.items() if t.get("core") or k not in I}))
    sub = ("SYNTHETIC DATA, not Jira · try things freely, nothing is written anywhere" if a.synthetic
           else "Live from Jira · snapshot, not a validated record · planned dates, not forecasts")
    page = app_page(f"{a.project} · portfolio" + (" (synthetic)" if a.synthetic else ""), sub, panels, data,
                    sorted({v["st"] for v in I.values() if v["core"]}), roadmap.CSS + pressure.CSS + topology.CSS, roadmap.JS + pressure.JS + (topology.js(tp) if tp else ""))
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
