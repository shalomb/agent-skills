"""Shared read-only Jira helpers and the HTML viewer used by the DAG and timeline scripts."""
import base64, json, netrc, re, sys, urllib.parse, urllib.request

DEAD = {"Done", "Discarded", "Closed", "Cancelled", "Resolved"}
ISSUE_FIELDS = ("key", "sum", "st", "pr", "ws", "who", "team", "par", "pardue", "start", "end", "url", "blocks", "blockedBy",
                "relates", "ext_in", "ext_out", "ext", "warn", "core", "children", "due", "refine", "flagged", "parsum", "labels", "tl")
EARLY = {"Funnel", "Backlog", "New", "To Do", "Analyzing"}


def client(url):
    host = urllib.parse.urlparse(url).hostname
    a = netrc.netrc().authenticators(host)
    if not a:
        sys.exit(f"no ~/.netrc entry for {host}")
    tok = base64.b64encode(f"{a[0]}:{a[2]}".encode()).decode()

    def get(path, **q):
        r = urllib.request.Request(f"{url}{path}?{urllib.parse.urlencode(q)}",
                                   headers={"Authorization": f"Basic {tok}", "Accept": "application/json"})
        return json.load(urllib.request.urlopen(r, timeout=60))
    return get


def search(get, jql, fields):
    out, tok = [], None
    while True:
        q = dict(jql=jql, fields=fields, maxResults=100)
        if tok:
            q["nextPageToken"] = tok
        d = get("/rest/api/3/search/jql", **q)
        out += d["issues"]
        tok = d.get("nextPageToken")
        if not tok:
            return out


def esc(s):
    return re.sub(r'["\[\]{}()<>|#&`*\\]', "", s or "")


def num(v):
    try:
        return float(v) if v is not None and str(v).strip() else None
    except (ValueError, TypeError):
        return None


def fv(v):
    if isinstance(v, dict):
        return v.get("name") or v.get("displayName") or v.get("value") or v.get("key") or ""
    return v


def fieldmap(get):
    return {f["name"]: f["id"] for f in get("/rest/api/3/field")}


def collect(get, base, jql, project):
    """Fetch issues for jql plus their open linked neighbours. Returns {key: info}."""
    fm = fieldmap(get)
    ids = {n: fm.get(n) for n in ("WSJF", "Target start", "Target end", "Team", "Refinement Status", "Flagged")}
    fl = ["summary", "status", "priority", "parent", "issuelinks", "assignee", "duedate", "labels"] + [i for i in ids.values() if i]
    issues = search(get, jql, ",".join(fl))
    I = {}
    for i in issues:
        f = i["fields"]
        I[i["key"]] = dict(key=i["key"], sum=f["summary"], st=f["status"]["name"], pr=(f.get("priority") or {}).get("name", ""),
                           ws=num(f.get(ids["WSJF"])) if ids["WSJF"] else None, who=(f.get("assignee") or {}).get("displayName", ""),
                           team=fv(f.get(ids["Team"])) if ids["Team"] else "", par=(f.get("parent") or {}).get("key", ""),
                           start=f.get(ids["Target start"]) if ids["Target start"] else None,
                           end=f.get(ids["Target end"]) if ids["Target end"] else None,
                           labels=f.get("labels") or [], due=f.get("duedate"), refine=fv(f.get(ids["Refinement Status"])) if ids["Refinement Status"] else "",
                           flagged=bool(f.get(ids["Flagged"])) if ids["Flagged"] else False,
                           url=f"{base}/browse/{i['key']}", core=True, blocks=[], blockedBy=[], relates=[], _links=f["issuelinks"])
    for k, v in list(I.items()):
        for l in v.pop("_links"):
            o = l.get("outwardIssue") or l.get("inwardIssue")
            if not o:
                continue
            st = o["fields"]["status"]["name"]
            if st in DEAD:
                continue
            nk = o["key"]
            if nk not in I:
                I[nk] = dict(key=nk, sum=o["fields"]["summary"], st=st, pr="", ws=None, who="", team="", par="", start=None, end=None,
                             due=None, labels=[], refine="", flagged=False,
                             url=f"{base}/browse/{nk}", core=False, blocks=[], blockedBy=[], relates=[])
            ref = dict(k=nk, st=st, s=o["fields"]["summary"], ext=nk.split("-")[0] != project)
            t = l["type"]["name"]
            if t == "Blocks":
                (v["blocks"] if l.get("outwardIssue") else v["blockedBy"]).append(ref)
            elif t == "Relates":
                v["relates"].append(ref)
    pars = sorted({v["par"] for v in I.values() if v["par"]})
    due = {}
    if pars:
        for i in search(get, "key in (%s)" % ",".join(pars), "summary,duedate"):
            due[i["key"]] = (i["fields"]["summary"], i["fields"].get("duedate"))
    for v in I.values():
        v["pardue"] = due.get(v["par"], ("", None))[1]
        v["parsum"] = due.get(v["par"], ("", None))[0]
    nb = [k for k, v in I.items() if not v["core"]]
    for n in range(0, len(nb), 40):  # due dates of neighbours, so enablers can feed the forecast
        for it in search(get, "key in (%s)" % ",".join(nb[n:n + 40]), "duedate"):
            I[it["key"]]["due"] = it["fields"].get("duedate")
    return finalize(I, project)


