/* Bake a town layout with the map editor's own code (bakeTown + townData), so every pixel is the game's art.

   node tools/voltmark_bake.js <dir>     (needs <dir>/vm_layout.json and a local server on :8765 serving the repo)
   -> sprites/overworld/maps/a12_v3_lower.png, a12_v3_upper.png and <dir>/vm_town.json */
const fs = require('fs'), path = require('path');
const { chromium } = require(process.env.PW || 'playwright-core');
const DIR = process.argv[2], ROOT = path.resolve(__dirname, '..');
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  /* bakeTown/townData live inside the editor's indoor-mode wrapper; expose them for this run only */
  await p.route('**/map_editor.html', async r => {
    let html = fs.readFileSync(path.join(ROOT, 'map_editor.html'), 'utf8');
    html = html.replace('function bakeTown(){', 'window.__bake={bakeTown,townData};function bakeTown(){');
    await r.fulfill({ status: 200, contentType: 'text/html', body: html });
  });
  await p.goto('http://localhost:8765/map_editor.html'); await p.waitForTimeout(3000);
  await p.waitForFunction(() => typeof IMG !== 'undefined' && IMG.kits && IMG.kits.complete && IMG.tiles_all && IMG.tiles_all.complete, null, { timeout: 60000 });
  const L = JSON.parse(fs.readFileSync(path.join(DIR, 'vm_layout.json'), 'utf8'));
  const out = await p.evaluate(L => {
    /* Goldenrod's learned road rules also list a few plaza tiles from the generic set (ids < 2000); keep roads to road tiles */
    const R = V.styles[L.style].rules;
    for (const k of Object.keys(R)) if (k.startsWith('R|')) { const keep = R[k].filter(([t]) => t >= 2000); if (keep.length) R[k] = keep; else delete R[k] }
    if (typeof groundKey !== 'undefined') groundKey = '';
    M = L; const [lo, up] = __bake.bakeTown(); const [D, notes] = __bake.townData(); return { lo, up, D, notes } }, L);
  const save = (u, f) => fs.writeFileSync(f, Buffer.from(u.split(',')[1], 'base64'));
  save(out.lo, path.join(ROOT, 'sprites/overworld/maps/a12_v3_lower.png'));
  save(out.up, path.join(ROOT, 'sprites/overworld/maps/a12_v3_upper.png'));
  /* people must stand somewhere you can walk to (from the west road): move any that landed under a building */
  { const D = out.D, C = D.coll, seen = new Set(['0,18']), q = [[0, 18]];
    while (q.length) { const [x, y] = q.shift(); for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const a = x + dx, c = y + dy, k = a + ',' + c;
      if (a >= 0 && c >= 0 && a < D.w && c < D.h && !seen.has(k) && C[c][a] === '0') { seen.add(k); q.push([a, c]) } } }
    const fronts = new Set(Object.values(D.doors).map(([x, y]) => x + ',' + (y + 1))), taken = new Set();
    for (const n of D.npcs) { let k = n.x + ',' + n.y;
      if (!seen.has(k) || fronts.has(k) || taken.has(k)) { const c = [...seen].filter(t => !fronts.has(t) && !taken.has(t)).map(t => t.split(',').map(Number)).sort((a, b) => (Math.abs(a[0] - n.x) + Math.abs(a[1] - n.y)) - (Math.abs(b[0] - n.x) + Math.abs(b[1] - n.y)))[0];
        console.log('moved', n.sheet || n.builtin, [n.x, n.y], '->', c); n.x = c[0]; n.y = c[1]; k = c.join(',') }
      taken.add(k) }
    const adj = (x, y) => [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => seen.has((x + dx) + ',' + (y + dy)));
    for (const s of D.signs) if (!adj(s.x, s.y)) console.log('SIGN NOT REACHABLE', s.lines[0], s.x, s.y);
    for (const [k, [x, y]] of Object.entries(D.doors)) if (!seen.has(x + ',' + (y + 1))) console.log('DOOR NOT REACHABLE', k);
    console.log('east exit reachable', seen.has((D.w - 1) + ',18')) }
  const town = { kind: 'town', area: 12, name: 'Voltmark', builtin: true, map: out.D,
    lower: 'sprites/overworld/maps/a12_v3_lower.png', upper: 'sprites/overworld/maps/a12_v3_upper.png' };
  fs.writeFileSync(path.join(DIR, 'vm_town.json'), JSON.stringify(town));
  console.log('baked', out.D.w, out.D.h, 'notes:', out.notes, 'errors:', errs);
  await b.close();
})();
