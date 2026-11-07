"""Pressure tab: where work piles up, what blocks the most, who to chase. Read-only, flow-oriented (Kanban).

Works on the whole open blocking graph of a project (all issue types), not only epics. Downstream counts are
transitive within the project plus direct external dependants. Nothing here writes to Jira.
"""
import datetime as dt, html, json
from jira_common import DEAD, EARLY, fieldmap, fv, search

INFLIGHT = {"Implementing", "In Progress", "Analyzing", "In Review", "Review", "Testing"}
STALL_DAYS, SOON_DAYS, IDLE_DAYS = 21, 14, 14


def from_jira(get, base, project):
    fm = fieldmap(get)
    team = fm.get("Team")
    fl = "summary,status,assignee,issuetype,statuscategorychangedate,duedate,issuelinks" + ("," + team if team else "")
    N = {}
    for i in search(get, f"project = {project} AND statusCategory != Done", fl):
        f = i["fields"]
        scd = f.get("statuscategorychangedate")
        N[i["key"]] = dict(key=i["key"], sum=f["summary"], st=f["status"]["name"], type=f["issuetype"]["name"],
                           who=(f.get("assignee") or {}).get("displayName", ""), due=f.get("duedate"),
                           age=(dt.date.today() - dt.date.fromisoformat(scd[:10])).days if scd else None,
                           team=(fv(f.get(team)) if team else "") or "", blocks=[], ext=False, _l=f["issuelinks"])
    for k, v in list(N.items()):
        for l in v.pop("_l"):
            if l["type"]["name"] != "Blocks":
                continue
            o = l.get("outwardIssue") or l.get("inwardIssue")
            if not o or o["fields"]["status"]["name"] in DEAD:
                continue
            ok = o["key"]
            if ok not in N:
                N[ok] = dict(key=ok, sum=o["fields"]["summary"], st=o["fields"]["status"]["name"], type="", who="", due=None, age=None,
                             team="", blocks=[], ext=ok.split("-")[0] != project)
            a, b = (k, ok) if l.get("outwardIssue") else (ok, k)
            if b not in N[a]["blocks"]:
                N[a]["blocks"].append(b)
    ext = [k for k, v in N.items() if "type" in v and v["type"] == "" and v["ext"]]
    for n in range(0, len(ext), 40):
        for i in search(get, "key in (%s)" % ",".join(ext[n:n + 40]), "assignee,duedate,statuscategorychangedate,issuetype"):
            f, v = i["fields"], N[i["key"]]
            v["who"] = (f.get("assignee") or {}).get("displayName", "")
            v["due"] = f.get("duedate")
            v["type"] = f["issuetype"]["name"]
            scd = f.get("statuscategorychangedate")
            v["age"] = (dt.date.today() - dt.date.fromisoformat(scd[:10])).days if scd else None
    return N


def analyse(N, project, today=None):
    today = today or dt.date.today()
    G = {k: [b for b in v["blocks"] if b in N] for k, v in N.items()}
    memo = {}

    def down(n):
        if n in memo:
            return memo[n]
        s, q = set(), list(G[n])
        while q:
            x = q.pop()
            if x not in s and x != n:
                s.add(x)
                q += G[x]
        memo[n] = s
        return s
    P = lambda s: dt.date.fromisoformat(s) if s else None
    rows = []
    for k, v in N.items():
        d = down(k)
        v["down"] = len(d)
        v["down_epics"] = sum(1 for x in d if N[x]["type"] == "Epic")
        v["consumers"] = sorted({x.split("-")[0] for x in d if x.split("-")[0] != project})
        dues = [P(N[x]["due"]) for x in d if N[x]["due"]]
        v["next_need"] = min(dues).isoformat() if dues else None
        fl = []
        own = not v["who"] and not v["ext"]
        if own:
            fl.append("no owner")
        dd = P(v["due"])
        if dd and dd < today:
            fl.append(f"overdue {(today - dd).days}d")
        elif dd and (dd - today).days <= SOON_DAYS:
            fl.append(f"due in {(dd - today).days}d")
        if v["st"] in INFLIGHT and v["age"] is not None and v["age"] >= STALL_DAYS:
            fl.append(f"stalled {v['age']}d")
        elif v["st"] in EARLY and v["age"] is not None and v["age"] >= IDLE_DAYS and v["down"]:
            fl.append(f"idle {v['age']}d, not started")
        v["flags"] = fl
        if v["down"] >= 2:
            rows.append(k)
    rows.sort(key=lambda k: (-N[k]["down"], -len(N[k]["flags"]), k))
    return rows[:15]