def finalize(I, project):
    """Derive cross-project flags and warnings. Shared by live and synthetic data."""
    for v in I.values():
        # project-external dependencies, both directions (open issues only)
        v["ext_in"] = any(r["ext"] for r in v["blockedBy"]) and v["key"].split("-")[0] == project
        v["ext_out"] = any(r["ext"] for r in v["blocks"]) and v["key"].split("-")[0] == project
        v["ext"] = v["key"].split("-")[0] != project
        v["warn"] = [f"external blocker still {r['st']}: {r['k']}" for r in v["blockedBy"] if r["ext"] and r["st"] in EARLY][:3]
    return I


def edges_of(I):
    e = set()
    for k, v in I.items():
        for r in v["blocks"]:
            if r["k"] in I:
                e.add((k, r["k"]))
        for r in v["blockedBy"]:
            if r["k"] in I:
                e.add((r["k"], k))
    return sorted(e)


def critical_path(E):
    import collections
    G = collections.defaultdict(list)
    for a, b in E:
        G[a].append(b)
    memo = {}

    def d(n, seen=()):
        if n in memo:
            return memo[n]
        if n in seen:
            return 0
        memo[n] = 1 + max([d(m, seen + (n,)) for m in G[n]] or [0])
        return memo[n]
    nodes = {x for e in E for x in e}
    for n in nodes:
        d(n)
    if not nodes:
        return [], memo
    n = max(nodes, key=lambda x: memo[x])
    path = [n]
    while G[n]:
        n = max(G[n], key=lambda m: memo[m])
        path.append(n)
    return path, memo


