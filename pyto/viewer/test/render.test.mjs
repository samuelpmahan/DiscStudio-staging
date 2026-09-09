/**
 * Render tests against a minimal document shim (no jsdom, no dependency).
 *
 * The shim's createElement returns plain objects, so the assertions walk the
 * viewer's own output tree. The load-bearing one: an `svg` value that contains
 * a <script> element is rendered through an <img> data URL, and no script node
 * exists anywhere in the produced tree.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { fromPytoRecord, fromChessLabReceipts, fromWumpusRecords } from '../adapters.js';
import {
  renderRecord, renderInvocation, renderValue, renderPartIndex,
  matchesFilter, filterTicks, searchTerms, svgDataUrl, toBase64
} from '../tick-viewer.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = (name) => JSON.parse(readFileSync(resolve(HERE, '..', 'fixtures', name), 'utf8'));
// The real record pyto.materialize wrote (fixtures/pyto-grouped-ablation.json is
// that file byte for byte; adapters.test.mjs pins the copy). Its values are all
// `json`, so the four other value kinds are rendered from the synthetic
// pyto-value-kinds.json, which exists for exactly that.
const record = fromPytoRecord(fixture('pyto-grouped-ablation.json'));
const kindsRecord = fromPytoRecord(fixture('pyto-value-kinds.json'));

/* ---------------------------------------------------------------- */
/* the shim                                                          */
/* ---------------------------------------------------------------- */

function createStubDocument() {
  return {
    createElement(tagName) {
      return {
        tagName: String(tagName).toLowerCase(),
        className: '',
        textContent: '',
        attributes: Object.create(null),
        children: [],
        appendChild(child) {
          this.children.push(child);
          return child;
        },
        setAttribute(name, value) {
          this.attributes[name] = String(value);
        },
        getAttribute(name) {
          return name in this.attributes ? this.attributes[name] : null;
        }
      };
    }
  };
}

function* walk(node) {
  yield node;
  for (const child of node.children) yield* walk(child);
}

const all = (root, tagName) => [...walk(root)].filter((node) => node.tagName === tagName);
const withClass = (root, className) => [...walk(root)].filter((node) => String(node.className).split(/\s+/).includes(className));
const textOf = (node) => [...walk(node)].map((n) => n.textContent).join(' ');

const doc = createStubDocument();
const byIdIn = (rec, id) => rec.ticks.flatMap((tick) => tick.invocations).find((invocation) => invocation.id === id);

/* ---------------------------------------------------------------- */
/* structure                                                         */
/* ---------------------------------------------------------------- */

test('the real record renders as four Tick sections and fifteen invocation rows', () => {
  // Literal, not derived from the record: run-1 is 4 Ticks and 15 invocations
  // (Prepare 2, Fit 6, Score 6, Compare 1), so a record that quietly shrank
  // would fail here instead of agreeing with itself.
  const root = renderRecord(record, { doc });
  const ticks = withClass(root, 'tick');
  assert.deepEqual(ticks.map((section) => withClass(section, 'tick-name')[0].textContent), ['Prepare', 'Fit', 'Score', 'Compare']);
  assert.deepEqual(ticks.map((section) => withClass(section, 'inv').length), [2, 6, 6, 1]);
  assert.equal(withClass(root, 'inv').length, 15);
  assert.equal(all(root, 'script').length, 0, 'a rendered record never produces a script node');
});

test('one section per Tick, in order, with index, name and invocation count', () => {
  const root = renderRecord(record, { doc });
  const ticks = withClass(root, 'tick');
  assert.equal(ticks.length, record.ticks.length);
  ticks.forEach((section, index) => {
    assert.equal(section.getAttribute('data-tick'), String(index));
    assert.equal(withClass(section, 'tick-index')[0].textContent, String(index));
    assert.equal(withClass(section, 'tick-name')[0].textContent, record.ticks[index].name);
    assert.equal(withClass(section, 'inv').length, record.ticks[index].invocations.length);
    assert.match(withClass(section, 'tick-meta')[0].textContent, /\d+ invocations? · /);
  });
  assert.equal(withClass(root, 'inv').length, record.counters.invocations);
});

