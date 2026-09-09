#!/usr/bin/env node
// Verify a JS port of the disc-art painter and the two promoted card renderers against the
// Python-produced fixtures. Dependency-free. Exit 0 only when every case is byte-identical.
//
//   node verify_port.mjs ./painter.mjs            # families only
//   node verify_port.mjs ./painter.mjs ./cards.mjs # families and cards
//
// painter.mjs must export: render(family, seed, base, accent, target, label) -> string (SVG text)
// cards.mjs must export:   renderSingle(card, art, width) -> string, renderBattle(card, art, width) -> string
// Byte-identical means: sha256 over the UTF-8 bytes of the returned string equals the fixture's.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const sha = (s) => createHash('sha256').update(Buffer.from(s, 'utf8')).digest('hex');
const firstDiff = (a, b) => { let i = 0; while (i < a.length && i < b.length && a[i] === b[i]) i++; return { at: i, expected: a.slice(Math.max(0, i - 40), i + 80), actual: b.slice(Math.max(0, i - 40), i + 80) }; };

const [painterPath, cardsPath] = process.argv.slice(2);
if (!painterPath) { console.error('usage: node verify_port.mjs ./painter.mjs [./cards.mjs]'); process.exit(2); }
const painter = await import(pathToFileURL(painterPath).href);
if (typeof painter.render !== 'function') { console.error('painter.mjs must export render(family, seed, base, accent, target, label)'); process.exit(2); }

const fam = JSON.parse(readFileSync(join(here, 'fixtures', 'expected.json'), 'utf8'));
const t0 = performance.now();
let pass = 0, fail = 0; const failures = [];
for (const c of fam.cases) {
  let out;
  try { out = painter.render(c.family, c.seed, c.base, c.accent, c.target, c.label); } catch (e) { fail++; failures.push({ case: `${c.family} ${c.seed} ${c.base} ${c.target}`, error: String(e) }); continue; }
  if (typeof out === 'string' && sha(out) === c.sha256) pass++; else { fail++; failures.push({ case: `${c.family} seed=${c.seed} base=${c.base} target=${c.target}`, diff: typeof out === 'string' ? firstDiff(c.svg, out) : { error: 'not a string' } }); }
}
const perFamily = {};
for (const c of fam.cases) { perFamily[c.family] ??= { total: 0, ok: 0 }; perFamily[c.family].total++; }
for (const f of failures) { const key = f.case.split(' ')[0]; if (perFamily[key]) perFamily[key].failed = (perFamily[key].failed || 0) + 1; }
console.log(`families: ${pass}/${fam.cases.length} byte-identical in ${(performance.now() - t0).toFixed(0)} ms`);
for (const [k, v] of Object.entries(perFamily)) console.log(`  ${k.padEnd(20)} ${String(v.total - (v.failed || 0)).padStart(3)}/${v.total}`);

let cpass = 0, cfail = 0;
if (cardsPath) {
  const cards = await import(pathToFileURL(cardsPath).href);
  const cf = JSON.parse(readFileSync(join(here, 'fixtures', 'expected-cards.json'), 'utf8'));
  for (const c of cf.cases) {
    const fn = c.renderer === 'single' ? cards.renderSingle : cards.renderBattle;
    let out;
    try { out = fn(c.card, c.art, c.width); } catch (e) { cfail++; failures.push({ case: `card ${c.renderer} ${c.card_name} ${c.width}`, error: String(e) }); continue; }
    if (typeof out === 'string' && sha(out) === c.sha256) cpass++; else { cfail++; failures.push({ case: `card ${c.renderer} ${c.card_name} ${c.width}`, diff: typeof out === 'string' ? firstDiff(c.svg, out) : { error: 'not a string' } }); }
  }
  console.log(`cards: ${cpass}/${cf.cases.length} byte-identical`);
}
for (const f of failures.slice(0, 10)) console.log('FAIL', JSON.stringify(f));
if (failures.length > 10) console.log(`... ${failures.length - 10} more failures`);
process.exit(fail + cfail === 0 ? 0 : 1);