CSS = """
:root{--ink:#1f2937;--mute:#6b7280;--line:#e5e7eb;--bg:#f8fafc;--card:#fff;--ext:#e8590c}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:.55rem 1rem;display:flex;gap:.9rem;align-items:center;flex-wrap:wrap}
header h1{font-size:1.05rem;margin:0}header .sub{color:var(--mute);font-size:.78rem}
nav{display:flex;gap:.2rem}nav button{border:0;background:none;padding:.35rem .8rem;border-radius:8px;cursor:pointer;font-size:.9rem;color:#475569}
nav button.on{background:#eef2ff;color:#3730a3;font-weight:600}nav .n{background:#fde8ef;color:#a61e4d;border-radius:999px;padding:0 .4rem;font-size:.72rem;margin-left:.3rem}
.filters{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap;margin-left:auto}
.filters input[type=search]{border:1px solid var(--line);border-radius:8px;padding:.28rem .6rem;width:15rem;font-size:.85rem}
.fb{border:1px solid var(--line);background:#fff;border-radius:999px;padding:.12rem .6rem;cursor:pointer;font-size:.78rem;color:#475569}
.fb[aria-pressed=true]{background:#1f2937;color:#fff;border-color:#1f2937}.fs{border:1px solid var(--line);border-radius:999px;padding:.12rem .4rem;font-size:.78rem;background:#fff;color:#475569;max-width:15rem}
.fb.ext[aria-pressed=true]{background:var(--ext);border-color:var(--ext)}
.ctl button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:.1rem .55rem;cursor:pointer}
.panel{display:none;padding:.8rem 1rem 2rem}.panel.on{display:block}
.legend{display:flex;gap:.9rem;flex-wrap:wrap;font-size:.78rem;color:var(--mute);margin:.1rem 0 .6rem}
.legend i{display:inline-block;width:.95rem;height:.7rem;border-radius:3px;margin-right:.3rem;vertical-align:-1px;border:2px solid}
.panel>svg{display:block;max-width:none;background:#fff;border:1px solid var(--line);border-radius:10px}
.dim{opacity:.14!important}.fx{opacity:.1!important}.node,.flowchart-link,[data-key]{transition:opacity .12s}
a{cursor:pointer}[data-key]{cursor:pointer}
#card{position:absolute;z-index:20;width:380px;max-width:92vw;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 12px 32px rgba(15,23,42,.18);padding:.9rem 1rem;display:none}
#card h2{font-size:.95rem;margin:0 1.5rem .15rem 0}#card h2 a{color:#2563eb;text-decoration:none}
#card .s{margin:.1rem 0 .55rem}#card .x{position:absolute;right:.6rem;top:.45rem;border:0;background:none;font-size:1.1rem;color:var(--mute);cursor:pointer}
.chip{display:inline-block;border-radius:999px;padding:.05rem .55rem;font-size:.74rem;margin:0 .25rem .25rem 0;background:#eef2f7;color:#334155}
.chip.tl{background:#e8f0fe;color:#1e4fa8}.chip.ext{background:#fff1e6;color:#b4440a;font-weight:600}.chip.warn{background:#fde8ef;color:#a61e4d;font-weight:600}
#card h3{font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;color:var(--mute);margin:.6rem 0 .2rem}
#card ul{margin:0;padding:0;list-style:none}#card li{padding:.1rem 0;font-size:.82rem}#card li a{color:#2563eb;text-decoration:none}
#card li.e{border-left:3px solid var(--ext);padding-left:.4rem}.mute{color:var(--mute)}
.att{max-width:980px}.att section{background:#fff;border:1px solid var(--line);border-radius:10px;padding:.7rem 1rem;margin:0 0 .8rem}
.att h2{font-size:.95rem;margin:0}.att h2 .n{background:#fde8ef;color:#a61e4d;border-radius:999px;padding:0 .5rem;font-size:.75rem;margin-left:.4rem}
.att p{margin:.15rem 0 .5rem;color:var(--mute);font-size:.82rem}.att ul{list-style:none;margin:0;padding:0}
.att li{padding:.28rem .4rem;border-radius:6px;cursor:pointer;font-size:.86rem}.att li:hover{background:#f1f5f9}.att li b{color:#1d4ed8}
.att li .t{color:#475569}.att li.e b{color:var(--ext)}.att .none{color:#15803d;font-size:.85rem}
"""