test('an invocation row carries id, address, short implementation hash, pill, duration and digest', () => {
  const invocation = record.ticks[0].invocations[1];
  const row = renderInvocation(doc, invocation);
  assert.equal(row.getAttribute('data-invocation'), 'split');
  assert.equal(withClass(row, 'inv-id')[0].textContent, 'split');
  assert.equal(withClass(row, 'inv-call')[0].textContent, 'fn.ablation.split');
  const impl = withClass(row, 'impl')[0];
  assert.equal(impl.textContent, `impl ${invocation.calculation.implementation_sha256.slice(0, 12)}…`);
  assert.equal(impl.getAttribute('title'), invocation.calculation.implementation_sha256, 'the full hash stays reachable');
  assert.equal(withClass(row, 'pill')[0].textContent, 'hit');
  assert.match(withClass(row, 'dur')[0].textContent, /^0\.0\d+ ms$/);
  const digest = withClass(row, 'digest')[0];
  assert.equal(digest.textContent, `${invocation.result_sha256.slice(0, 16)}…`);
  assert.equal(digest.getAttribute('title'), invocation.result_sha256);
  assert.ok(textOf(row).includes('scratch.ablation.split'), 'the into address is shown');
});

test('hit and computed pills follow the record, never the renderer', () => {
  const root = renderRecord(record, { doc });
  const pills = withClass(root, 'pill').map((node) => node.textContent);
  assert.equal(pills.filter((p) => p === 'hit').length, record.counters.hits);
  assert.equal(pills.filter((p) => p === 'computed').length, record.counters.computed);
});

test('reads show declared beside actual and highlight a divergence', () => {
  const chess = fromChessLabReceipts(fixture('chesslab-s0-s1.json').receipts);
  const s1 = chess.ticks[1].invocations[0];
  const row = renderInvocation(doc, s1);
  const diverging = withClass(row, 'diverges');
  assert.equal(diverging.length, 1, 'exactly the undeclared read is flagged');
  assert.ok(textOf(diverging[0]).includes('px.chess.frame'));
  assert.ok(textOf(diverging[0]).includes('read, never declared'));

  // The declared-and-read address is present and not flagged.
  const readsTable = withClass(row, 'reads-table')[0];
  const rows = all(readsTable, 'tr').filter((tr) => textOf(tr).includes('px.chess.objects'));
  assert.equal(rows.length, 1);
  assert.equal(rows[0].className, '');
});

test('a fn: binding is shown as an earlier invocation result, not as a store read', () => {
  const fit = record.ticks[1].invocations[0];
  const row = renderInvocation(doc, fit);
  const resultRefs = withClass(row, 'resultref');
  assert.equal(resultRefs.length, 1);
  assert.ok(textOf(resultRefs[0]).includes('fn:split'));
  assert.ok(textOf(resultRefs[0]).includes('result of split'));
});

test('writes carry their kind', () => {
  const row = renderInvocation(doc, record.ticks[0].invocations[0]);
  const kinds = withClass(row, 'kind');
  assert.equal(kinds.length, 1);
  assert.equal(kinds[0].textContent, 'new-address');
  assert.ok(String(kinds[0].className).includes('kind-new-address'));
});

test('an invocation that records no writes says so instead of rendering an empty list', () => {
  const bare = {
    ...record.ticks[0].invocations[0],
    id: 'nothing', inputs: {}, declared_consumes: [], actual_consumes: [], actual_produces: [], writes: [], into: null
  };
  const row = renderInvocation(doc, bare);
  const notes = withClass(row, 'none').map((n) => n.textContent);
  assert.deepEqual(notes, ['reads nothing off the store', 'wrote nothing']);
});

/* ---------------------------------------------------------------- */
/* the value as material                                             */
/* ---------------------------------------------------------------- */

