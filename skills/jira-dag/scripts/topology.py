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
    cls = {k: list(classify(k, cfg)) for k in N}  # also for neighbours that are not drawn, so relationship filters can see them
    for k in N:
        for r in I[k].get("blocks", []) + I[k].get("blockedBy", []):
            cls.setdefault(r["k"], list(classify(r["k"], cfg)))
    spec = dict(W=W, H=H, GX=GX, GY=GY, PAD=PAD, bands=spec_bands, nodes=spec_nodes, edges=[list(e) for e in L["edges"]], height=y, cls=cls)
    return dict(svg=svg, edges=[list(e) for e in L["edges"]], layout=L, spec=spec)


CSS += ("body[data-tab=topology] .filters{display:none}"  # the drawer replaces the global filter bar on this tab
        "#p-topology g.ghost{opacity:.35}#p-topology path.ghost{opacity:.3}"
        ".tstrip{position:sticky;top:0;z-index:6;background:#fff;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:.4rem}"
        ".tbar{padding:.3rem .6rem;font-size:.82rem;display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}"
        ".tbar .pc,.tbar .fc{border-radius:999px;padding:.05rem .6rem;cursor:pointer;font-weight:600}.tbar .pc{background:#fde8ef;color:#a61e4d}"
        ".tbar .fc{background:#e8f0fe;color:#1e4fa8}.tbar .m{color:#6b7280}.tbar .cnt{color:#334155;font-weight:600}.tbar .sp{margin-left:auto}"
        ".tbar button{border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:.1rem .5rem;cursor:pointer}.tbar button.on{background:#1e4fa8;color:#fff;border-color:#1e4fa8}"
        ".tdrawer,.tlegend{display:none;position:absolute;left:0;top:100%;z-index:7;background:#fff;border:1px solid #cbd5e1;border-radius:8px;box-shadow:0 12px 32px rgba(15,23,42,.2);"
        "padding:.6rem .8rem;max-height:75vh;overflow:auto;font-size:.82rem}.tdrawer{width:26rem;max-width:94vw}.tdrawer.open,.tlegend.open{display:block}"
        ".tlegend{left:auto;right:0;margin-top:.2rem}.tlegend .legend{margin:0;flex-direction:column;gap:.35rem}"
        ".tdrawer fieldset{border:1px solid #e5e7eb;border-radius:6px;margin:0 0 .5rem;padding:.3rem .5rem}.tdrawer legend{font-weight:700;font-size:.75rem;color:#475569;padding:0 .3rem}"
        ".tdrawer .opts{max-height:9rem;overflow:auto;display:flex;flex-direction:column}.tdrawer .opt{white-space:nowrap}.tdrawer .n{color:#6b7280}"
        ".tdrawer .hint{color:#6b7280;font-style:italic}.tdrawer .row{display:flex;gap:.3rem;flex-wrap:wrap}.tdrawer input[type=range]{width:100%}"
        ".tdrawer .dd{display:flex;justify-content:space-between;color:#475569}.tdrawer .x{float:right;border:0;background:none;font-size:1.1rem;cursor:pointer;color:#6b7280}"
        ".pinb{margin:.5rem 0 0;border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:.15rem .6rem;cursor:pointer;font-size:.8rem}")

