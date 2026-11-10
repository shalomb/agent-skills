// Pure view-state logic (scripts/viewstate.js), no DOM. Run: node --test tests/js
// Scenario ids refer to specs/filters-state.md.
const test = require('node:test');
const assert = require('node:assert/strict');
const VS = require('../../scripts/viewstate.js');

const issue = (key, extra) => Object.assign({key, st: 'Backlog', labels: [], components: [], start: null, end: null, blocks: [], blockedBy: []}, extra || {});
const ref = k => ({k, st: 'Backlog', s: k, ext: false});
const filters = extra => Object.assign({}, VS.emptyState().filters, extra);
const matches = (issues, f, cls) => Object.keys(issues).filter(k => VS.match(issues[k], f, cls || {})).sort();

test('S-flt-1 OR within a label group, AND between groups', () => {
  const I = {
    A: issue('A', {labels: ['kind-enabler', 'for-web']}),
    B: issue('B', {labels: ['kind-deliverable', 'for-mobile']}),
    C: issue('C', {labels: ['kind-spike', 'for-web']}),
    D: issue('D', {labels: ['for-web']}),
  };
  assert.deepEqual(matches(I, filters({labels: ['kind-enabler', 'kind-deliverable']})), ['A', 'B']);
  assert.deepEqual(matches(I, filters({labels: ['kind-enabler', 'kind-deliverable', 'for-web']})), ['A']);
  assert.deepEqual(matches(I, filters({labels: ['for-web', 'for-mobile']})), ['A', 'B', 'C', 'D']);
});

test('S-flt-1 labels without a known prefix form the "other" group', () => {
  assert.equal(VS.labelGroup('kind-x'), 'kind-');
  assert.equal(VS.labelGroup('pi-2025q1'), 'pi-');
  assert.equal(VS.labelGroup('area-onboarding'), 'other');
  const I = {A: issue('A', {labels: ['area-a']}), B: issue('B', {labels: ['area-b']}), C: issue('C', {labels: ['kind-x']})};
  assert.deepEqual(matches(I, filters({labels: ['area-a', 'area-b']})), ['A', 'B']);
});

test('S-flt-1 status chips are OR within status and AND with labels', () => {
  const I = {A: issue('A', {st: 'Backlog', labels: ['kind-x']}), B: issue('B', {st: 'Funnel', labels: ['kind-x']}), C: issue('C', {st: 'Done', labels: []})};
  assert.deepEqual(matches(I, filters({status: ['Backlog', 'Funnel']})), ['A', 'B']);
  assert.deepEqual(matches(I, filters({status: ['Backlog', 'Done'], labels: ['kind-x']})), ['A']);
});

test('S-flt-2 components match on any selected component; none selected does not filter', () => {
  const I = {A: issue('A', {components: ['api']}), B: issue('B', {components: ['ui', 'db']}), C: issue('C', {components: []}), D: issue('D', {components: null})};
  assert.deepEqual(matches(I, filters({components: ['api', 'db']})), ['A', 'B']);
  assert.deepEqual(matches(I, filters({components: []})), ['A', 'B', 'C', 'D']);
});

const cls = {A1: ['pod', 'A'], A2: ['pod', 'A'], B1: ['pod', 'B'], E1: ['external', 'EXT'], R1: ['interface', 'REQ']};
const relIssues = () => ({
  A1: issue('A1', {blockedBy: [ref('B1')]}),                  // waits on another POD: incoming
  A2: issue('A2', {blockedBy: [ref('A1')]}),                  // waits on the same POD: not incoming
  B1: issue('B1', {blocks: [ref('A1'), ref('E1')]}),          // blocks another POD and leaves the ART
  E1: issue('E1', {blockedBy: [ref('B1')]}),
  R1: issue('R1', {blocks: [ref('A2')]}),                     // interface blocks a POD
});

test('S-flt-3 incoming: waits on another POD or outside the ART', () => {
  const I = relIssues();
  I.A1.blockedBy.push(ref('E1'));
  assert.deepEqual(matches(I, filters({rel: ['incoming']}), cls), ['A1', 'E1']);
  const J = {A1: issue('A1', {blockedBy: [ref('E1')]}), A2: issue('A2', {blockedBy: [ref('A1')]})};
  assert.deepEqual(matches(J, filters({rel: ['incoming']}), cls), ['A1']);
});

test('S-flt-3 external: has a link leaving the ART', () => {
  assert.deepEqual(matches(relIssues(), filters({rel: ['external']}), cls), ['B1']);
});

test('S-flt-3 blocking: blocks another POD', () => {
  assert.deepEqual(matches(relIssues(), filters({rel: ['blocking']}), cls), ['B1', 'R1']);
});

test('S-flt-3 several toggles are OR\'d with each other and AND\'d with labels', () => {
  const I = relIssues();
  I.B1.labels = ['kind-x'];
  I.A1.labels = ['kind-y'];
  assert.deepEqual(matches(I, filters({rel: ['incoming', 'external']}), cls), ['A1', 'B1', 'E1']);
  assert.deepEqual(matches(I, filters({rel: ['incoming', 'external'], labels: ['kind-x']}), cls), ['B1']);
});