test('an svg value containing <script> renders as an <img> data URL and creates no script node', () => {
  const hostile = '<svg xmlns="http://www.w3.org/2000/svg"><script>globalThis.PWNED = 1;</script><rect width="10" height="10"/></svg>';
  const box = renderValue(doc, { kind: 'svg', data: hostile, note: null });

  assert.equal(all(box, 'script').length, 0, 'no script element anywhere in the tree');
  assert.equal(all(box, 'svg').length, 0, 'the markup is never inlined as elements');
  const images = all(box, 'img');
  assert.equal(images.length, 1);
  const src = images[0].getAttribute('src');
  assert.ok(src.startsWith('data:image/svg+xml;base64,'), src.slice(0, 40));
  assert.equal(images[0].getAttribute('alt'), 'SVG Part value');

  // The bytes survive the round trip: the viewer neither executes nor edits them.
  const decoded = Buffer.from(src.slice('data:image/svg+xml;base64,'.length), 'base64').toString('utf8');
  assert.equal(decoded, hostile);

  // The raw markup appears nowhere as text either.
  assert.ok(!textOf(box).includes('<script>'), 'the markup is not written into any textContent');
  assert.equal(globalThis.PWNED, undefined);
});

test('a whole record whose Parts are hostile SVG still produces no script node', () => {
  const hostile = structuredClone(record);
  for (const tick of hostile.ticks) {
    for (const invocation of tick.invocations) {
      invocation.value = { kind: 'svg', data: '<svg xmlns="http://www.w3.org/2000/svg" onload="globalThis.PWNED = 1"><script>globalThis.PWNED = 1;</script></svg>', note: null };
    }
  }
  const root = renderRecord(hostile, { doc });
  assert.equal(all(root, 'script').length, 0);
  assert.equal(all(root, 'img').length, hostile.counters.invocations);
  for (const img of all(root, 'img')) assert.ok(img.getAttribute('src').startsWith('data:image/svg+xml;base64,'));
});

test('json is collapsible, text is a pre, png-data-url is an img, omitted is the note', () => {
  const json = renderValue(doc, { kind: 'json', data: { a: [1, 2] }, note: null });
  assert.equal(all(json, 'details').length, 1);
  assert.match(all(json, 'summary')[0].textContent, /^json · \d+ lines$/);
  assert.equal(all(json, 'pre')[0].textContent, JSON.stringify({ a: [1, 2] }, null, 2));

  const text = renderValue(doc, { kind: 'text', data: 'two\nlines', note: null });
  assert.equal(all(text, 'pre').length, 1);
  assert.equal(all(text, 'pre')[0].textContent, 'two\nlines');
  assert.equal(all(text, 'details').length, 0);

  const png = 'data:image/png;base64,iVBORw0KGgo=';
  const image = renderValue(doc, { kind: 'png-data-url', data: png, note: null });
  assert.equal(all(image, 'img')[0].getAttribute('src'), png);

  const omitted = renderValue(doc, { kind: 'omitted', data: null, note: 'over the cap' });
  assert.equal(all(omitted, 'img').length, 0);
  assert.equal(withClass(omitted, 'omitted')[0].textContent, 'over the cap');
});

test('a png-data-url that is not a PNG data URL never reaches an <img src>', () => {
  // The record is data, and <img src> is a fetch. RECORD.md:109-110 fixes the
  // shape; adapters.js refuses anything else, and the render site re-checks so
  // a record that reached the DOM by some other path still makes no request
  // from a page whose premise is that it makes none.
  for (const data of ['https://evil.example/beacon.gif?record=opened', 'javascript:alert(1)//', 'data:image/svg+xml,<svg/>']) {
    const box = renderValue(doc, { kind: 'png-data-url', data, note: null });
    assert.equal(all(box, 'img').length, 0, `an <img> was created for ${data}`);
    assert.equal(all(box, 'figure').length, 0);
    const refused = withClass(box, 'omitted');
    assert.equal(refused.length, 1);
    assert.match(refused[0].textContent, /must be a data:image\/png;base64,\.\.\. string/);
    assert.ok(!textOf(box).includes('evil.example'), 'the rejected URL is not echoed into the page');
  }
  // And a whole record of them never gets as far as the renderer: renderRecord
  // validates first, so the fallback above is the second line, not the only one.
  const hostile = structuredClone(record);
  for (const tick of hostile.ticks) {
    for (const invocation of tick.invocations) {
      invocation.value = { kind: 'png-data-url', data: 'https://evil.example/beacon.gif', note: null };
    }
  }
  assert.throws(() => renderRecord(hostile, { doc }), /value\.data: expected a string beginning/);
});

