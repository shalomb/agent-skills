"""Topologies tab: Team Topologies view of an ART from a config blob (read-only, no Jira calls here).

Config (JSON or YAML): {art, pods:[{id,name?,projects:[..]}], interface:{name?,projects:[..]}, products:[{id,name?,projects:[..]}]}.
Anything whose project is not in the config is external.
Optional `policy: {<pod id>: {slice_cap_days: N}}` sets the per-POD slice cap read by rules.py (not used for drawing).
Bands, top to bottom: On the platform (products) · interface (requests from products; spans every POD) ·
In the platform (one lane per POD, incoming-from-another-POD on the left, dotted lane borders) · External (outgoing, under the ART).
External incoming sits in a left gutter. Only nodes on a cross-boundary edge are drawn; same-POD edges are counted per lane.
"""
import html, json, os, re, subprocess, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jira_common import critical_path, edges_of

W, H, GX, GY, PAD = 250, 80, 18, 14, 14
GUTTER = 230
LEGEND = [("background:#e8f0fe;border:1px solid #5b7fd1", "POD epic"), ("background:#fff4d6;border:1px solid #c9a227", "Early (Funnel, Backlog, Analyzing)"),
          ("background:#e6f4ea;border:1px solid #4a9d5b", "In progress"), ("border-top:2px dotted #888;height:0;margin-top:8px", "POD boundary")]
CSS = "#p-topology path.dim{opacity:0!important}#p-topology path{transition:opacity .12s}"
EARLY = {"Funnel", "Backlog", "New", "To Do", "Analyzing"}


def load_config(path):
    path = os.path.expanduser(path)
    if path.endswith(".json"):
        return json.load(open(path))
    try:
        import yaml
        return yaml.safe_load(open(path))
    except ImportError:
        return json.loads(subprocess.check_output(["yq", "-o=json", ".", path]))


def default_config_path():
    for n in ("topology.yaml", "topology.yml", "topology.json"):
        p = os.path.expanduser("~/.config/jira-dag/" + n)
        if os.path.exists(p):
            return p


def _groups(cfg):
    yield from (("pod", p) for p in cfg.get("pods", []))
    if cfg.get("interface"):
        yield "interface", dict(cfg["interface"], id=cfg["interface"].get("id", "interface"))
    yield from (("product", p) for p in cfg.get("products", []))


def all_projects(cfg):
    return [pr for _, g in _groups(cfg) for pr in g.get("projects", [])]


DEFAULT_LABEL_GROUPS = [{"prefix": "kind-", "title": "Work kind"}, {"prefix": "for-", "title": "Serves"},
                        {"prefix": "pod-", "title": "POD"}, {"prefix": "cap-", "title": "Capability"},
                        {"label": "blocked-external", "title": "Flag"}]


def card_groups(labels, cfg):
    """Topology-relevant labels for an epic card, as [(title, [values])]. A group matches by `prefix` (stripped) or exact `label`."""
    out = {}
    for g in (cfg or {}).get("label_groups", DEFAULT_LABEL_GROUPS):
        for l in labels or []:
            if "prefix" in g and l.startswith(g["prefix"]):
                out.setdefault(g["title"], []).append(l[len(g["prefix"]):])
            elif g.get("label") == l:
                out.setdefault(g["title"], []).append(l)
    return list(out.items())


def classify(key, cfg):
    pj = key.rsplit("-", 1)[0]
    for kind, g in _groups(cfg):
        if pj in g.get("projects", []):
            return kind, g["id"]
    return "external", pj