test('S-flt-4 date range overlaps target start to end; open ends are unbounded', () => {
  const I = {
    BEFORE: issue('BEFORE', {start: '2025-01-01', end: '2025-01-31'}),
    OVERLAP: issue('OVERLAP', {start: '2025-01-20', end: '2025-02-10'}),
    INSIDE: issue('INSIDE', {start: '2025-02-05', end: '2025-02-06'}),
    AFTER: issue('AFTER', {start: '2025-03-01', end: '2025-03-31'}),
    ONLYEND: issue('ONLYEND', {end: '2025-02-15'}),
  };
  const range = (from, to, undated) => filters({dates: {from, to, undated: undated !== false}});
  assert.deepEqual(matches(I, range('2025-02-01', '2025-02-28')), ['INSIDE', 'ONLYEND', 'OVERLAP']);
  assert.deepEqual(matches(I, range('2025-02-01', null)), ['AFTER', 'INSIDE', 'ONLYEND', 'OVERLAP']);
  assert.deepEqual(matches(I, range(null, '2025-01-10')), ['BEFORE']);
});

test('S-flt-4 an undated epic matches only when undated is on (default on); unknown is never a date', () => {
  const I = {DATED: issue('DATED', {start: '2025-02-05', end: '2025-02-06'}), NONE: issue('NONE'), EMPTY: issue('EMPTY', {start: '', end: ''})};
  assert.equal(VS.emptyState().filters.dates.undated, true);
  assert.deepEqual(matches(I, filters({dates: {from: '2025-02-01', to: '2025-02-28', undated: true}})), ['DATED', 'EMPTY', 'NONE']);
  assert.deepEqual(matches(I, filters({dates: {from: '2025-02-01', to: '2025-02-28', undated: false}})), ['DATED']);
  assert.deepEqual(matches(I, filters({dates: {from: '1900-01-01', to: '1900-01-02', undated: true}})), ['EMPTY', 'NONE']);
});

// Chain R -> A1 -> B1 -> A2, plus X -> Y on the side. Labels decide who matches.
const graph = () => {
  const issues = {
    R: issue('R', {labels: ['kind-x']}), A1: issue('A1', {labels: ['kind-y']}), B1: issue('B1', {labels: ['kind-x']}),
    A2: issue('A2', {labels: ['kind-y']}), X: issue('X', {labels: ['kind-y']}), Y: issue('Y', {labels: ['kind-y']}),
  };
  const edges = [['R', 'A1'], ['A1', 'B1'], ['B1', 'A2'], ['X', 'Y']];
  return {issues, edges, nodes: Object.keys(issues), cls: {}};
};
const classify = (g, state) => VS.classify(Object.assign({}, g, {state: Object.assign(VS.emptyState(), state)}));

test('S-flt-5 pinned epic and its neighbours are shown even when the filter would hide them', () => {
  const g = graph();
  const f = filters({labels: ['kind-x']});
  const filtered = classify(g, {filters: f});
  assert.equal(filtered.nodes.A1, 'ghost');
  const pinned = classify(g, {filters: f, pins: ['A1']});
  assert.deepEqual([pinned.nodes.R, pinned.nodes.A1, pinned.nodes.B1], ['shown', 'shown', 'shown']);
  assert.equal(pinned.nodes.A2, 'hidden');
  assert.equal(pinned.nodes.X, 'hidden');
  const full = classify(g, {filters: f, pins: ['A1'], depth: 'full'});
  assert.equal(full.nodes.A2, 'shown');
  assert.equal(full.edges['A1|B1'], 'shown');
  assert.equal(full.edges['X|Y'], 'hidden');
});

test('S-flt-5 pins alone behave as before: direct neighbours, edges only around the pin', () => {
  const r = classify(graph(), {pins: ['A1']});
  assert.deepEqual(Object.keys(r.nodes).filter(k => r.nodes[k] === 'shown').sort(), ['A1', 'B1', 'R']);
  assert.deepEqual(Object.keys(r.edges).filter(e => r.edges[e] === 'shown').sort(), ['A1|B1', 'R|A1']);
});

test('S-flt-6 linked neighbours that fail the filter are ghosts; unrelated epics are hidden', () => {
  const r = classify(graph(), {filters: filters({labels: ['kind-x']})});
  assert.deepEqual(r.nodes, {R: 'shown', A1: 'ghost', B1: 'shown', A2: 'ghost', X: 'hidden', Y: 'hidden'});
  assert.equal(r.edges['R|A1'], 'ghost');
  assert.equal(r.edges['A1|B1'], 'ghost');
  assert.equal(r.edges['X|Y'], 'hidden');
});

test('S-flt-6 a link between two matches is shown; a link between two ghosts is not drawn', () => {
  const g = graph();
  g.issues.A1.labels = ['kind-x'];
  let r = classify(g, {filters: filters({labels: ['kind-x']})});
  assert.equal(r.edges['A1|B1'], 'shown');
  assert.equal(r.edges['R|A1'], 'shown');
  g.issues = Object.assign({}, g.issues, {R: issue('R', {labels: ['kind-y']}), A2: issue('A2', {labels: ['kind-y']})});
  r = classify(g, {filters: filters({labels: ['kind-x']})});
  assert.equal(r.nodes.R, 'ghost');
  assert.equal(r.edges['R|A1'], 'ghost');
});