test('a note is rendered beside the material it qualifies', () => {
  const box = renderValue(doc, { kind: 'text', data: 'x', note: 'array truncated: showing the first 200 of 255 entries' });
  const notes = withClass(box, 'note').map((n) => n.textContent);
  assert.deepEqual(notes, ['array truncated: showing the first 200 of 255 entries']);
});

test('toBase64 and svgDataUrl survive non-Latin1 text', () => {
  const text = '<svg xmlns="http://www.w3.org/2000/svg"><title>🥏 étoile</title></svg>';
  assert.equal(Buffer.from(toBase64(text), 'base64').toString('utf8'), text);
  assert.ok(svgDataUrl(text).startsWith('data:image/svg+xml;base64,'));
});

/* ---------------------------------------------------------------- */
/* filter                                                            */
/* ---------------------------------------------------------------- */

test('an empty filter keeps every row', () => {
  assert.equal(filterTicks(record.ticks, '').length, record.ticks.length);
  assert.equal(filterTicks(record.ticks, '   ').flatMap((t) => t.invocations).length, record.counters.invocations);
});

test('a substring filter narrows rows to the matching addresses', () => {
  // `compare` reads every score Part, so a substring filter finds the readers
  // of an address as well as its writer -- across Ticks.
  const kept = filterTicks(record.ticks, 'score');
  const ids = kept.flatMap((tick) => tick.invocations.map((i) => i.id));
  assert.deepEqual(ids, ['score.all', 'score.drop_g0', 'score.drop_g1', 'score.drop_g2', 'score.drop_g3', 'score.drop_g4', 'compare']);
  assert.deepEqual(kept.map((tick) => tick.name), ['Score', 'Compare']);
  // Prepare and Fit have no surviving invocation and are dropped entirely.
  assert.equal(kept.length, 2, 'ticks with no surviving invocation are dropped');

  // The reach of the filter is exactly what the invocation spells. `compare`
  // binds `fn:score.drop_g3`, never the address, and its actual_consumes is
  // empty because a fn: result never touches the store -- so the full address
  // finds the writer only, even though the Part index (derived through the fn:
  // ref) lists `compare` as a reader of it. The filter reports the testimony;
  // the Part index reports the resolution.
  assert.deepEqual(filterTicks(record.ticks, 'scratch.ablation.score.drop_g3').flatMap((t) => t.invocations.map((i) => i.id)), ['score.drop_g3']);
  assert.deepEqual(record.parts['scratch.ablation.score.drop_g3'].read_by, ['compare']);
  assert.deepEqual(byIdIn(record, 'compare').actual_consumes, []);
});

test('a trailing * filters by address prefix, the way PQL.prefix describes itself', () => {
  const fits = ['fit.all', 'fit.drop_g0', 'fit.drop_g1', 'fit.drop_g2', 'fit.drop_g3', 'fit.drop_g4'];
  const kept = filterTicks(record.ticks, 'scratch.ablation.model.*');
  const ids = kept.flatMap((tick) => tick.invocations.map((i) => i.id));
  assert.deepEqual(ids, fits);
  assert.equal(kept.length, 1, 'only the Fit Tick survives');

  // The same text without the star is a substring match, so it also finds the
  // score invocations that read those models by fn: ref -- and it must not.
  assert.deepEqual(filterTicks(record.ticks, 'scratch.ablation.model').flatMap((t) => t.invocations.map((i) => i.id)), fits);
  // A prefix that matches nothing keeps nothing.
  assert.deepEqual(filterTicks(record.ticks, 'scratch.ablation.model.*x'), []);
});

test('the filter matches calculation addresses and tick names too, case-insensitively', () => {
  assert.deepEqual(filterTicks(record.ticks, 'fn.ablation.fit').flatMap((t) => t.invocations.map((i) => i.id)),
    ['fit.all', 'fit.drop_g0', 'fit.drop_g1', 'fit.drop_g2', 'fit.drop_g3', 'fit.drop_g4']);
  assert.deepEqual(filterTicks(record.ticks, 'COMPARE').flatMap((t) => t.invocations.map((i) => i.id)), ['compare']);
  assert.deepEqual(filterTicks(kindsRecord.ticks, 'MATERIALIZE').flatMap((t) => t.invocations.map((i) => i.id)), ['sheet', 'snapshot']);
  const wumpus = fromWumpusRecords(fixture('wumpus-belief-tick.json').records);
  assert.deepEqual(filterTicks(wumpus.ticks, 'px.agent.belief').flatMap((t) => t.invocations.map((i) => i.id)), ['tick-2', 'tick-3']);
});

