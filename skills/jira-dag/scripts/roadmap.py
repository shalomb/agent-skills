"""Stakeholder roadmap panel: forecast from blockers, derived confidence, local what-if. Browser-only; no Jira writes."""

BRIEF = '<div id=bf><div id=bfbar></div><div id=bfhost></div></div>'

PANEL = ('<div id=rm><div id=rmbar></div><div id=rmhost></div></div>'
         '<div id=wi></div><div id=chg></div><div id=exp><div><h3>Proposed changes (not applied to Jira)</h3><textarea id=expt readonly></textarea>'
         '<p><button id=expcopy>Copy</button> <button id=expclose>Close</button></p></div></div>')

CSS = """
#rm{max-width:1500px}#rmbar{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;margin:.1rem 0 .7rem}
#rmbar .note{background:#eefbf3;border:1px solid #b7e4c7;color:#1b5e3a;border-radius:8px;padding:.2rem .6rem;font-size:.78rem}
#rmbar label{font-size:.82rem;color:#475569;cursor:pointer}
.cnt{display:flex;gap:.5rem;flex-wrap:wrap}.pill{border-radius:999px;padding:.12rem .7rem;font-size:.8rem;font-weight:600;border:1px solid}
.c-committed{--bg:#bfe3cc;--bd:#5fa77c;--tx:#14532d}.c-likely{--bg:#cfdcef;--bd:#7f9bc4;--tx:#1e3a5f}.c-risk{--bg:#ffd9c2;--bd:#e8590c;--tx:#7a2e05}.c-unplanned{--bg:#eceff3;--bd:#b6bcc6;--tx:#475569}
.pill{background:var(--bg);border-color:var(--bd);color:var(--tx)}
.rmg{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;position:relative}
.rmh{display:flex;border-bottom:1px solid var(--line);background:#fbfcfe;position:sticky;top:0}.rmh .lab{flex:0 0 340px;padding:.4rem .8rem;font-size:.75rem;color:var(--mute)}
.rmh .mo{position:relative;flex:1}.rmh .mo span{position:absolute;top:.4rem;font-size:.75rem;color:#64748b;font-weight:600;padding-left:.35rem;border-left:1px solid #e2e8f0}
.rmi{background:#eef2f7;padding:.35rem .8rem;font-weight:700;font-size:.88rem;color:#334155;display:flex;gap:.6rem;align-items:baseline}.rmi small{font-weight:400;color:#64748b}
.rmr{display:flex;border-top:1px solid #f1f5f9;min-height:44px;align-items:stretch;cursor:pointer}.rmr:hover{background:#f8fafc}.rmr.sel{background:#f0f4ff}
.rmr .lab{flex:0 0 340px;padding:.4rem .8rem;font-size:.86rem;display:flex;flex-direction:column;justify-content:center}
.rmr .lab .why{font-size:.72rem;color:var(--mute)}.rmr .lab .k{font-weight:700;color:#1d4ed8;margin-right:.3rem}
.rmr .tl{position:relative;flex:1}.vl{position:absolute;top:0;bottom:0;width:1px;background:#f1f5f9}
.bar{position:absolute;top:11px;height:22px;border-radius:7px;background:var(--bg);border:1.5px solid var(--bd);color:var(--tx);font-size:.72rem;line-height:19px;padding:0 .45rem;white-space:nowrap;overflow:hidden}
.ghost{position:absolute;top:11px;height:22px;border-radius:7px;border:1.5px dashed #cbd5e1;background:transparent}
.lg{display:flex;gap:1rem;flex-wrap:wrap;font-size:.76rem;color:var(--mute);align-items:center}.lg i{display:inline-block;vertical-align:-3px;margin-right:.3rem}
.due{position:absolute;top:8px;width:14px;height:14px;background:#7c3aed;transform:rotate(45deg);border-radius:2px}.duel{position:absolute;top:26px;font-size:.66rem;color:#6d28d9;white-space:nowrap}
.idue{position:absolute;top:0;bottom:0;width:0;border-left:2px dashed #d97796}
.today{position:absolute;top:0;bottom:0;width:0;border-left:2px dashed #2dd4bf}
#wi{position:fixed;right:0;top:0;bottom:0;width:380px;max-width:94vw;background:#fff;border-left:1px solid var(--line);box-shadow:-10px 0 30px rgba(15,23,42,.12);padding:1rem 1.1rem;overflow:auto;display:none;z-index:30}
#wi h2{font-size:1rem;margin:0 1.6rem .2rem 0}#wi .x{position:absolute;right:.7rem;top:.5rem;border:0;background:none;font-size:1.2rem;cursor:pointer;color:var(--mute)}
#wi h3{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);margin:.9rem 0 .3rem}#wi ul{margin:0;padding-left:1.1rem;font-size:.84rem}
#wi .row{display:flex;gap:.3rem;flex-wrap:wrap;align-items:center;margin:.2rem 0}#wi button,#chg button,#exp button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:.15rem .55rem;cursor:pointer;font-size:.8rem}
#wi button.on{background:#1f2937;color:#fff;border-color:#1f2937}#wi input[type=date]{border:1px solid var(--line);border-radius:6px;padding:.15rem .4rem}
#chg{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;background:#1f2937;color:#fff;border-radius:999px;padding:.35rem .5rem .35rem 1rem;display:none;gap:.6rem;align-items:center;z-index:25;font-size:.84rem}
#chg button{background:#374151;color:#fff;border-color:#4b5563}#exp{position:fixed;inset:0;background:rgba(15,23,42,.45);display:none;z-index:40;align-items:center;justify-content:center}
#exp>div{background:#fff;border-radius:12px;padding:1rem 1.2rem;width:min(720px,94vw)}#exp textarea{width:100%;height:260px;font:12px/1.4 ui-monospace,monospace;border:1px solid var(--line);border-radius:8px;padding:.5rem}
body.sk .keyonly{display:none}
#bf{max-width:1100px}#bfbar{display:flex;gap:.8rem;align-items:center;flex-wrap:wrap;margin:.1rem 0 .8rem}#bfbar select{border:1px solid var(--line);border-radius:8px;padding:.3rem .5rem;font-size:.9rem}
#bfbar button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:.25rem .7rem;cursor:pointer;font-size:.82rem}
.bfc{background:#fff;border:1px solid var(--line);border-radius:12px;padding:1rem 1.2rem;margin-bottom:1rem}.bfc h2{margin:0 0 .15rem;font-size:1.05rem}.bfc .sub{color:var(--mute);font-size:.8rem;margin-bottom:.6rem}
.bfc table{width:100%;border-collapse:collapse;font-size:.86rem}.bfc th{text-align:left;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);padding:.3rem .5rem;border-bottom:1px solid var(--line)}
.bfc td{padding:.45rem .5rem;border-bottom:1px solid #f1f5f9;vertical-align:top}.gap{font-weight:600;border-radius:999px;padding:.05rem .55rem;font-size:.76rem;white-space:nowrap}
.g-late{background:#ffd9c2;color:#7a2e05}.g-ok{background:#bfe3cc;color:#14532d}.g-unk{background:#eceff3;color:#475569}.bfc .why{color:var(--mute);font-size:.76rem}
.bfs{display:flex;gap:.6rem;flex-wrap:wrap;margin:.3rem 0 .7rem}.bfn{color:var(--mute);font-size:.8rem;margin:.4rem 0 0}
@media print{header,#wi,#chg,#exp,#rmbar .note{display:none}.panel{display:none}.panel.on{display:block}}
"""