test('S-flt-7 toHash and fromHash round-trip the state exactly', () => {
  const states = [
    VS.emptyState(),
    Object.assign(VS.emptyState(), {pins: ['AAA-1', 'BBB-1'], depth: 'full'}),
    Object.assign(VS.emptyState(), {pins: ['AAA-1']}),
    {filters: {labels: ['kind-a', 'for-b'], components: ['api'], status: ['In Progress', 'Backlog'], rel: ['incoming', 'blocking'],
               dates: {from: '2025-01-01', to: '2025-06-30', undated: false}}, pins: ['X-1'], depth: 'direct'},
    {filters: {labels: ['has,comma', 'pct%2Cenc', '100%', 'a&b=c#d'], components: ['x y'], status: [], rel: [], dates: {from: null, to: '2025-06-30', undated: true}}, pins: [], depth: 'direct'},
  ];
  for (const s of states) assert.deepEqual(VS.fromHash(VS.toHash(s)), s, JSON.stringify(s));
  for (const s of states) assert.deepEqual(VS.fromHash('#' + VS.toHash(s)), s, 'leading #');
  assert.equal(VS.toHash(VS.emptyState()), '');
});

test('S-flt-7 keeps compatibility with pin=A,B&depth=full, plain or %2C-encoded, and ignores unknown keys', () => {
  const want = Object.assign(VS.emptyState(), {pins: ['AAA-1', 'BBB-1'], depth: 'full'});
  assert.deepEqual(VS.fromHash('#pin=AAA-1,BBB-1&depth=full'), want);
  assert.deepEqual(VS.fromHash('#tab=topology&pin=AAA-1%2CBBB-1&depth=full&k=AAA-1&junk=1'), want);
  assert.deepEqual(VS.fromHash('#nonsense'), VS.emptyState());
  assert.deepEqual(VS.fromHash(''), VS.emptyState());
  assert.deepEqual(VS.fromHash('#depth=sideways&undated=maybe'), VS.emptyState());
  for (const key of VS.STATE_KEYS) assert.ok(!['tab', 'k'].includes(key), key);
});

test('S-flt-8 with no filters and no pins every epic is shown and nothing is ghosted', () => {
  const g = graph();
  const r = classify(g, {});
  assert.equal(r.active, false);
  assert.deepEqual(Object.values(r.nodes), g.nodes.map(() => 'shown'));
  assert.deepEqual(Object.values(r.edges), g.edges.map(() => 'shown'));
  assert.equal(VS.activeCount(VS.emptyState().filters), 0);
});

test('S-flt-8 a filter that matches everything ghosts nothing', () => {
  const r = classify(graph(), {filters: filters({status: ['Backlog']})});
  assert.ok(Object.values(r.nodes).every(s => s === 'shown'));
});

test('S-flt-9 facets give label groups with prefix title, values and counts', () => {
  const I = {A: issue('A', {labels: ['kind-enabler', 'for-web', 'area-x']}), B: issue('B', {labels: ['kind-enabler', 'kind-deliverable', 'pi-q1']}), C: issue('C', {labels: null})};
  const f = VS.facets(I, Object.keys(I));
  assert.deepEqual(f.labelGroups.map(g => g.prefix), ['kind-', 'for-', 'pi-', 'other']);
  const kind = f.labelGroups[0];
  assert.equal(kind.title, 'Work kind');
  assert.deepEqual(kind.values, [{label: 'kind-enabler', name: 'enabler', n: 2}, {label: 'kind-deliverable', name: 'deliverable', n: 1}]);
  const other = f.labelGroups[3];
  assert.deepEqual(other.values, [{label: 'area-x', name: 'area-x', n: 1}]);
});

test('S-flt-9 components facet is empty when no epic has components, else sorted by count', () => {
  const none = {A: issue('A'), B: issue('B', {components: null})};
  assert.deepEqual(VS.facets(none, ['A', 'B']).components, []);
  const some = {A: issue('A', {components: ['api', 'ui']}), B: issue('B', {components: ['ui']})};
  assert.deepEqual(VS.facets(some, ['A', 'B']).components, [{name: 'ui', n: 2}, {name: 'api', n: 1}]);
});

test('S-flt-9 facets also list statuses and the target date span (unknown dates ignored)', () => {
  const I = {A: issue('A', {st: 'Funnel', start: '2025-02-01', end: '2025-03-01'}), B: issue('B', {st: 'Backlog', end: '2025-01-10'}), C: issue('C', {st: 'Funnel'})};
  const f = VS.facets(I, ['A', 'B', 'C']);
  assert.deepEqual(f.statuses, [{name: 'Funnel', n: 2}, {name: 'Backlog', n: 1}]);
  assert.deepEqual(f.dates, {min: '2025-01-10', max: '2025-03-01'});
  assert.deepEqual(VS.facets({A: issue('A')}, ['A']).dates, {min: null, max: null});
});