def wip(N, project):
    import collections
    T = collections.defaultdict(lambda: collections.Counter())
    for v in N.values():
        if v["ext"] or v["type"] == "" and v["ext"]:
            continue
        t = v["team"] or "(no team)"
        if v["st"] in INFLIGHT:
            T[t]["inflight"] += 1
            T[t]["epic" if v["type"] == "Epic" else "work"] += 1
        elif v["st"] in EARLY:
            T[t]["queue"] += 1
    return {t: dict(c) for t, c in sorted(T.items())}


def externals_holding(N, project):
    H = {}
    for k, v in N.items():
        if not v["ext"]:
            continue
        mine = [b for b in v["blocks"] if b in N and not N[b]["ext"]]
        if mine:
            H.setdefault(k.split("-")[0], []).append((k, mine))
    return H


def render(N, project, base, names):
    top = analyse(N, project)
    W = wip(N, project)
    H = externals_holding(N, project)
    e = html.escape
    link = lambda k: f'<a href="{e(base)}/browse/{e(k)}" target=_blank rel=noopener><b>{e(k)}</b></a>'
    def chips(fl):
        return "".join(f'<span class="chip {"warn" if any(x in f for x in ("no owner","overdue","not started")) else ""}">{e(f)}</span>' for f in fl)
    h = ['<div class=pr>']
    h.append("<section><h2>What blocks the most</h2><p>Open issues ranked by how many others sit behind them (all issue types, within this project plus direct dependants in other projects). Flags show why each is a pressure point.</p><table>"
            "<tr><th>#</th><th>Issue</th><th>Owner</th><th>Status</th><th>Behind it</th><th>Earliest need-by</th><th>Flags</th></tr>")
    for i, k in enumerate(top, 1):
        v = N[k]
        cons = (f'<div class=why>other projects: {e(", ".join(v["consumers"]))}</div>' if v["consumers"] else "")
        h.append(f'<tr><td>{i}</td><td>{link(k)} <span class=mute>{e(v["type"])}</span><div class=why>{e(v["sum"][:80])}</div></td>'
                 f'<td>{e(v["who"]) if v["who"] else ("—" if v["ext"] else "<span class=bad>none</span>")}</td>'
                 f'<td>{e(v["st"])}<div class=why>{(str(v["age"]) + " days in state") if v["age"] is not None else ""}</div></td>'
                 f'<td><b>{v["down"]}</b> issues' + (f", {v['down_epics']} epics" if v["down_epics"] else "") + f'{cons}</td>'
                 f'<td>{e(v["next_need"] or "—")}</td><td>{chips(v["flags"])}</td></tr>')
    h.append("</table></section>")
    h.append("<section><h2>Work in flight by team</h2><p>Epics and other work in Implementing, In Progress or Analyzing, with the queue waiting behind. Set a limit to see where a team is over it. Limits stay in this browser.</p><table id=wiptab>"
             "<tr><th>Team</th><th>In flight</th><th>Epics</th><th>Other work</th><th>Queue</th><th>Limit</th></tr>")
    for t, c in W.items():
        h.append(f'<tr data-team="{e(t)}" data-n="{c.get("inflight", 0)}"><td>{e(t)}</td><td><b>{c.get("inflight", 0)}</b></td><td>{c.get("epic", 0)}</td>'
                 f'<td>{c.get("work", 0)}</td><td>{c.get("queue", 0)}</td><td><input type=number min=0 class=lim style="width:4.5rem"> <span class=ovr></span></td></tr>')
    h.append("</table><p class=mute>Queue = Funnel, Backlog, New, To Do. In-flight counts only issues that exist in Jira at that level; hidden work is not counted.</p></section>")
    md = [f"# Chase list ({dt.date.today().isoformat()})", ""]
    groups = {}
    for k in top:
        v = N[k]
        if v["flags"] and not v["ext"]:
            groups.setdefault(v["who"] or "Unowned", []).append(k)
    h.append("<section><h2>Chase list</h2><p>Who to talk to, grouped. Top blockers that are unowned, not started, due soon or overdue; then other projects' items that hold up ours.</p>")
    for who, ks in sorted(groups.items(), key=lambda x: (x[0] != "Unowned", x[0])):
        h.append(f"<h3>{e(who)}</h3><ul>")
        md += [f"## {who}"]
        for k in ks:
            v = N[k]
            h.append(f'<li>{link(k)} {e(v["sum"][:70])} <span class=mute>[{e(v["st"])}, {v["down"]} behind it]</span> {chips(v["flags"])}</li>')
            md.append(f"- {k} {v['sum'][:70]} [{v['st']}, {v['down']} behind it]: {', '.join(v['flags'])}")
        h.append("</ul>")
        md.append("")
    if H:
        h.append("<h3>Other projects' items that hold up ours</h3>")
        md.append("## Other projects' items that hold up ours")
        for pk, items in sorted(H.items(), key=lambda x: -sum(len(m) for _, m in x[1])):
            h.append(f"<div class=pj><b>{e(names.get(pk, pk))}</b><ul>")
            md.append(f"### {names.get(pk, pk)}")
            for k, mine in sorted(items, key=lambda x: -len(x[1])):
                v = N[k]
                h.append(f'<li>{link(k)} {e(v["sum"][:70])} <span class=mute>[{e(v["st"])}{", due " + e(v["due"]) if v["due"] else ", no date"}{", " + e(v["who"]) if v["who"] else ""}]</span> holds up {len(mine)} of ours</li>')
                md.append(f"- {k} {v['sum'][:70]} [{v['st']}{', due ' + v['due'] if v['due'] else ', no date'}]: holds up {len(mine)} of ours")
            h.append("</ul></div>")
            md.append("")
    if not groups and not H:
        h.append("<p class=none>Nothing flagged.</p>")
    h.append('<p><button id=prcopy>Copy chase list as Markdown</button></p></section></div>')
    flagged = sum(1 for k in top if N[k]["flags"])
    return "".join(h), "\n".join(md), flagged