JS = r"""
(()=>{
const D=JSON.parse(document.getElementById('data').textContent),host=document.getElementById('rmhost');if(!host)return;
const $=s=>document.querySelector(s),DAY=864e5,I=D.issues;
const P=s=>s?new Date(s+'T00:00:00Z').getTime():null,F=t=>new Date(t).toISOString().slice(0,10);
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],ML=t=>{const d=new Date(t);return MON[d.getUTCMonth()]+' '+d.getUTCFullYear()};
const early=new Set(['Funnel','Backlog','New','To Do','Analyzing']);
const KEY='po-whatif:'+D.base+':'+(D.project||'');let ov={};try{ov=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
let stake=true,sel=null;const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(ov))}catch(e){}};
const preds={};(D.alledges||[]).forEach(([a,b])=>{if(I[a]&&I[b])(preds[b]=preds[b]||[]).push(a)});
function eff(k){const v=I[k],o=ov[k]||{},e0=P(v.end);return{start:P(v.start),end:e0==null?null:e0+(o.shift||0)*7*DAY,
 due:(o.due!==undefined)?(o.due===''?null:P(o.due)):P(v.due),who:o.owner==null?!!v.who:o.owner,flag:o.flag==null?!!v.flagged:o.flag}}
let memo={};
function fc(k,seen){seen=seen||[];if(memo[k])return memo[k];if(seen.includes(k))return{fs:null,fe:null,why:[]};const e=eff(k),v=I[k];let fs=e.start,fe=e.end;const why=[];
 if(!v.core){const d=P(v.due);fs=d;fe=d}
 let b=null;(preds[k]||[]).forEach(p=>{const f=fc(p,seen.concat(k)),pv=I[p];
  if(f.fe==null)why.push('waits on '+(pv.ext?'another project':'a prerequisite')+' with no date');else b=Math.max(b==null?0:b,f.fe);
  if(early.has(pv.st)&&(!pv.core||pv.ext))why.push('waits on '+(pv.ext?'another project':'an enabler')+' that has not started')});
 if(fs!=null&&fe!=null&&b!=null&&b>fs){const d=fe-fs;fs=b;fe=fs+d}
 return memo[k]={fs,fe,why,planEnd:e.end}}
function cls(k){const v=I[k],e=eff(k),f=fc(k),r=[];if(e.flag)r.push('flagged as an impediment');f.why.forEach(w=>{if(!r.includes(w))r.push(w)});
 if(f.fe!=null&&e.end!=null&&f.fe>e.end+DAY)r.push('forecast '+Math.round((f.fe-e.end)/DAY/7*10)/10+' weeks behind its plan, because of blockers');
 if(e.due!=null&&f.fe!=null&&f.fe>e.due)r.push('forecast passes its commitment date');
 const pd=P(v.pardue);if(pd!=null&&f.fe!=null&&f.fe>pd)r.push('forecast passes the initiative due date');
 const info=[];if(!e.who)info.push('no owner');if(!v.par)info.push('no initiative');if(e.start==null||e.end==null)info.push('no dates');
 let c;if(info.length)c='unplanned';else if(r.length)c='risk';else if(e.due!=null&&(v.refine==='Ready'||v.st==='Implementing'))c='committed';else c='likely';
 return{c,r,info,e,f}}
const LBL={committed:'Committed',likely:'Likely',risk:'At risk',unplanned:'Not yet planned'};
function render(){memo={};const pf=window.__pof,ks=Object.keys(I).filter(k=>I[k].core&&(!pf||pf.match(k))),R={};ks.forEach(k=>R[k]=cls(k));
 const ts=[];ks.forEach(k=>{const r=R[k];[r.e.start,r.f.fs,r.f.fe,r.e.end,r.e.due,P(I[k].pardue)].forEach(t=>t!=null&&ts.push(t))});ts.push(Date.now());
 const lo0=new Date(Math.min(...ts));const lo=Date.UTC(lo0.getUTCFullYear(),lo0.getUTCMonth(),1);const hi0=new Date(Math.max(...ts));const hi=Date.UTC(hi0.getUTCFullYear(),hi0.getUTCMonth()+1,1);
 const pc=t=>((t-lo)/(hi-lo)*100).toFixed(3)+'%',w=(a,b)=>(((b-a)/(hi-lo))*100).toFixed(3)+'%';
 const cnt={committed:0,likely:0,risk:0,unplanned:0};ks.forEach(k=>cnt[R[k].c]++);
 const bar=$('#rmbar');bar.replaceChildren();const n=document.createElement('span');n.className='note';n.textContent='What-if is local to this browser. Nothing is written to Jira.';bar.append(n);
 const cd=document.createElement('div');cd.className='cnt';Object.keys(cnt).forEach(c=>{const s=document.createElement('span');s.className='pill c-'+c;s.textContent=cnt[c]+' '+LBL[c].toLowerCase();cd.append(s)});bar.append(cd);
 const lab=document.createElement('label');const cb=document.createElement('input');cb.type='checkbox';cb.checked=stake;cb.onchange=()=>{stake=cb.checked;render()};lab.append(cb,' Stakeholder view (hide keys and people)');bar.append(lab);const lg=document.createElement('div');lg.className='lg';lg.innerHTML='<span><i style="width:12px;height:12px;background:#7c3aed;transform:rotate(45deg);border-radius:2px"></i>commitment date (Jira Due date)</span><span><i style="width:22px;height:11px;border:1.5px dashed #cbd5e1;border-radius:4px"></i>original plan, where the forecast is later</span><span><i style="width:0;height:13px;border-left:2px dashed #d97796"></i>initiative due date</span><span><i style="width:0;height:13px;border-left:2px dashed #2dd4bf"></i>today</span>';bar.append(lg);
 const g=document.createElement('div');g.className='rmg';
 let mh='<div class=rmh><div class=lab>Outcome</div><div class=mo>';for(let t=lo;t<hi;){const d=new Date(t);mh+='<span style="left:'+pc(t)+'">'+ML(t)+'</span>';t=Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,1)}mh+='</div></div>';g.innerHTML=mh;
 const vl=(()=>{let s='';for(let t=lo;t<hi;){const d=new Date(t);s+='<i class=vl style="left:'+pc(t)+'"></i>';t=Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,1)}return s})();
 const groups={};ks.forEach(k=>(groups[I[k].par||'~']=groups[I[k].par||'~']||[]).push(k));
 Object.keys(groups).sort((a,b)=>a==='~'?1:b==='~'?-1:a<b?-1:1).forEach(par=>{const arr=groups[par].sort((a,b)=>(R[a].f.fe||9e15)-(R[b].f.fe||9e15));const f0=I[arr[0]];
  const h=document.createElement('div');h.className='rmi';h.innerHTML='<span>'+(par==='~'?'No initiative yet':esc(f0.parsum||par))+'</span>'+(f0.pardue?'<small>due '+f0.pardue+'</small>':'');g.append(h);
  arr.forEach(k=>{const r=R[k],v=I[k],row=document.createElement('div');row.className='rmr'+(sel===k?' sel':'');row.dataset.k=k;
   const why=r.c==='unplanned'?r.info.join(', '):r.r[0]||'';
   let h2='<div class=lab><div><span class="k keyonly">'+esc(k)+'</span>'+esc(v.sum)+'</div>'+(why?'<div class=why>'+esc(why)+'</div>':'')+'</div><div class=tl>'+vl;
   if(v.pardue)h2+='<i class=idue style="left:'+pc(P(v.pardue))+'"></i>';
   h2+='<i class=today style="left:'+pc(Date.now())+'"></i>';
   if(r.e.start!=null&&r.e.end!=null){const showGhost=r.f.fe!=null&&r.f.fe>r.e.end+DAY||(r.f.fs!=null&&r.f.fs>r.e.start+DAY);
    if(showGhost)h2+='<i class=ghost style="left:'+pc(r.e.start)+';width:'+w(r.e.start,r.e.end)+'"></i>';
    const s=r.f.fs??r.e.start,e=r.f.fe??r.e.end;h2+='<span class="bar c-'+r.c+'" style="left:'+pc(s)+';width:'+w(s,Math.max(e,s+3*DAY))+'">'+(stake?ML(e):F(s)+' → '+F(e))+'</span>'}
   if(r.e.due!=null)h2+='<i class=due title="commitment '+F(r.e.due)+'" style="left:calc('+pc(r.e.due)+' - 7px)"></i>';
   row.innerHTML=h2+'</div>';row.onclick=()=>{sel=k;drawer(k);render()};g.append(row)})});
 host.replaceChildren(g);document.body.classList.toggle('sk',stake);changes()}
const R_=k=>cls(k);
function gapOf(fe,need){if(need==null)return{t:'need-by date unknown',c:'unk',d:null};if(fe==null)return{t:'our date unknown',c:'unk',d:null};const d=Math.round((fe-need)/DAY/7*10)/10;return d>0?{t:'late by '+d+' wk',c:'late',d}:{t:'on time'+(d<0?' ('+(-d)+' wk margin)':''),c:'ok',d}}
function brief(){memo={};const host2=document.getElementById('bfhost'),bar=document.getElementById('bfbar');if(!host2)return;
 const fs=(D.facets||{}),cons=(fs.cons||[]),prov=(fs.prov||[]),all=[...new Map([...cons,...prov].map(o=>[o.k,o])).values()];
 if(!bar.dataset.init){bar.dataset.init=1;const s=document.createElement('select');s.id='bfsel';all.forEach(o=>{const x=document.createElement('option');x.value=o.k;x.textContent=o.name;s.append(x)});
  const hp=new URLSearchParams(location.hash.slice(1)).get('for');if(hp&&all.some(o=>o.k===hp))s.value=hp;
  s.onchange=()=>{const p=new URLSearchParams(location.hash.slice(1));p.set('for',s.value);history.replaceState(null,'','#'+p);brief()};
  const lab=document.createElement('label');lab.innerHTML='<input type=checkbox id=bfkeys> show our issue keys';lab.querySelector('input').onchange=brief;
  const cp=document.createElement('button');cp.textContent='Copy as Markdown';cp.onclick=()=>{navigator.clipboard&&navigator.clipboard.writeText(window.__bfmd||'')};
  const pr=document.createElement('button');pr.textContent='Print / save as PDF';pr.onclick=()=>window.print();
  const l0=document.createElement('span');l0.textContent='Brief: ';bar.append(l0,s,lab,cp,pr)}
 const C=document.getElementById('bfsel')?document.getElementById('bfsel').value:'';if(!C){host2.innerHTML='<p class=mute>No other project is linked to our epics yet.</p>';return}
 const nm=(all.find(o=>o.k===C)||{}).name||C,keys=document.getElementById('bfkeys')&&document.getElementById('bfkeys').checked;
 const ours=Object.keys(I).filter(k=>I[k].core),rows=[],needs=[];
 ours.forEach(k=>{const v=I[k];v.blocks.filter(r=>r.ext&&r.k.indexOf(C+'-')===0).forEach(r=>{const c=cls(k),their=I[r.k]||{},g=gapOf(c.f.fe,P(their.due));rows.push({k,v,c,r,their,g})});
  v.blockedBy.filter(r=>r.ext&&r.k.indexOf(C+'-')===0).forEach(r=>{const c=cls(k),their=I[r.k]||{},d=P(their.due),need=c.f.fs!=null?c.f.fs:c.e.start,g=gapOf(d,need);needs.push({k,v,c,r,their,g,need})})});
 const ord={late:0,unk:1,ok:2};rows.sort((a,b)=>ord[a.g.c]-ord[b.g.c]);needs.sort((a,b)=>ord[a.g.c]-ord[b.g.c]);
 const cnt=a=>({late:a.filter(x=>x.g.c==='late').length,unk:a.filter(x=>x.g.c==='unk').length,ok:a.filter(x=>x.g.c==='ok').length});
 const m=(t)=>t==null?'?':ML(t),dt=s=>s?ML(P(s)):'unknown';
 const lbl=x=>(keys?x.k+' · ':'')+x.v.sum;
 const A=cnt(rows),B=cnt(needs);let h='<div class=bfc><h2>What '+esc(nm)+' can rely on from us</h2><div class=sub>Snapshot '+F(Date.now())+'. Forecast = our planned dates, moved later where a blocker ends later. It is a forecast, not a commitment, unless marked Committed.</div>';
 if(!rows.length)h+='<p class=mute>Nothing of theirs is recorded as waiting on us.</p>';else{
  h+='<div class=bfs><span class="gap g-ok">'+A.ok+' on time</span><span class="gap g-late">'+A.late+' late</span><span class="gap g-unk">'+A.unk+' unknown</span></div><table><tr><th>You need</th><th>Needed by</th><th>Our outcome</th><th>Our forecast</th><th>Confidence</th><th>Fit</th></tr>';
  rows.forEach(x=>{h+='<tr><td><b>'+esc(x.r.k)+'</b> '+esc((x.r.s||'').slice(0,70))+'<div class=why>'+esc(x.r.st)+'</div></td><td>'+dt(x.their.due)+'</td><td>'+esc(lbl(x))+(x.c.r[0]?'<div class=why>'+esc(x.c.r[0])+'</div>':'')+'</td><td>'+m(x.c.f.fe)+'</td><td><span class="pill c-'+x.c.c+'">'+LBL[x.c.c]+'</span></td><td><span class="gap g-'+x.g.c+'">'+esc(x.g.t)+'</span></td></tr>'});h+='</table>'}
 h+='</div><div class=bfc><h2>What we need from '+esc(nm)+'</h2><div class=sub>Items of theirs that block our outcomes. Their date is what is recorded in Jira, not something they have agreed.</div>';
 if(!needs.length)h+='<p class=mute>Nothing of theirs is recorded as blocking us.</p>';else{
  h+='<div class=bfs><span class="gap g-ok">'+B.ok+' in time</span><span class="gap g-late">'+B.late+' late for us</span><span class="gap g-unk">'+B.unk+' unknown</span></div><table><tr><th>We need</th><th>Their date</th><th>Our outcome waiting</th><th>We need it by</th><th>Fit</th></tr>';
  needs.forEach(x=>{h+='<tr><td><b>'+esc(x.r.k)+'</b> '+esc((x.r.s||'').slice(0,70))+'<div class=why>'+esc(x.r.st)+'</div></td><td>'+dt(x.their.due)+'</td><td>'+esc(lbl(x))+'</td><td>'+m(x.need)+'</td><td><span class="gap g-'+x.g.c+'">'+esc(x.g.t.replace('late by','late for us by'))+'</span></td></tr>'});h+='</table>'}
 h+='<p class=bfn>Dates come from Jira and from blocker links. Anything not recorded in Jira is not shown here.</p></div>';host2.innerHTML=h;
 const md='# What '+nm+' can rely on from us ('+F(Date.now())+')\n\nForecast, not a commitment unless marked Committed.\n\n| You need | Needed by | Our outcome | Our forecast | Confidence | Fit |\n|---|---|---|---|---|---|\n'+rows.map(x=>'| '+x.r.k+' '+(x.r.s||'')+' | '+dt(x.their.due)+' | '+lbl(x)+' | '+m(x.c.f.fe)+' | '+LBL[x.c.c]+' | '+x.g.t+' |').join('\n')+
  '\n\n## What we need from '+nm+'\n\n| We need | Their date | Our outcome waiting | We need it by | Fit |\n|---|---|---|---|---|\n'+needs.map(x=>'| '+x.r.k+' '+(x.r.s||'')+' | '+dt(x.their.due)+' | '+lbl(x)+' | '+m(x.need)+' | '+x.g.t+' |').join('\n');window.__bfmd=md}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function drawer(k){const v=I[k],r=cls(k),o=ov[k]||{},d=$('#wi');d.style.display='block';
 const sh=o.shift||0;const btn=(n)=>'<button data-s="'+n+'" class="'+(sh===n?'on':'')+'">'+(n>0?'+':'')+n+' wk</button>';
 d.innerHTML='<button class=x id=wix>×</button><h2><a href="'+esc(v.url)+'" target=_blank rel=noopener>'+esc(k)+' ↗</a></h2><div>'+esc(v.sum)+'</div>'+
 '<div class=row><span class="pill c-'+r.c+'">'+LBL[r.c]+'</span><span class=mute>'+esc(v.st)+(v.refine?' · '+esc(v.refine):'')+(v.ws!=null?' · WSJF '+v.ws:'')+'</span></div>'+
 '<h3>Why</h3><ul>'+((r.r.concat(r.info).map(x=>'<li>'+esc(x)+'</li>').join(''))||'<li>No flags: owner, dates and blockers look fine.</li>')+'</ul>'+
 '<h3>Dates</h3><div>Plan '+(r.e.start!=null?F(r.e.start):'?')+' → '+(r.e.end!=null?F(r.e.end):'?')+(sh?' (slipped '+sh+' wk)':'')+'<br>Forecast '+(r.f.fs!=null?F(r.f.fs):'?')+' → '+(r.f.fe!=null?F(r.f.fe):'?')+'<br>Commitment '+(r.e.due!=null?F(r.e.due):'none')+'</div>'+
 '<h3>What if…</h3><div class=row>Slip the end by '+[-2,-1,1,2,4].map(btn).join('')+'</div>'+
 '<div class=row>Commit to <input type=date id=wid value="'+(r.e.due!=null?F(r.e.due):'')+'"><button id=widc>clear</button></div>'+
 '<div class=row><label><input type=checkbox id=wio '+(r.e.who?'checked':'')+'> has an owner</label> <label><input type=checkbox id=wif '+(r.e.flag?'checked':'')+'> flagged as impediment</label></div>'+
 '<div class=row><button id=wir>Reset this epic</button></div>'+
 '<h3>Waits on</h3><ul>'+((preds[k]||[]).map(p=>{const f=fc(p),pv=I[p];return'<li>'+esc(p)+' ['+esc(pv.st)+'] '+esc(pv.sum.slice(0,50))+(f.fe!=null?' — ends '+F(f.fe):' — no date')+(pv.ext?' (other project)':'')+'</li>'}).join('')||'<li>Nothing.</li>')+'</ul>';
 const set=(f)=>{const x=ov[k]=ov[k]||{};f(x);if(!Object.keys(x).length||(x.shift===0&&x.due===undefined&&x.owner==null&&x.flag==null))delete ov[k];save();render();drawer(k)};
 $('#wix').onclick=()=>{d.style.display='none';sel=null;render()};d.querySelectorAll('[data-s]').forEach(b=>b.onclick=()=>set(x=>{const n=+b.dataset.s;x.shift=(x.shift||0)===n?0:n}));
 $('#wid').onchange=e=>set(x=>{x.due=e.target.value});$('#widc').onclick=()=>set(x=>{x.due=''});
 $('#wio').onchange=e=>set(x=>{x.owner=e.target.checked===!!v.who?null:e.target.checked});$('#wif').onchange=e=>set(x=>{x.flag=e.target.checked===!!v.flagged?null:e.target.checked});
 $('#wir').onclick=()=>{delete ov[k];save();render();drawer(k)}}
function list(){const L=[];Object.keys(ov).forEach(k=>{const o=ov[k],v=I[k],e=eff(k);
 if(o.shift)L.push({key:k,field:'Target end',from:v.end,to:F(e.end),note:'slip '+o.shift+' weeks'});
 if(o.due!==undefined)L.push({key:k,field:'Due date (commitment)',from:v.due||null,to:o.due||null});
 if(o.owner!=null)L.push({key:k,field:'Assignee',from:v.who||null,to:o.owner?'(assign someone)':'(unassign)'});
 if(o.flag!=null)L.push({key:k,field:'Flagged',from:!!v.flagged,to:o.flag})});return L}
function changes(){const L=list(),c=$('#chg');if(!L.length){c.style.display='none';return}c.style.display='flex';
 c.innerHTML='<span>'+L.length+' local change'+(L.length>1?'s':'')+' — not applied to Jira</span><button id=chx>Export…</button><button id=chr>Reset all</button>';
 $('#chr').onclick=()=>{ov={};save();$('#wi').style.display='none';sel=null;render()};
 $('#chx').onclick=()=>{const md='# Proposed Jira changes (not applied)\n\n| Issue | Field | From | To |\n|---|---|---|---|\n'+L.map(x=>'| '+x.key+' | '+x.field+' | '+(x.from??'—')+' | '+(x.to??'—')+(x.note?' ('+x.note+')':'')+' |').join('\n')+
  '\n\nJSON:\n'+JSON.stringify(L,null,2);$('#expt').value=md;$('#exp').style.display='flex'}}
$('#expclose').onclick=()=>$('#exp').style.display='none';$('#expcopy').onclick=()=>{$('#expt').select();document.execCommand('copy')};
document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('#exp').style.display='none'}});
render();brief();document.addEventListener('pofilter',()=>{render()});window.addEventListener('hashchange',()=>{const f=new URLSearchParams(location.hash.slice(1)).get('for'),s=document.getElementById('bfsel');if(f&&s&&s.value!==f){s.value=f;brief()}});document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.t==='brief')brief()}));
})();
"""