test('matchesFilter and searchTerms agree on what an invocation can be found by', () => {
  const split = record.ticks[0].invocations[1];
  const terms = searchTerms(split, 'Prepare');
  assert.ok(terms.includes('split'));
  assert.ok(terms.includes('fn.ablation.split'));
  assert.ok(terms.includes('input.ablation.rows'));
  assert.ok(terms.includes('px:input.ablation.rows'));
  assert.ok(terms.includes('scratch.ablation.split'));
  assert.ok(terms.includes('Prepare'));
  for (const term of terms) assert.equal(matchesFilter(split, term, 'Prepare'), true, term);
  assert.equal(matchesFilter(split, 'nothing-like-this', 'Prepare'), false);
});

test('renderRecord reports what the filter narrowed and says so when nothing matches', () => {
  const narrowed = renderRecord(record, { doc, filter: 'fn.ablation.score' });
  assert.equal(withClass(narrowed, 'inv').length, 6);
  assert.equal(withClass(narrowed, 'tick').length, 1);
  assert.match(withClass(narrowed, 'filtered')[0].textContent, /filter "fn\.ablation\.score": 6 of 15 invocations, 1 of 4 ticks/);

  const empty = renderRecord(record, { doc, filter: 'zzz' });
  assert.equal(withClass(empty, 'tick').length, 0);
  assert.match(withClass(empty, 'none')[0].textContent, /no invocation matches "zzz"/);
  assert.equal(withClass(empty, 'parts').length, 1, 'the Part index stays available');
});

/* ---------------------------------------------------------------- */
/* header and Part index                                             */
/* ---------------------------------------------------------------- */

test('the header shows pcr, source and counters', () => {
  const root = renderRecord(record, { doc });
  const head = withClass(root, 'record-head')[0];
  assert.equal(all(head, 'h1')[0].textContent, 'ablation.grouped');
  assert.ok(withClass(head, 'source')[0].textContent.startsWith('pyto 0.1.0 · '));
  const counters = withClass(head, 'counters')[0].children.map((li) => li.children.map((s) => s.textContent));
  assert.deepEqual(counters.map((c) => c[1]), ['invocations', 'hits', 'computed', 'wall', 'ticks']);
  assert.deepEqual(counters.map((c) => c[0]).slice(0, 3), ['15', '2', '13']);
  assert.equal(counters[4][0], '4');
});

test('the Part index lists every address with its writer, readers and preexisting flag', () => {
  const section = renderPartIndex(doc, record.parts);
  const rows = all(section, 'tbody')[0].children;
  assert.equal(rows.length, Object.keys(record.parts).length);
  const addresses = rows.map((tr) => tr.children[0].textContent);
  assert.deepEqual(addresses, [...addresses].sort(), 'sorted by address');

  const rowFor = (address) => rows.find((tr) => tr.children[0].textContent === address).children.map((td) => td.textContent);
  assert.deepEqual(rowFor('input.ablation.rows'), ['input.ablation.rows', '—', 'split', 'yes']);
  // Written, never read: the em dash says so rather than the address vanishing.
  assert.deepEqual(rowFor('scratch.ablation.comparison'), ['scratch.ablation.comparison', 'compare', '—', 'no']);
  assert.deepEqual(rowFor('scratch.ablation.model.drop_g2'), ['scratch.ablation.model.drop_g2', 'fit.drop_g2', 'score.drop_g2', 'no']);
  assert.equal(rows.find((tr) => tr.children[0].textContent === 'input.ablation.rows').className, 'preexisting');
});

test('an empty Part index says so', () => {
  const section = renderPartIndex(doc, {});
  assert.equal(all(section, 'table').length, 0);
  assert.equal(withClass(section, 'none')[0].textContent, 'no Parts recorded');
});

test('renderRecord validates before it renders', () => {
  const broken = structuredClone(record);
  broken.ticks[0].invocations[0].hit = 'yes';
  assert.throws(() => renderRecord(broken, { doc }), /ticks\[0\]\.invocations\[0\]\.hit/);
});