JS = r"""
(()=>{
const D=JSON.parse(document.getElementById('data').textContent),card=document.getElementById('card');
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
function el(t,c,x){const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
const PN={};let active=null;
D.panels.forEach(P=>{if(!P.svg)return;const root=$('#p-'+P.id),svg=root.querySelector(':scope>svg'),idmap=P.idmap||{},k2i={},nodes={},edges={};
 Object.entries(idmap).forEach(([i,k])=>k2i[k]=i);
 svg.querySelectorAll('g.node,[data-key]').forEach(g=>{const m=(g.id||'').match(/flowchart-(.+)-\d+$/);const k=m?idmap[m[1]]:(g.dataset&&g.dataset.key);if(k&&D.issues[k])nodes[k]=g});
 svg.querySelectorAll('path[data-edge]').forEach(p=>{if(p.dataset.edge.includes('|'))edges[p.dataset.edge]=p});
 svg.querySelectorAll('path.flowchart-link').forEach(p=>{const id=p.getAttribute('data-id')||'';P.edges.forEach(([a,b])=>{if(id.startsWith('L_'+k2i[a]+'_'+k2i[b]+'_'))edges[a+'|'+b]=p})});
 const vb=svg.viewBox.baseVal,up={},dn={};P.edges.forEach(([a,b])=>{(dn[a]=dn[a]||[]).push(b);(up[b]=up[b]||[]).push(a)});
 PN[P.id]={P,root,svg,nodes,edges,up,dn,nat:(vb&&vb.width)||1200,z:1}});
function reach(k,m){const s=new Set([k]),q=[k];while(q.length){const x=q.pop();(m[x]||[]).forEach(y=>{if(!s.has(y)){s.add(y);q.push(y)}})}return s}
function focus(pn,k){const A=reach(k,pn.up),B=reach(k,pn.dn);Object.entries(pn.nodes).forEach(([x,e])=>e.classList.toggle('dim',!(A.has(x)||B.has(x))));
 Object.entries(pn.edges).forEach(([e,p])=>{const[a,b]=e.split('|');p.classList.toggle('dim',!((A.has(a)&&A.has(b))||(B.has(a)&&B.has(b))))})}
function unfocus(pn){Object.values(pn.nodes).forEach(e=>e.classList.remove('dim'));Object.values(pn.edges).forEach(e=>e.classList.remove('dim'))}
function ref(r){const li=el('li',r.ext?'e':'');const a=el('a',null,r.k);a.href=D.base+'/browse/'+r.k;a.target='_blank';a.rel='noopener';li.append(a,' ',el('span','mute','['+r.st+'] '),document.createTextNode((r.s||'').slice(0,70)));if(r.ext)li.append(el('span','chip ext','external'));return li}
function setHash(k){const p=new URLSearchParams(location.hash.slice(1));if(active)p.set('tab',active);if(k)p.set('k',k);else p.delete('k');history.replaceState(null,'','#'+p)}
function show(k,x,y){const v=D.issues[k];if(!v)return;card.replaceChildren();const b=el('button','x','×');b.onclick=hide;card.append(b);
 const h=el('h2'),a=el('a',null,k);a.href=v.url;a.target='_blank';a.rel='noopener';h.append(a,' ↗');card.append(h,el('div','s',v.sum));
 [v.st,v.pr&&('Priority '+v.pr),(v.ws!=null&&v.ws!=='')&&('WSJF '+v.ws),v.who&&('Assignee '+v.who),v.team,v.children!=null&&(v.children+' child issue'+(v.children===1?'':'s'))].filter(Boolean).forEach(c=>card.append(el('span','chip',c)));
 (v.tl||[]).forEach(g=>card.append(el('span','chip tl',g[0]+': '+g[1].join(', '))));
 if(window.topoHas&&window.topoHas(k)){const pb=el('button','pinb',window.topoIsPinned(k)?'Unpin from Topologies':'Pin on Topologies');pb.onclick=()=>{window.topoToggle(k);hide()};card.append(pb)}
 if(v.ext_in)card.append(el('span','chip ext','◀ blocked by another project'));if(v.ext_out)card.append(el('span','chip ext','blocks another project ▶'));if(v.ext)card.append(el('span','chip ext','outside this project'));
 if(v.start||v.end)card.append(el('div','s mute','Target '+(v.start||'?')+' → '+(v.end||'?')+(v.par?(' · '+v.par+(v.pardue?' due '+v.pardue:'')):'')));
 (v.warn||[]).forEach(w=>card.append(el('span','chip warn',w)));
 const sec=(t,l)=>{if(!l.length)return;card.append(el('h3',null,t));const u=el('ul');l.forEach(r=>u.append(ref(r)));card.append(u)};
 sec('Blocked by',v.blockedBy);sec('Blocks',v.blocks);if(v.relates.length)sec('Relates to ('+v.relates.length+')',v.relates.slice(0,6));
 card.style.display='block';const w=card.offsetWidth,hh=card.offsetHeight;card.style.left=Math.max(8,Math.min(x+14,scrollX+innerWidth-w-12))+'px';card.style.top=Math.max(scrollY+8,Math.min(y+14,scrollY+innerHeight-hh-12))+'px';setHash(k)}
function hide(){card.style.display='none';setHash(null)}
Object.values(PN).forEach(pn=>Object.entries(pn.nodes).forEach(([k,g])=>{g.addEventListener('mouseenter',()=>focus(pn,k));g.addEventListener('mouseleave',()=>unfocus(pn));
 (g.closest('a')||g).addEventListener('click',e=>{if(e.metaKey||e.ctrlKey||e.shiftKey||e.button)return;e.preventDefault();e.stopPropagation();show(k,e.pageX,e.pageY)})}));
$$('.att li[data-k]').forEach(li=>li.addEventListener('click',e=>{e.stopPropagation();show(li.dataset.k,e.pageX,e.pageY)}));
document.addEventListener('click',e=>{if(!card.contains(e.target))hide()});
function zoom(pn,z){pn.z=z;pn.svg.style.width=pn.nat*z+'px';pn.svg.style.height='auto'}
function fit(pn){zoom(pn,Math.min(1,(innerWidth-48)/pn.nat))}
function tab(id){active=id;$$('.panel').forEach(p=>p.classList.toggle('on',p.id==='p-'+id));$$('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===id));$('.ctl').style.visibility=PN[id]?'visible':'hidden';setHash(null);hide()}
$$('nav button').forEach(b=>b.onclick=()=>tab(b.dataset.t));
const cur=()=>PN[active];$('#zi').onclick=()=>cur()&&zoom(cur(),Math.min(4,cur().z*1.25));$('#zo').onclick=()=>cur()&&zoom(cur(),Math.max(.15,cur().z/1.25));$('#zf').onclick=()=>cur()&&fit(cur());
const F={q:'',st:new Set(),ext:false,cons:'',prov:'',label:''};
function pk(r,p){return r.k.indexOf(p+'-')===0}
function match(k){const v=D.issues[k];if(!v)return true;if(F.st.size&&!F.st.has(v.st))return false;if(F.ext&&!(v.ext||v.ext_in||v.ext_out))return false;
 if(F.cons||F.prov||F.label){if(!v.core)return !!((F.cons&&k.indexOf(F.cons+'-')===0)||(F.prov&&k.indexOf(F.prov+'-')===0));
  if(F.cons&&!v.blocks.some(r=>r.ext&&pk(r,F.cons)))return false;if(F.prov&&!v.blockedBy.some(r=>r.ext&&pk(r,F.prov)))return false;if(F.label&&!(v.labels||[]).includes(F.label))return false}
 if(F.q){const s=(k+' '+v.sum+' '+(v.who||'')+' '+(v.team||'')).toLowerCase();if(!F.q.split(/\s+/).every(w=>s.includes(w)))return false}return true}
function applyF(){let n=0,t=0;Object.values(PN).forEach(pn=>Object.entries(pn.nodes).forEach(([k,g])=>{const m=match(k);g.classList.toggle('fx',!m)}));
 $$('.att li[data-k]').forEach(li=>{li.style.display=match(li.dataset.k)?'':'none'});
 document.dispatchEvent(new Event('pofilter'));$('#fcount').textContent=(F.q||F.st.size||F.ext||F.cons||F.prov||F.label)?Object.keys(D.issues).filter(k=>D.issues[k].core&&match(k)).length+' epics match':''}
$('#q').addEventListener('input',e=>{F.q=e.target.value.trim().toLowerCase();applyF()});
const fbar=$('#fbar');D.statuses.forEach(s=>{const b=el('button','fb',s);b.setAttribute('aria-pressed','false');b.onclick=()=>{F.st.has(s)?F.st.delete(s):F.st.add(s);b.setAttribute('aria-pressed',F.st.has(s));applyF()};fbar.append(b)});
const FS=D.facets||{};
function sel(id,label,opts,key){if(!opts||!opts.length)return;const s=el('select','fs');s.id=id;s.title=label;const o0=el('option',null,label+': all');o0.value='';s.append(o0);opts.forEach(o=>{const o1=el('option',null,o.name+' ('+o.n+')');o1.value=o.k;s.append(o1)});s.onchange=()=>{F[key]=s.value;applyF()};fbar.append(s)}
sel('fcons','Consumer: waits on us',FS.cons,'cons');sel('fprov','Provider: we wait on',FS.prov,'prov');sel('flab','Label',FS.labels,'label');
window.__pof={match:k=>match(k),F:F};
const xb=el('button','fb ext','external only');xb.setAttribute('aria-pressed','false');xb.onclick=()=>{F.ext=!F.ext;xb.setAttribute('aria-pressed',F.ext);applyF()};fbar.append(xb);
document.addEventListener('keydown',e=>{if(e.key==='Escape'){hide()}else if(e.key==='/'&&document.activeElement.id!=='q'){e.preventDefault();$('#q').focus()}});
Object.values(PN).forEach(fit);
const hp=new URLSearchParams(location.hash.slice(1));tab(hp.get('tab')&&$('#p-'+hp.get('tab'))?hp.get('tab'):D.panels[0].id);
const k0=hp.get('k');if(k0&&D.issues[k0]){const n=cur()&&cur().nodes[k0];if(n){n.scrollIntoView({block:'center',inline:'center'});const r=n.getBoundingClientRect();show(k0,r.left+scrollX+r.width/2,r.top+scrollY+r.height/2)}else show(k0,innerWidth/3,scrollY+110)}
})();
"""


