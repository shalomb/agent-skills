// Pure view-state logic for the Topologies tab: filters, pins, depth and the shown / ghost / hidden decision. No DOM.
// Used two ways: required by node tests (tests/js) and inlined into the page by topology.js(). Keep this file free of the
// closing-script-tag sequence, since it is embedded in a <script> element.
// State: {filters:{labels,components,status,rel,dates:{from,to,undated}}, pins, depth}. Hover is transient and not part of it.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ViewState = factory();
})(this, function () {
  const LABEL_GROUPS = [
    {prefix: 'kind-', title: 'Work kind'}, {prefix: 'for-', title: 'Serves'}, {prefix: 'pod-', title: 'POD'},
    {prefix: 'cap-', title: 'Capability'}, {prefix: 'pi-', title: 'PI'}, {prefix: 'other', title: 'Other'},
  ];
  const REL = ['incoming', 'external', 'blocking'];
  const STATE_KEYS = ['pin', 'depth', 'label', 'comp', 'status', 'rel', 'from', 'to', 'undated'];

  const emptyState = () => ({
    filters: {labels: [], components: [], status: [], rel: [], dates: {from: null, to: null, undated: true}},
    pins: [], depth: 'direct',
  });

  const labelGroup = label => {
    const g = LABEL_GROUPS.find(x => x.prefix !== 'other' && String(label).startsWith(x.prefix));
    return g ? g.prefix : 'other';
  };
  const day = d => (d ? String(d).slice(0, 10) : null);
  const datesActive = d => !!(d && (d.from || d.to || d.undated === false));
  const hasFilters = f => !!(f.labels.length || f.components.length || f.status.length || f.rel.length || datesActive(f.dates));
  const activeCount = f => f.labels.length + f.components.length + f.status.length + f.rel.length + (datesActive(f.dates) ? 1 : 0);

  // Where an issue sits relative to the ART, from cls = {key: [kind, group]} (kind: pod, interface, product, external).
  const relFlags = (issue, cls) => {
    const own = cls[issue.key];
    const other = r => {
      const c = cls[r.k];
      return c && !(own && own[0] === 'pod' && c[0] === 'pod' && c[1] === own[1]) ? c : null;
    };
    const blockedBy = issue.blockedBy || [], blocks = issue.blocks || [];
    return {
      incoming: blockedBy.some(r => { const c = other(r); return c && (c[0] === 'external' || c[0] === 'pod'); }),
      external: blocks.some(r => (cls[r.k] || [])[0] === 'external'),
      blocking: blocks.some(r => { const c = other(r); return c && c[0] === 'pod'; }),
    };
  };

  const matchDates = (issue, d) => {
    const s = day(issue.start), e = day(issue.end);
    if (!s && !e) return d.undated !== false;
    const lo = s || e, hi = e || s;
    return (!d.from || hi >= d.from) && (!d.to || lo <= d.to);
  };

  // OR within a label group, AND between groups; AND across kinds of filter; relationship toggles are OR'd together.
  const match = (issue, f, cls) => {
    if (f.labels.length) {
      const have = new Set(issue.labels || []), byGroup = {};
      f.labels.forEach(l => { (byGroup[labelGroup(l)] = byGroup[labelGroup(l)] || []).push(l); });
      if (!Object.values(byGroup).every(ls => ls.some(l => have.has(l)))) return false;
    }
    if (f.components.length && !(issue.components || []).some(c => f.components.includes(c))) return false;
    if (f.status.length && !f.status.includes(issue.st)) return false;
    if (f.rel.length) {
      const flags = relFlags(issue, cls || {});
      if (!f.rel.some(r => flags[r])) return false;
    }
    return matchDates(issue, f.dates);
  };

  const reach = (k, m) => {
    const s = new Set([k]), q = [k];
    while (q.length) (m[q.pop()] || []).forEach(y => { if (!s.has(y)) { s.add(y); q.push(y); } });
    return s;
  };

  // Pins override filters: while anything is pinned the view is the pinned epics and their chain, filters are not applied.
  function classifyPins(nodes, edges, pins, depth) {
    const up = {}, dn = {}, vis = new Set(), E = new Set();
    edges.forEach(([a, b]) => { (dn[a] = dn[a] || []).push(b); (up[b] = up[b] || []).push(a); });
    pins.forEach(p => {
      vis.add(p);
      if (depth === 'direct') {
        (dn[p] || []).forEach(b => { vis.add(b); E.add(p + '|' + b); });
        (up[p] || []).forEach(a => { vis.add(a); E.add(a + '|' + p); });
      } else {
        const A = reach(p, up), B = reach(p, dn);
        A.forEach(x => vis.add(x)); B.forEach(x => vis.add(x));
        edges.forEach(([a, b]) => { if ((A.has(a) && A.has(b)) || (B.has(a) && B.has(b))) E.add(a + '|' + b); });
      }
    });
    return {
      nodes: Object.fromEntries(nodes.map(k => [k, vis.has(k) ? 'shown' : 'hidden'])),
      edges: Object.fromEntries(edges.map(([a, b]) => [a + '|' + b, E.has(a + '|' + b) ? 'shown' : 'hidden'])),
    };
  }

  function classify({issues, nodes, edges, state, cls}) {
    const pins = state.pins.filter(p => nodes.includes(p));
    if (pins.length) return Object.assign({active: true, mode: 'pins'}, classifyPins(nodes, edges, pins, state.depth));
    if (!hasFilters(state.filters)) {
      return {active: false, mode: 'none', nodes: Object.fromEntries(nodes.map(k => [k, 'shown'])),
              edges: Object.fromEntries(edges.map(([a, b]) => [a + '|' + b, 'shown']))};
    }
    const hit = new Set(nodes.filter(k => issues[k] && match(issues[k], state.filters, cls)));
    const near = new Set();
    edges.forEach(([a, b]) => { if (hit.has(a)) near.add(b); if (hit.has(b)) near.add(a); });
    const st = Object.fromEntries(nodes.map(k => [k, hit.has(k) ? 'shown' : near.has(k) ? 'ghost' : 'hidden']));
    return {
      active: true, mode: 'filters', nodes: st,
      edges: Object.fromEntries(edges.map(([a, b]) => [a + '|' + b,
        st[a] === 'hidden' || st[b] === 'hidden' || (st[a] === 'ghost' && st[b] === 'ghost') ? 'hidden' : st[a] === 'ghost' || st[b] === 'ghost' ? 'ghost' : 'shown'])),
    };
  }

  const byCount = (a, b) => b.n - a.n || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
  const tally = (items, name) => {
    const m = new Map();
    items.forEach(x => m.set(name(x), (m.get(name(x)) || 0) + 1));
    return [...m].map(([n, c]) => ({name: n, n: c})).sort(byCount);
  };

  function facets(issues, keys) {
    const list = keys.map(k => issues[k]).filter(Boolean);
    const groups = {};
    list.forEach(v => (v.labels || []).forEach(l => {
      const g = labelGroup(l);
      groups[g] = groups[g] || {};
      groups[g][l] = (groups[g][l] || 0) + 1;
    }));
    const labelGroups = LABEL_GROUPS.filter(g => groups[g.prefix]).map(g => ({
      prefix: g.prefix, title: g.title,
      values: Object.entries(groups[g.prefix]).map(([label, n]) => ({label, name: g.prefix === 'other' ? label : label.slice(g.prefix.length), n}))
        .sort((a, b) => b.n - a.n || (a.label < b.label ? -1 : 1)),
    }));
    const days = [];
    list.forEach(v => { if (day(v.start)) days.push(day(v.start)); if (day(v.end)) days.push(day(v.end)); });
    days.sort();
    return {
      labelGroups,
      components: tally(list.flatMap(v => v.components || []), x => x),
      statuses: tally(list, v => v.st),
      dates: {min: days[0] || null, max: days[days.length - 1] || null},
    };
  }

  // Each list value is escaped on its own (comma becomes %2C) so values may contain commas; the list is then
  // joined with plain commas, which is also what the older pin=A,B hashes look like.
  const enc = list => list.map(encodeURIComponent).join(',');
  const dec = s => s.split(',').filter(Boolean).map(x => { try { return decodeURIComponent(x); } catch (e) { return x; } });

  function toHash(state) {
    const p = new URLSearchParams(), f = state.filters;
    if (state.pins.length) p.set('pin', enc(state.pins));
    if (state.depth === 'full') p.set('depth', 'full');
    [['label', f.labels], ['comp', f.components], ['status', f.status], ['rel', f.rel]].forEach(([k, v]) => { if (v.length) p.set(k, enc(v)); });
    if (f.dates.from) p.set('from', f.dates.from);
    if (f.dates.to) p.set('to', f.dates.to);
    if (f.dates.undated === false) p.set('undated', '0');
    return p.toString();
  }

  function fromHash(hash) {
    const p = new URLSearchParams(String(hash || '').replace(/^#/, '')), s = emptyState(), f = s.filters;
    const list = k => dec(p.get(k) || '');
    s.pins = list('pin');
    if (p.get('depth') === 'full') s.depth = 'full';
    f.labels = list('label'); f.components = list('comp'); f.status = list('status');
    f.rel = list('rel').filter(r => REL.includes(r));
    f.dates.from = p.get('from') || null;
    f.dates.to = p.get('to') || null;
    if (p.get('undated') === '0') f.dates.undated = false;
    return s;
  }

  return {LABEL_GROUPS, REL, STATE_KEYS, emptyState, labelGroup, hasFilters, datesActive, activeCount, relFlags, match, classify, facets, toHash, fromHash};
});