def layout(I, cfg):
    E = []
    for k, v in I.items():
        for r in v.get("blocks", []):
            if r["k"] in I:
                E.append((k, r["k"]))
        for r in v.get("blockedBy", []):
            if r["k"] in I:
                E.append((r["k"], k))
    E = sorted(set(E))
    cl = {k: classify(k, cfg) for k in I}
    intra = {p["id"]: 0 for p in cfg.get("pods", [])}
    drawn = []
    for a, b in E:
        if cl[a] == cl[b]:
            if cl[a][0] == "pod":
                intra[cl[a][1]] += 1
            continue
        if cl[a][0] == "external" and cl[b][0] == "external":
            continue
        drawn.append((a, b))
    nodes = {}
    for a, b in drawn:
        for k in (a, b):
            kind, gid = cl[k]
            n = nodes.setdefault(k, dict(zone={"pod": "pod", "interface": "interface", "product": "product"}.get(kind), group=gid, side="right"))
            if kind == "external":
                n["zone"] = "ext_out"
    for a, b in drawn:  # external that feeds a POD or product, rather than being fed
        if cl[a][0] == "external":
            nodes[a]["zone"] = "ext_in"
        if cl[b][0] == "pod" and cl[a][0] in ("pod", "external") :
            nodes[b]["side"] = "left"
    return dict(nodes=nodes, edges=drawn, intra=intra, cl=cl)


STATUS_FILL = {"Implementing": ("#d6f0df", "#168a4b"), "In Progress": ("#d6f0df", "#168a4b"), "Analyzing": ("#fff1b8", "#c99700"),
               "Backlog": ("#e6edf7", "#51657f"), "Funnel": ("#f3f4f6", "#9ca3af")}


def _fill(st):
    return STATUS_FILL.get(st, ("#ffffff", "#9ca3af"))


def edge_d(pa, pb):
    """Cubic from the right of A to the left of B when B is to the right, else from the bottom/top. Mirrored in JS (JS below)."""
    (ax, ay), (bx, by) = pa, pb
    fwd = ax + W <= bx
    sx, sy, tx, ty = (ax + W, ay + H / 2, bx, by + H / 2) if fwd else (ax + W / 2, ay + H, bx + W / 2, by) if ay < by else (ax + W / 2, ay, bx + W / 2, by + H)
    m = (sx + tx) / 2 if fwd else sx
    return f"M{sx},{sy} C{m},{sy} {m},{ty} {tx},{ty}"