CSS = """
.pr{max-width:1150px}.pr section{background:#fff;border:1px solid var(--line);border-radius:12px;padding:.8rem 1.1rem;margin-bottom:1rem}.pr h2{margin:0;font-size:1rem}.pr h3{font-size:.9rem;margin:.8rem 0 .2rem}
.pr p{margin:.2rem 0 .6rem;color:var(--mute);font-size:.82rem}.pr table{width:100%;border-collapse:collapse;font-size:.86rem}
.pr th{text-align:left;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);padding:.3rem .5rem;border-bottom:1px solid var(--line)}.pr td{padding:.45rem .5rem;border-bottom:1px solid #f1f5f9;vertical-align:top}
.pr .why{color:var(--mute);font-size:.74rem}.pr .bad{color:#a61e4d;font-weight:700}.pr a{color:#1d4ed8;text-decoration:none}.pr ul{margin:.2rem 0 .4rem;padding-left:1.1rem;font-size:.85rem}.pr li{margin:.15rem 0}
.pr button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:.25rem .7rem;cursor:pointer;font-size:.82rem}.pr .pj{margin-left:.2rem}.pr .ovr{color:#a61e4d;font-weight:700;font-size:.8rem}
.pr tr.over td{background:#fff4f4}
"""

JS = r"""
(()=>{const D=JSON.parse(document.getElementById('data').textContent),t=document.getElementById('wiptab');if(!t)return;
const K='po-wiplimits:'+D.base+':'+(D.project||'');let L={};try{L=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
function paint(){t.querySelectorAll('tr[data-team]').forEach(r=>{const tm=r.dataset.team,n=+r.dataset.n,i=r.querySelector('.lim'),o=r.querySelector('.ovr');if(document.activeElement!==i)i.value=L[tm]==null?'':L[tm];
 const lim=L[tm];const over=lim!=null&&lim!==''&&n>lim;r.classList.toggle('over',over);o.textContent=over?('over by '+(n-lim)):''})}
t.querySelectorAll('tr[data-team]').forEach(r=>r.querySelector('.lim').oninput=e=>{const v=e.target.value;if(v==='')delete L[r.dataset.team];else L[r.dataset.team]=+v;try{localStorage.setItem(K,JSON.stringify(L))}catch(x){}paint()});
paint();const b=document.getElementById('prcopy');if(b)b.onclick=()=>{navigator.clipboard&&navigator.clipboard.writeText((D.pressure&&D.pressure.md)||'')}})();
"""
