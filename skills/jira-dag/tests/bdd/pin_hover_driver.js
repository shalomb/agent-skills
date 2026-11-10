// Drives the Topologies page in headless Chrome and records DOM snapshots. Observation only: assertions live in Python.
// Usage: node pin_hover_driver.js <job.json>   job = {puppeteer, chrome, url, scenarios: {name: {hash, steps: [...]}}}
// Prints {scenario: {snaps: {label: snapshot}, errors: [..]}} as JSON on stdout.
const fs = require('fs');

// Runs inside the page. Reads the state the scenarios assert on; changes nothing.
function pageSnapshot() {
  const svg = document.querySelector('#p-topology > svg');
  const shift = el => {
    const m = (el.getAttribute('transform') || '').match(/translate\(\s*(-?[\d.e+-]+)[ ,]+(-?[\d.e+-]+)\s*\)/);
    return m ? [+m[1], +m[2]] : [0, 0];
  };
  const boxes = {};
  svg.querySelectorAll('g.tn').forEach(g => {
    const r = g.querySelector('rect'), t = shift(g);
    boxes[g.dataset.key] = {
      shown: g.style.display !== 'none', dim: g.classList.contains('dim'),
      pos: [+r.getAttribute('x') + t[0], +r.getAttribute('y') + t[1]], opacity: +getComputedStyle(g).opacity,
    };
  });
  const edges = {};
  svg.querySelectorAll('path[data-edge]').forEach(p => {
    edges[p.dataset.edge] = {shown: p.style.display !== 'none', dim: p.classList.contains('dim'), d: p.getAttribute('d'), opacity: +getComputedStyle(p).opacity};
  });
  const bands = {};
  svg.querySelectorAll('[data-band]').forEach(e => {
    const b = bands[e.dataset.band] = bands[e.dataset.band] || {hidden: true, top: null};
    if (e.style.display !== 'none') b.hidden = false;
    if (e.classList.contains('bf')) b.top = +e.getAttribute('y') + shift(e)[1];
  });
  const bar = document.querySelector('#p-topology .tbar');
  const card = document.getElementById('card'), pinb = card.querySelector('.pinb');
  return {
    hash: location.hash, boxes, edges, bands,
    svgHeight: +svg.getAttribute('height'), viewBox: svg.getAttribute('viewBox'),
    bar: bar ? bar.textContent : null,
    chips: bar ? [...bar.querySelectorAll('.pc')].map(e => e.textContent) : [],
    buttons: bar ? [...bar.querySelectorAll('button')].map(b => ({text: b.textContent, on: b.classList.contains('on')})) : [],
    card: {visible: card.style.display === 'block', title: card.querySelector('h2') ? card.querySelector('h2').textContent : null, pinText: pinb ? pinb.textContent : null},
  };
}

async function center(page, selector) {
  const h = await page.$(selector);
  if (!h) throw new Error('no element ' + selector);
  const bb = await h.boundingBox();
  if (!bb) throw new Error('element not rendered ' + selector);
  return {x: bb.x + bb.width / 2, y: bb.y + bb.height / 2};
}
const boxSel = k => `#p-topology g.tn[data-key="${k}"]`;

async function runStep(page, step, snaps) {
  if (step.hover) { const c = await center(page, boxSel(step.hover)); await page.mouse.move(c.x, c.y); }
  else if (step.leave) await page.mouse.move(1490, 1190);
  else if (step.click) { const c = await center(page, boxSel(step.click)); await page.mouse.click(c.x, c.y); }
  else if (step.shiftClick) {
    const c = await center(page, boxSel(step.shiftClick));
    await page.keyboard.down('Shift'); await page.mouse.click(c.x, c.y); await page.keyboard.up('Shift');
  } else if (step.clickText) {
    const [selector, text] = step.clickText;
    for (const h of await page.$$(selector)) {
      if ((await h.evaluate(e => e.textContent)).includes(text)) { await h.click(); return; }
    }
    throw new Error(`no ${selector} containing ${text}`);
  } else if (step.press) await page.keyboard.press(step.press);
  else if (step.eval) await page.evaluate(step.eval);
  else if (step.evalSnap) snaps[step.label] = await page.evaluate(`(()=>{${step.evalSnap};return (${pageSnapshot})()})()`);  // action and snapshot in one task, before the browser can re-hover
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
        await page.goto(job.url + (sc.hash || ''));
        for (const step of sc.steps) await runStep(page, step, snaps);
      } catch (e) { errors.push(String(e)); }
      out[name] = {snaps, errors};
      await page.close();
    }
  } finally { await browser.close(); }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(1); });