def render(I, cfg):
    L = layout(I, cfg)
    E_all = edges_of(I)
    path, _ = critical_path(E_all)
    down = {}
    for a_, b_ in E_all:
        down.setdefault(a_, set()).add(b_)

    def blocks_n(k):
        seen, q = set(), [k]
        while q:
            for m in down.get(q.pop(), ()):
                if m not in seen:
                    seen.add(m); q.append(m)
        return len(seen)
    N, pods = L["nodes"], cfg.get("pods", [])
    esc = html.escape
    Z = lambda z: sorted((k for k, n in N.items() if n["zone"] == z), key=lambda k: (I[k].get("ws") is None, -(I[k].get("ws") or 0), k))
    laneW = 2 * W + 3 * GX
    x0 = GUTTER if Z("ext_in") else PAD
    width = x0 + laneW * max(1, len(pods)) + PAD
    pos, out, y = {}, [], PAD
    spec_nodes, spec_bands = {}, []

    def box(k, x, yy, band, col=None, o=0):
        spec_nodes[k] = dict(band=band, col=col, o=o, x=x, y=yy)
        v, n = I[k], N[k]
        fill, stroke = _fill(v["st"])
        ext_node = n["zone"] in ("ext_in", "ext_out")
        ring = ext_node or any(classify(r["k"], cfg)[0] == "external" for r in v.get("blocks", []) + v.get("blockedBy", []))
        flag = ""
        if not ext_node:
            fin = any(classify(r["k"], cfg)[0] == "external" for r in v.get("blockedBy", []))
            fout = any(classify(r["k"], cfg)[0] == "external" for r in v.get("blocks", []))
            flag = "◀▶ EXTERNAL IN+OUT" if fin and fout else "◀ EXTERNAL IN" if fin else "EXTERNAL OUT ▶" if fout else ""
        if ext_node:
            fill, stroke = "#fff4e6", "#e8590c"
        nb = blocks_n(k)
        meta = " · ".join(x_ for x_ in [v["st"], f"WSJF {v['ws']}" if v.get("ws") not in (None, "") else "", f"blocks {nb}" if nb else ""] if x_)
        lines = textwrap.wrap(v["sum"][:56], 34)[:2]
        dash = ' stroke-dasharray="6 4"' if ext_node else ' stroke-dasharray="3 3"' if not v.get("core") else ""
        t = lambda dy, txt, extra="": f'<text x={x + 8} y={yy + dy} {extra if 'font-size' in extra else 'font-size=11 ' + extra}>{esc(txt)}</text>'
        body = t(15, ("★ " if k in path else "") + k, "font-weight=700") + "".join(t(29 + 12 * i, ln) for i, ln in enumerate(lines))
        body += t(57, meta, 'fill="#475569" font-size=10') + (t(70, flag, 'fill="#b4440a" font-weight=700 font-size=10') if flag else "")
        pos[k] = (x, yy)
        out.append(f'<g data-key="{esc(k)}" class=tn><rect x={x} y={yy} width={W} height={H} rx=6 fill="{fill}" stroke="{"#d6336c" if k in path else "#e8590c" if ring else stroke}" '
                   f'stroke-width={4 if k in path else 3 if ring else 2}{dash}/>{body}</g>')
    def band(bid, title, yy, hh, extra="", type_="flow", cols=None):
        spec_bands.append(dict(id=bid, type=type_, top=yy, h=hh, x0=x0, availX=width - PAD, cols=cols or {}))
        out.append(f'<rect class=bf data-band={bid} x=4 y={yy} width={width - 8} height={hh} fill="#fafafa" stroke="#ddd" rx=6/>'
                   f'<text data-band={bid} x=12 y={yy + 15} font-size=12 font-weight=700 fill="#555">{esc(title)}{extra}</text>')

    def flow(ks, x, yy, avail, bid):  # place boxes left-to-right, wrapping; return height used
        per = max(1, (avail - x) // (W + GX)); rows = (len(ks) + per - 1) // per
        for i, k in enumerate(ks):
            box(k, x + (i % per) * (W + GX), yy + (i // per) * (H + GY), bid, None, i)
        return max(1, rows) * (H + GY)
    prods, ifc = Z("product"), Z("interface")
    hh = 24 + (flow(prods, x0, y + 24, width - PAD, "product") if prods else 24)
    band("product", "On the platform · products (stream-aligned)", y, hh, "" if prods else " — no product data yet")
    y += hh + GY
    if ifc or cfg.get("interface"):
        iname = (cfg.get("interface") or {}).get("name", "Interface") + " · product requests, commitments across all PODs"
        hh = 24 + (flow(ifc, x0, y + 24, width - PAD, "interface") if ifc else 24)
        band("interface", iname, y, hh, "" if ifc else " — nothing linked"); y += hh + GY
    ly = y
    rows = {}
    for z in range(len(pods)):
        pid = pods[z]["id"]
        for side in ("left", "right"):
            ks = [k for k in Z("pod") if N[k]["group"] == pid and N[k]["side"] == side]
            rows[pid, side] = ks
    nrows = max([len(v) for v in rows.values()] + [len(Z("ext_in")), 1])
    lh = 40 + nrows * (H + GY)
    colx = {"ext_in": PAD}
    for i, p in enumerate(pods):
        for j, side in enumerate(("left", "right")):
            colx[f"{p['id']}|{side}"] = x0 + i * laneW + GX + j * (W + GX)
    band("lanes", "In the platform · " + cfg.get("art", "ART"), ly, lh, type_="cols", cols=colx)
    for i, p in enumerate(pods):
        lx = x0 + i * laneW
        if i:
            out.append(f'<line class=sep data-band=lanes x1={lx - 6} y1={ly + 4} x2={lx - 6} y2={ly + lh - 4} stroke="#888" stroke-dasharray="3 5"/>')
        n_in = L["intra"].get(p["id"], 0)
        out.append(f'<text data-band=lanes x={lx + 8} y={ly + 34} font-size=12 font-weight=700>{esc(p.get("name", p["id"]))}</text><text data-band=lanes x={lx + laneW - 14} y={ly + 34} font-size=9 text-anchor=end fill="#888">{n_in} same-POD links not drawn</text>')
        for j, side in enumerate(("left", "right")):
            for r, k in enumerate(rows[p["id"], side]):
                box(k, lx + GX + j * (W + GX), ly + 42 + r * (H + GY), "lanes", f"{p['id']}|{side}", r)
    out.append(f'<text class=bh data-band=lanes x={x0 + 10} y={ly + lh - 4} font-size=9 fill="#888">left: waits on another POD or outside · right: provides / no incoming</text>')
    exin = Z("ext_in")
    if exin:
        out.append(f'<text data-band=lanes x=12 y={ly + 34} font-size=12 font-weight=700>External incoming</text>')
        for r, k in enumerate(exin):
            box(k, PAD, ly + 42 + r * (H + GY), "lanes", "ext_in", r)
    y = ly + lh + GY
    exo = Z("ext_out")
    hh = 24 + (flow(exo, x0, y + 24, width - PAD, "ext_out") if exo else 24)
    band("ext_out", "External · other ARTs and platforms (outgoing)", y, hh, "" if exo else " — nothing linked")
    y += hh + PAD
    # paint boxes after bands: bands were appended first only for their own frame, boxes appended before later bands. Reorder: frames first.
    frames = [o for o in out if not o.startswith("<g data-key")]
    boxes = [o for o in out if o.startswith("<g data-key")]
    paths = []
    for a, b in L["edges"]:
        paths.append(f'<path d="{edge_d(pos[a], pos[b])}" fill=none stroke="#7a7a7a" stroke-width=1.3 marker-end="url(#ar)" data-edge="{esc(a)}|{esc(b)}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width={width} height={y} viewBox="0 0 {width} {y}" font-family="system-ui,sans-serif">'
           '<defs><marker id=ar viewBox="0 0 8 8" refX=7 refY=4 markerWidth=7 markerHeight=7 orient=auto><path d="M0,0 L8,4 L0,8 z" fill="#7a7a7a"/></marker></defs>'
           + "".join(frames) + "".join(paths) + "".join(boxes) + "</svg>")
    svg = re.sub(r'(\s[\w:-]+)=([^\s"<>/]+)', r'\1="\2"', svg)  # quote bare attributes: valid standalone XML
    spec = dict(W=W, H=H, GX=GX, GY=GY, PAD=PAD, bands=spec_bands, nodes=spec_nodes, edges=[list(e) for e in L["edges"]], height=y)
    return dict(svg=svg, edges=[list(e) for e in L["edges"]], layout=L, spec=spec)


CSS += (".tbar{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid #e5e7eb;padding:.4rem .8rem;font-size:.82rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}"
        ".tbar .pc{background:#fde8ef;color:#a61e4d;border-radius:999px;padding:.05rem .6rem;cursor:pointer;font-weight:600}.tbar .m{color:#6b7280}"
        ".tbar button{border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:.1rem .5rem;cursor:pointer}.tbar button.on{background:#1e4fa8;color:#fff;border-color:#1e4fa8}"
        ".pinb{margin:.5rem 0 0;border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:.15rem .6rem;cursor:pointer;font-size:.8rem}")

JS_BODY = r"""
(()=>{
const T=%SPEC%;const root=document.getElementById('p-topology');if(!root)return;
const svg=root.querySelector(':scope>svg'),W=T.W,H=T.H,GX=T.GX,GY=T.GY,PAD=T.PAD,N=T.nodes;
const box={},edge={};svg.querySelectorAll('g.tn').forEach(g=>box[g.dataset.key]=g);svg.querySelectorAll('path[data-edge]').forEach(p=>edge[p.dataset.edge]=p);
const up={},dn={};T.edges.forEach(([a,b])=>{(dn[a]=dn[a]||[]).push(b);(up[b]=up[b]||[]).push(a)});
const reach=(k,m)=>{const s=new Set([k]),q=[k];while(q.length){const x=q.pop();(m[x]||[]).forEach(y=>{if(!s.has(y)){s.add(y);q.push(y)}})}return s};
let pins=[],depth='direct';
const edgeD=(pa,pb)=>{const[ax,ay]=pa,[bx,by]=pb,f=ax+W<=bx;let sx,sy,tx,ty;
 if(f){sx=ax+W;sy=ay+H/2;tx=bx;ty=by+H/2}else if(ay<by){sx=ax+W/2;sy=ay+H;tx=bx+W/2;ty=by}else{sx=ax+W/2;sy=ay;tx=bx+W/2;ty=by+H}
 const m=f?(sx+tx)/2:sx;return `M${sx},${sy} C${m},${sy} ${m},${ty} ${tx},${ty}`};
const bandEls={};T.bands.forEach(b=>bandEls[b.id]=[...svg.querySelectorAll('[data-band="'+b.id+'"]')]);
const bandKeys={};Object.entries(N).forEach(([k,n])=>{(bandKeys[n.band]=bandKeys[n.band]||[]).push(k)});
Object.values(bandKeys).forEach(a=>a.sort((x,y)=>N[x].o-N[y].o));
function compute(){if(!pins.length)return{vis:null,E:null};const vis=new Set(),E=new Set();
 pins.filter(p=>N[p]).forEach(p=>{vis.add(p);
  if(depth==='direct'){(dn[p]||[]).forEach(b=>{vis.add(b);E.add(p+'|'+b)});(up[p]||[]).forEach(a=>{vis.add(a);E.add(a+'|'+p)})}
  else{const A=reach(p,up),B=reach(p,dn);A.forEach(x=>vis.add(x));B.forEach(x=>vis.add(x));T.edges.forEach(([a,b])=>{if((A.has(a)&&A.has(b))||(B.has(a)&&B.has(b)))E.add(a+'|'+b)})}});
 return{vis,E}}
function clearDim(){svg.querySelectorAll('.dim').forEach(e=>e.classList.remove('dim'))}
svg.addEventListener('mouseleave',clearDim);
function layout(){clearDim();const{vis,E}=compute(),P={};let y=PAD;
 T.bands.forEach(b=>{const ks=(bandKeys[b.id]||[]).filter(k=>!vis||vis.has(k));let h;
  const hide=vis&&b.type==='flow'&&!ks.length;
  if(b.type==='flow'){const per=Math.max(1,Math.floor((b.availX-b.x0)/(W+GX)));ks.forEach((k,i)=>{P[k]=[b.x0+(i%per)*(W+GX),y+24+Math.floor(i/per)*(H+GY)]});
   h=24+(ks.length?Math.ceil(ks.length/per)*(H+GY):24)}
  else{const cols={};ks.forEach(k=>{(cols[N[k].col]=cols[N[k].col]||[]).push(k)});const rows=Math.max(1,...Object.values(cols).map(a=>a.length));
   Object.entries(cols).forEach(([c,a])=>a.forEach((k,r)=>{P[k]=[b.cols[c],y+42+r*(H+GY)]}));h=40+rows*(H+GY)}
  if(hide)h=-GY;
  const dy=y-b.top,dh=h-b.h;bandEls[b.id].forEach(e=>{e.style.display=hide?'none':'';
   if(e.classList.contains('bf')){e.setAttribute('height',Math.max(h,0));e.setAttribute('transform','translate(0,'+dy+')')}
   else if(e.classList.contains('sep')){e.dataset.y2=e.dataset.y2||e.getAttribute('y2');e.setAttribute('y2',+e.dataset.y2+dh);e.setAttribute('transform','translate(0,'+dy+')')}
   else if(e.classList.contains('bh'))e.setAttribute('transform','translate(0,'+(dy+dh)+')');
   else e.setAttribute('transform','translate(0,'+dy+')')});
  y+=h+GY});
 y+=PAD-GY;
 Object.entries(box).forEach(([k,g])=>{const p=P[k];g.style.display=p?'':'none';if(p)g.setAttribute('transform','translate('+(p[0]-N[k].x)+','+(p[1]-N[k].y)+')')});
 Object.entries(edge).forEach(([e,p])=>{const[a,b]=e.split('|');const ok=P[a]&&P[b]&&(!E||E.has(e));p.style.display=ok?'':'none';if(ok)p.setAttribute('d',edgeD(P[a],P[b]))});
 svg.setAttribute('height',y);const vb=svg.getAttribute('viewBox').split(' ');svg.setAttribute('viewBox',vb[0]+' '+vb[1]+' '+vb[2]+' '+y);
 bar()}
const bar=(()=>{const d=document.createElement('div');d.className='tbar';const lg=root.querySelector('.legend');(lg?lg.nextSibling:root.firstChild)?root.insertBefore(d,lg?lg.nextSibling:root.firstChild):root.append(d);
 return()=>{d.replaceChildren();const t=(c,x)=>{const e=document.createElement('span');e.className=c;e.textContent=x;return e};
  if(!pins.length){d.append(t('m','Shift-click an epic, or use Pin on its card, to focus on it. Pin several to compare. Esc clears.'));return}
  d.append(t('m','Pinned:'));pins.forEach(k=>{const c=t('pc',k+' ✕');c.title='Unpin';c.onclick=()=>toggle(k);d.append(c)});
  ['direct','full'].forEach(m=>{const b=document.createElement('button');b.textContent=m==='direct'?'Direct':'Full chain';b.className=depth===m?'on':'';b.onclick=()=>{depth=m;sync();layout()};d.append(b)});
  const n=Object.values(box).filter(g=>g.style.display!=='none').length;d.append(t('m',n+' epics shown'));
  const u=document.createElement('button');u.textContent='Unpin all';u.onclick=()=>{pins=[];sync();layout()};d.append(u)}})();
function sync(){const p=new URLSearchParams(location.hash.slice(1));if(pins.length)p.set('pin',pins.join(','));else p.delete('pin');if(pins.length&&depth==='full')p.set('depth','full');else p.delete('depth');history.replaceState(null,'','#'+p)}
function toggle(k){if(!N[k])return;const i=pins.indexOf(k);if(i<0)pins.push(k);else pins.splice(i,1);sync();layout()}
window.topoHas=k=>!!N[k];window.topoIsPinned=k=>pins.includes(k);window.topoToggle=toggle;
window.topoPin=(ks,d)=>{pins=ks.filter(k=>N[k]);depth=d||depth;sync();layout()};
Object.entries(box).forEach(([k,g])=>g.addEventListener('click',e=>{if(e.shiftKey){e.preventDefault();e.stopPropagation();toggle(k)}},true));
addEventListener('keydown',e=>{if(e.key==='Escape'&&pins.length&&document.getElementById('p-topology').offsetParent){pins=[];sync();layout()}});
const h0=new URLSearchParams(location.hash.slice(1));if(h0.get('depth')==='full')depth='full';pins=(h0.get('pin')||'').split(',').filter(k=>N[k]);layout();
})();
"""


def js(r):
    """Client script: pin one or more epics and show only how they relate (relayout in the browser). r is the dict from render()."""
    return JS_BODY.replace("%SPEC%", json.dumps(r["spec"]).replace("</", "<\\/"))
