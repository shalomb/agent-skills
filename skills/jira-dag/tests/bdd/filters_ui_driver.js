// Drives the Topologies filter drawer in headless Chrome and records DOM snapshots. Observation only: assertions live in Python.
// Usage: node filters_ui_driver.js <job.json>   job = {puppeteer, chrome, scenarios: {name: {url, steps: [...]}}}
// Steps: {snap}, {click: selector}, {clickText: [selector, text]}, {shiftClick: key}, {press}, {eval}, {reload}, {shot: path}, {wait}.
const fs = require('fs');

// Runs inside the page. Reads what the S-ui scenarios assert on; changes nothing.
function pageSnapshot() {
  const svg = document.querySelector('#p-topology > svg');
  const shift = el => {
    const m = (el.getAttribute('transform') || '').match(/translate\(\s*(-?[\d.e+-]+)[ ,]+(-?[\d.e+-]+)\s*\)/);
    return m ? [+m[1], +m[2]] : [0, 0];
  };
  const boxes = {};
  svg.querySelectorAll('g.tn').forEach(g => {
    const r = g.querySelector('rect'), t = shift(g);
    boxes[g.dataset.key] = {shown: g.style.display !== 'none', ghost: g.classList.contains('ghost'), dim: g.classList.contains('dim'),
      pos: [+r.getAttribute('x') + t[0], +r.getAttribute('y') + t[1]], opacity: +getComputedStyle(g).opacity};
  });
  const edges = {};
  svg.querySelectorAll('path[data-edge]').forEach(p => {
    edges[p.dataset.edge] = {shown: p.style.display !== 'none', ghost: p.classList.contains('ghost'), opacity: +getComputedStyle(p).opacity};
  });
  const vis = e => !!e && getComputedStyle(e).display !== 'none';
  const drawer = document.querySelector('#p-topology .tdrawer'), bar = document.querySelector('#p-topology .tbar');
  const filterBar = document.querySelector('header .filters');
  const comps = document.querySelector('#p-topology .tdrawer fieldset[data-section=components]');
  const rect = e => { const b = e.getBoundingClientRect(); return {top: b.top + scrollY, bottom: b.bottom + scrollY, height: b.height}; };
  return {
    hash: location.hash, boxes, edges, svgHeight: +svg.getAttribute('height'), svgTop: rect(svg).top,
    drawer: {open: vis(drawer), rect: rect(drawer), labelGroups: [...drawer.querySelectorAll('[data-group]')].map(g => ({prefix: g.dataset.group, labels: [...g.querySelectorAll('input')].map(i => i.value)})),
      buttons: [...drawer.querySelectorAll('button[data-kind]')].map(b => ({kind: b.dataset.kind, value: b.dataset.value, pressed: b.getAttribute('aria-pressed')})),
      checked: [...drawer.querySelectorAll('input[type=checkbox]:checked')].map(i => i.value),
      ranges: drawer.querySelectorAll('input[type=range]').length},
    components: comps ? {disabled: comps.disabled, hint: (comps.querySelector('.hint') || {}).textContent || null, inputs: comps.querySelectorAll('input').length} : null,
    filtersButton: [...bar.querySelectorAll('button')].filter(b => /^Filters/.test(b.textContent)).map(b => b.textContent)[0] || null,
    filterChips: [...bar.querySelectorAll('.fc')].map(e => e.textContent),
    pinChips: [...bar.querySelectorAll('.pc')].map(e => e.textContent),
    count: (bar.querySelector('.cnt') || {}).textContent || null,
    globalFilterBarVisible: vis(filterBar),
    legendOpen: vis(document.querySelector('#p-topology .tlegend')),
    headerHeight: document.querySelector('header').offsetHeight, stripHeight: document.querySelector('#p-topology .tstrip').offsetHeight,
    legendHeight: document.querySelector('#p-topology .tlegend').offsetHeight,
  };
}

async function runStep(page, step, snaps) {
  if (step.click) await page.click(step.click);
  else if (step.clickText) {
    const [selector, text] = step.clickText;
    for (const h of await page.$$(selector)) {
      if ((await h.evaluate(e => e.textContent)).includes(text)) { await h.click(); return; }
    }
    throw new Error(`no ${selector} containing ${text}`);
  } else if (step.shiftClick) {
    const h = await page.$(`#p-topology g.tn[data-key="${step.shiftClick}"]`), bb = await h.boundingBox();
    await page.keyboard.down('Shift'); await page.mouse.click(bb.x + bb.width / 2, bb.y + bb.height / 2); await page.keyboard.up('Shift');
  } else if (step.press) await page.keyboard.press(step.press);
  else if (step.eval) await page.evaluate(step.eval);
  else if (step.reload) await page.reload();
  else if (step.shot) await page.screenshot({path: step.shot});
  else if (step.wait) await new Promise(r => setTimeout(r, step.wait));
  else if (step.snap) snaps[step.snap] = await page.evaluate(`(${pageSnapshot})()`);
  else throw new Error('unknown step ' + JSON.stringify(step));
}

(async () => {
  const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const puppeteer = require(job.puppeteer);
  const browser = await puppeteer.launch({headless: 'shell', executablePath: job.chrome, args: ['--no-sandbox']});
  const out = {};
  try {
    for (const [name, sc] of Object.entries(job.scenarios)) {
      const page = await browser.newPage(), errors = [], snaps = {};
      page.on('pageerror', e => errors.push(String(e)));
      page.on('requestfailed', r => errors.push('request failed: ' + r.url()));
      await page.setViewport({width: 1500, height: 1200});
      try {
        await page.goto(sc.url + (sc.hash || ''));
        for (const step of sc.steps) await runStep(page, step, snaps);
      } catch (e) { errors.push(String(e)); }
      out[name] = {snaps, errors};
      await page.close();
    }
  } finally { await browser.close(); }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