JS_BODY = r"""
(()=>{
const T=%SPEC%;const root=document.getElementById('p-topology');if(!root)return;
const VS=window.ViewState,D=JSON.parse(document.getElementById('data').textContent),I=D.issues||{};
const svg=root.querySelector(':scope>svg'),W=T.W,H=T.H,GX=T.GX,GY=T.GY,PAD=T.PAD,N=T.nodes;
const el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e};
const box={},edge={};svg.querySelectorAll('g.tn').forEach(g=>box[g.dataset.key]=g);svg.querySelectorAll('path[data-edge]').forEach(p=>edge[p.dataset.edge]=p);
const keys=Object.keys(N),iss={};keys.forEach(k=>iss[k]=I[k]||{key:k});
const FAC=VS.facets(iss,keys);
// One state object {filters,pins,depth} drives layout(); hover is transient and lives only in the .dim class.
let state=VS.fromHash(location.hash),R=null,open=false,legOpen=false;
state.pins=state.pins.filter(k=>N[k]);if(!state.pins.length)state.depth='direct';
const edgeD=(pa,pb)=>{const[ax,ay]=pa,[bx,by]=pb,f=ax+W<=bx;let sx,sy,tx,ty;
 if(f){sx=ax+W;sy=ay+H/2;tx=bx;ty=by+H/2}else if(ay<by){sx=ax+W/2;sy=ay+H;tx=bx+W/2;ty=by}else{sx=ax+W/2;sy=ay;tx=bx+W/2;ty=by+H}
 const m=f?(sx+tx)/2:sx;return `M${sx},${sy} C${m},${sy} ${m},${ty} ${tx},${ty}`};
const bandEls={};T.bands.forEach(b=>bandEls[b.id]=[...svg.querySelectorAll('[data-band="'+b.id+'"]')]);
const bandKeys={};Object.entries(N).forEach(([k,n])=>{(bandKeys[n.band]=bandKeys[n.band]||[]).push(k)});
Object.values(bandKeys).forEach(a=>a.sort((x,y)=>N[x].o-N[y].o));
function clearDim(){svg.querySelectorAll('.dim').forEach(e=>e.classList.remove('dim'))}
svg.addEventListener('mouseleave',clearDim);
function layout(){clearDim();R=VS.classify({issues:iss,nodes:keys,edges:T.edges,state,cls:T.cls});const P={};let y=PAD;
 T.bands.forEach(b=>{const ks=(bandKeys[b.id]||[]).filter(k=>R.nodes[k]!=='hidden');let h;
  const hide=R.active&&b.type==='flow'&&!ks.length;
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
 Object.entries(box).forEach(([k,g])=>{const p=P[k];g.style.display=p?'':'none';g.classList.toggle('ghost',R.nodes[k]==='ghost');if(p)g.setAttribute('transform','translate('+(p[0]-N[k].x)+','+(p[1]-N[k].y)+')')});
 Object.entries(edge).forEach(([e,p])=>{const[a,b]=e.split('|');const ok=P[a]&&P[b]&&R.edges[e]!=='hidden';p.style.display=ok?'':'none';p.classList.toggle('ghost',ok&&R.edges[e]==='ghost');if(ok)p.setAttribute('d',edgeD(P[a],P[b]))});
 svg.setAttribute('height',y);const vb=svg.getAttribute('viewBox').split(' ');svg.setAttribute('viewBox',vb[0]+' '+vb[1]+' '+vb[2]+' '+y);
 renderBar();syncDrawer()}
// ---- strip: chip row, filter drawer, legend popover
const strip=el('div','tstrip'),barEl=el('div','tbar'),drawer=el('div','tdrawer'),pop=el('div','tlegend');
strip.append(barEl,drawer,pop);root.insertBefore(strip,root.firstChild);
const lg=root.querySelector(':scope>.legend');if(lg)pop.append(lg);
const stick=()=>{const h=document.querySelector('header');strip.style.top=(h?h.offsetHeight:0)+'px'};stick();addEventListener('resize',stick);
const LIST={label:'labels',component:'components',status:'status',rel:'rel'},RELN={incoming:'Incoming',external:'External',blocking:'Blocking others'};
const F=()=>state.filters;
function sync(){const p=new URLSearchParams(location.hash.slice(1));VS.STATE_KEYS.forEach(k=>p.delete(k));new URLSearchParams(VS.toHash(state)).forEach((v,k)=>p.set(k,v));history.replaceState(null,'','#'+p)}
function commit(){if(!state.pins.length)state.depth='direct';sync();layout()}
function toggleIn(kind,v){const a=F()[LIST[kind]],i=a.indexOf(v);if(i<0)a.push(v);else a.splice(i,1);commit()}
function toggle(k){if(!N[k])return;const i=state.pins.indexOf(k);if(i<0)state.pins.push(k);else state.pins.splice(i,1);commit()}
const resetDates=()=>{F().dates={from:null,to:null,undated:true}};
const chip=(c,x,t,fn)=>{const e=el('span',c,x);e.title=t;e.onclick=fn;return e};
const btn=(x,fn,c)=>{const b=el('button',c||'',x);b.onclick=fn;return b};
function renderBar(){barEl.replaceChildren();const f=F(),nf=VS.activeCount(f);
 const fb=btn('Filters ('+nf+')',()=>{open=!open;legOpen=false;showPanels()},'fbtn');fb.setAttribute('aria-expanded',open);barEl.append(fb);
 f.labels.forEach(l=>barEl.append(chip('fc',l+' ✕','Remove filter',()=>toggleIn('label',l))));
 f.components.forEach(l=>barEl.append(chip('fc',l+' ✕','Remove filter',()=>toggleIn('component',l))));
 f.status.forEach(l=>barEl.append(chip('fc',l+' ✕','Remove filter',()=>toggleIn('status',l))));
 f.rel.forEach(l=>barEl.append(chip('fc',RELN[l]+' ✕','Remove filter',()=>toggleIn('rel',l))));
 if(VS.datesActive(f.dates))barEl.append(chip('fc','Target '+(f.dates.from||'…')+' → '+(f.dates.to||'…')+(f.dates.undated?'':' · no undated')+' ✕','Remove filter',()=>{resetDates();commit()}));
 if(state.pins.length){barEl.append(el('span','m','Pinned:'));state.pins.forEach(k=>barEl.append(chip('pc',k+' ✕','Unpin',()=>toggle(k))));
  ['direct','full'].forEach(m=>barEl.append(btn(m==='direct'?'Direct':'Full chain',()=>{state.depth=m;commit()},state.depth===m?'on':'')));
  if(nf)barEl.append(el('span','m','(filters paused while pinned)'))}
 if(R.active){const sh=keys.filter(k=>R.nodes[k]==='shown').length,gh=keys.filter(k=>R.nodes[k]==='ghost').length;
  barEl.append(el('span','cnt',sh+' epics shown of '+keys.length+(gh?' (+'+gh+' faded)':'')))}
 if(state.pins.length)barEl.append(btn('Unpin all',()=>{state.pins=[];commit()}));
 if(nf)barEl.append(btn('Clear filters',()=>{state.filters=VS.emptyState().filters;commit()}));
 if(!state.pins.length&&!nf)barEl.append(el('span','m','Shift-click an epic, or use Pin on its card, to focus on it. Pin several to compare. Esc clears.'));
 const q=btn('?',()=>{legOpen=!legOpen;open=false;showPanels()},'sp');q.title='Legend';q.setAttribute('aria-expanded',legOpen);barEl.append(q)}
function showPanels(){drawer.classList.toggle('open',open);pop.classList.toggle('open',legOpen);renderBar()}
const sect=(title,id)=>{const s=el('fieldset','tsec');s.dataset.section=id;s.append(el('legend',null,title));drawer.append(s);return s};
function check(parent,kind,value,text,n){const l=el('label','opt'),c=document.createElement('input');c.type='checkbox';c.dataset.kind=kind;c.value=value;c.onchange=()=>toggleIn(kind,value);
 l.append(c,' '+text+' ',el('span','n','('+n+')'));parent.append(l)}
function pill(parent,kind,value,text,n){const b=el('button','fb',text+(n!=null?' ('+n+')':''));b.dataset.kind=kind;b.dataset.value=value;b.setAttribute('aria-pressed','false');b.onclick=()=>toggleIn(kind,value);parent.append(b)}
const dn=s=>Date.parse(s+'T00:00:00Z')/864e5,ds=n=>new Date(n*864e5).toISOString().slice(0,10);
let dmin=0,span=0;const dr={};
(function buildDrawer(){
 const x=btn('✕',()=>{open=false;showPanels()},'x');x.title='Close';drawer.append(x);
 const labs=sect('Labels','labels');
 if(!FAC.labelGroups.length)labs.append(el('span','hint','No labels on these epics'));
 FAC.labelGroups.forEach(g=>{const gd=el('div');gd.dataset.group=g.prefix;gd.append(el('div','m',g.title+(g.prefix==='other'?'':' ('+g.prefix+')')));const o=el('div','opts');
  g.values.forEach(v=>check(o,'label',v.label,v.label,v.n));gd.append(o);labs.append(gd)});
 const comps=sect('Components','components');
 if(FAC.components.length){const o=el('div','opts');FAC.components.forEach(c=>check(o,'component',c.name,c.name,c.n));comps.append(o)}
 else{comps.disabled=true;comps.setAttribute('aria-disabled','true');comps.append(el('span','hint','No epic here has a component yet'))}
 const st=sect('Status','status'),sr=el('div','row');FAC.statuses.forEach(s=>pill(sr,'status',s.name,s.name,s.n));st.append(sr);
 const rl=sect('Relationships','rel'),rr=el('div','row');VS.REL.forEach(r=>pill(rr,'rel',r,RELN[r]));rl.append(rr);
 const dt=sect('Target dates','dates');
 if(!FAC.dates.min){dt.disabled=true;dt.setAttribute('aria-disabled','true');dt.append(el('span','hint','No target dates on these epics'))}
 else{dmin=dn(FAC.dates.min);span=dn(FAC.dates.max)-dmin;
  const mk=(id)=>{const r=document.createElement('input');r.type='range';r.min=0;r.max=span;r.step=1;r.value=id==='from'?0:span;r.setAttribute('list','tdates');r.setAttribute('aria-label','Target '+id);dr[id]=r;return r};
  const dl=document.createElement('datalist');dl.id='tdates';
  for(let d=new Date(FAC.dates.min.slice(0,7)+'-01T00:00:00Z');d<=new Date(FAC.dates.max+'T00:00:00Z');d.setUTCMonth(d.getUTCMonth()+1)){const n=d.getTime()/864e5-dmin;if(n>=0&&n<=span){const o=document.createElement('option');o.value=n;dl.append(o)}}
  dr.out=el('div','dd');dr.und=document.createElement('input');dr.und.type='checkbox';dr.und.value='undated';dr.und.checked=true;
  const ul=el('label','opt');ul.append(dr.und,' Undated');
  dt.append(mk('from'),mk('to'),dl,dr.out,ul);
  const set=(a,b)=>{const d=F().dates;d.from=a<=0?null:ds(dmin+a);d.to=b>=span?null:ds(dmin+b);commit()};
  dr.from.oninput=()=>{let a=+dr.from.value,b=+dr.to.value;if(a>b){b=a;dr.to.value=b}set(a,b)};
  dr.to.oninput=()=>{let a=+dr.from.value,b=+dr.to.value;if(b<a){a=b;dr.from.value=a}set(a,b)};
  dr.und.onchange=()=>{F().dates.undated=dr.und.checked;commit()}}
})();
function syncDrawer(){const f=F();
 drawer.querySelectorAll('input[data-kind]').forEach(c=>{c.checked=f[LIST[c.dataset.kind]].includes(c.value)});
 drawer.querySelectorAll('button[data-kind]').forEach(b=>b.setAttribute('aria-pressed',f[LIST[b.dataset.kind]].includes(b.dataset.value)));
 if(dr.from){const c=v=>Math.max(0,Math.min(span,v));dr.from.value=f.dates.from?c(dn(f.dates.from)-dmin):0;dr.to.value=f.dates.to?c(dn(f.dates.to)-dmin):span;dr.und.checked=f.dates.undated!==false;
  dr.out.replaceChildren(el('span',null,f.dates.from||FAC.dates.min),el('span',null,f.dates.to||FAC.dates.max))}}
window.topoHas=k=>!!N[k];window.topoIsPinned=k=>state.pins.includes(k);window.topoToggle=toggle;
window.topoPin=(ks,d)=>{state.pins=ks.filter(k=>N[k]);if(d)state.depth=d;commit()};
Object.entries(box).forEach(([k,g])=>g.addEventListener('click',e=>{if(e.shiftKey){e.preventDefault();e.stopPropagation();toggle(k)}},true));
addEventListener('keydown',e=>{if(e.key!=='Escape'||!root.offsetParent)return;
 if(open||legOpen){open=legOpen=false;showPanels()}else if(state.pins.length){state.pins=[];commit()}});
layout();
})();
"""


def js(r):
    """Client script: view state (filters, pins, depth) and the Topologies renderer. r is the dict from render()."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewstate.js")) as f:
        viewstate = f.read()
    return viewstate + "\n" + JS_BODY.replace("%SPEC%", json.dumps(r["spec"]).replace("</", "<\\/"))