def app_page(title, sub, panels, data, statuses, extra_css="", extra_js=""):
    """panels: [{id,label,badge?,svg?,html?,legend?,idmap?,edges?}]. First panel is the default tab."""
    t = re.sub("[<>&]", "", title)
    nav = "".join(f'<button data-t="{p["id"]}">{p["label"]}' + (f'<span class=n>{p["badge"]}</span>' if p.get("badge") else "") + "</button>" for p in panels)
    body = ""
    for p in panels:
        lg = "".join(f'<span><i style="{s}"></i>{x}</span>' for s, x in p.get("legend", []))
        inner = re.sub(r"^<\?xml[^>]*>\s*", "", p["svg"]) if p.get("svg") else p.get("html", "")
        body += f'<div class=panel id="p-{p["id"]}">' + (f"<div class=legend>{lg}</div>" if lg else "") + inner + "</div>"
    data = dict(data, statuses=statuses, panels=[{k: p.get(k) for k in ("id", "idmap", "edges")} | {"svg": bool(p.get("svg"))} for p in panels])
    blob = json.dumps(data).replace("</", "<\\/")
    return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{t}</title><style>{CSS}{extra_css}</style>"
            f"<header><div><h1>{t}</h1><div class=sub>{re.sub('[<>]','',sub)}</div></div><nav>{nav}</nav>"
            "<span class=ctl><button id=zo>−</button> <button id=zf>fit</button> <button id=zi>+</button></span>"
            "<div class=filters><input id=q type=search placeholder='Filter  ( / )'><span id=fbar class=filters></span><span id=fcount class=sub></span></div></header>"
            f"{body}<div id=card></div><script id=data type=application/json>{blob}</script><script>{JS}</script><script>{extra_js}</script>")
