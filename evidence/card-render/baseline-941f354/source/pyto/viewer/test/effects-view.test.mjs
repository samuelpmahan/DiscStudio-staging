/**
 * Effects you can see: an invocation card lists what its Calculation did outside
 * the store -- one row per effect, with the kind, the path or a one-line arg
 * summary, and the digest of the result -- and an OperationalCalculation (an
 * `oc.` address) is drawn distinctly. The contract is rendered when the record
 * carries it and never required: a record with no `effects` key at all renders
 * byte for byte the tree it rendered before this file existed.
 *
 * The assertions are on the rendered tree and on exact printed text, against the
 * same minimal document shim the other render tests use (no jsdom, no dependency).
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { fromPytoRecord } from '../adapters.js';
import {
  renderRecord, renderInvocation, renderEffects,
  effectSummary, invocationEffects, isOperationalCalculation
} from '../tick-viewer.js';
import { buildPage } from '../embed.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const VIEWER = resolve(HERE, '..');
const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

// Hand-made, and the only record here carrying the effects contract: one `oc.`
// invocation with three effects, one `fn.` invocation with an empty list.
const demo = fromPytoRecord(readJson(resolve(VIEWER, 'fixtures', 'effects-demo.json')));
// The record the students homework actually wrote, from before effects existed:
// no invocation carries an `effects` key at all.
const STUDENTS = resolve(VIEWER, '..', 'experiments', 'students', 'evidence', 'run-1', 'record.json');
const students = fromPytoRecord(readJson(STUDENTS));

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

const withClass = (root, className) => [...walk(root)].filter((node) => String(node.className).split(/\s+/).includes(className));
const doc = createStubDocument();

/**
 * One rendered tree as one string: tag, classes, attributes (sorted) and text,
 * one node per line, indented by depth. Two trees are equal exactly when their
 * two strings are, which is what the byte-for-byte assertions below compare.
 */
function serialize(node, depth = 0) {
  const pad = '  '.repeat(depth);
  const attrs = Object.keys(node.attributes).sort().map((k) => `${k}=${JSON.stringify(node.attributes[k])}`).join(' ');
  const head = [
    node.tagName,
    node.className ? `class=${JSON.stringify(node.className)}` : '',
    attrs,
    node.textContent ? `text=${JSON.stringify(node.textContent)}` : ''
  ].filter(Boolean).join(' ');
  return [pad + head, ...node.children.map((child) => serialize(child, depth + 1))].join('\n');
}

/** The invocation cards of a tree, in render order. */
const cardsOf = (root) => withClass(root, 'inv');
/** The effect rows of one card, in record order. */
const rowsOf = (card) => withClass(card, 'effect');
const cellText = (row, className) => withClass(row, className)[0].textContent;

/* ---------------------------------------------------------------- */
/* (a) the fixture: three rows on the oc card, nothing on the fn one  */
/* ---------------------------------------------------------------- */

test('the effects-demo record draws three effect rows on its oc card, with the kinds, the paths and the digests it carries', () => {
  const root = renderRecord(demo, { doc });
  const [oc, fn] = cardsOf(root);
  assert.equal(oc.getAttribute('data-invocation'), 'read.roster');
  assert.equal(fn.getAttribute('data-invocation'), 'count');

  const rows = rowsOf(oc);
  assert.equal(rows.length, 3, 'one row per recorded effect');
  assert.deepEqual(rows.map((row) => row.getAttribute('data-effect')), ['0', '1', '2']);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-index')), ['0', '1', '2']);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-kind')), ['read_text', 'env', 'write_text']);

  // The path when the effect names one; `name=value` over the args when it does not.
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-arg')), [
    '/tmp/effects-demo/roster.csv',
    'name="PYTO_SEED"',
    '/tmp/effects-demo/roster.copy.csv'
  ]);

  // The first twelve hex of each digest, with the whole digest on the title so
  // nothing is lost: the rows are a witness, not a summary.
  const digests = demo.ticks[0].invocations[0].effects.map((effect) => effect.result_sha256);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-digest')), digests.map((hex) => `${hex.slice(0, 12)}…`));
  assert.deepEqual(rows.map((row) => withClass(row, 'effect-digest')[0].getAttribute('title')), digests);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-digest').length), [13, 13, 13]);

  // The heading, once, above the list, and the list says how many rows it holds.
  assert.deepEqual(withClass(oc, 'effects-head').map((h) => h.textContent), ['effects']);
  assert.equal(withClass(oc, 'effect-list')[0].getAttribute('data-effects'), '3');
  assert.equal(withClass(oc, 'effect-list')[0].tagName, 'ol', 'an ordered list: the order is the order they happened');

  // The oc card is drawn distinctly, and carries the chip.
  assert.ok(String(oc.className).split(/\s+/).includes('oc'), 'the oc card is marked');
  assert.deepEqual(withClass(oc, 'pill').map((p) => p.textContent), ['oc', 'computed']);
  assert.equal(isOperationalCalculation(demo.ticks[0].invocations[0]), true);

  // `effects: []` on a pure fn. Calculation shows nothing extra at all.
  assert.equal(rowsOf(fn).length, 0);
  assert.equal(withClass(fn, 'effects').length, 0, 'no wrapper');
  assert.equal(withClass(fn, 'effects-head').length, 0, 'no heading');
  assert.equal(String(fn.className), 'inv', 'no oc mark on a fn. card');
  assert.deepEqual(withClass(fn, 'pill').map((p) => p.textContent), ['computed'], 'no oc chip on a fn. card');
  assert.equal(isOperationalCalculation(demo.ticks[1].invocations[0]), false);
  assert.deepEqual(demo.ticks[1].invocations[0].effects, [], 'the fixture really does carry an empty list');
});

test('an effect the record could not digest prints no digest, and an unknown kind is shown unstyled', () => {
  const bare = structuredClone(demo);
  bare.ticks[0].invocations[0].effects = [
    { kind: 'now_ms', args: {}, result_sha256: null },
    { kind: 'sing', args: { note: 'A' }, result_sha256: '' }
  ];
  const rows = rowsOf(cardsOf(renderRecord(bare, { doc }))[0]);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-kind')), ['now_ms', 'sing']);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-arg')), ['—', 'note="A"']);
  assert.deepEqual(rows.map((row) => cellText(row, 'effect-digest')), ['—', '—'], 'a digest is never invented');
  assert.equal(withClass(rows[0], 'effect-digest')[0].getAttribute('title'), null);
  assert.equal(withClass(rows[0], 'effect-kind')[0].className, 'kind effect-kind kind-now_ms');
  assert.equal(withClass(rows[1], 'effect-kind')[0].className, 'kind effect-kind', 'a kind outside the contract gets no kind- class');

  // The summary is always one line: a long value is cut, a newline is escaped.
  assert.equal(effectSummary({ args: { text: 'a\nb' } }), 'text="a\\nb"');
  assert.equal(effectSummary({ args: { blob: 'x'.repeat(200) } }).length, 81);
  assert.equal(effectSummary({ args: null }), '—');
  assert.equal(effectSummary({}), '—');
});

test('an oc. Calculation that performed no effect is still drawn as an oc card', () => {
  const quiet = structuredClone(demo);
  quiet.ticks[0].invocations[0].effects = [];
  const [oc] = cardsOf(renderRecord(quiet, { doc }));
  assert.ok(String(oc.className).split(/\s+/).includes('oc'));
  assert.deepEqual(withClass(oc, 'pill').map((p) => p.textContent), ['oc', 'computed']);
  assert.equal(withClass(oc, 'effects').length, 0, 'the chip is about the address, the rows are about the record');
});

/* ---------------------------------------------------------------- */
/* (b) a record from before effects renders exactly as it did        */
/* ---------------------------------------------------------------- */

// Written by this same serializer against the renderer as task 40 left it, before
// any of the code above existed. It is the whole students page, 280 lines of tree.
const GOLDEN = resolve(HERE, 'students-card-tree.golden.txt');

test('the students record carries no effects key at all, and renders byte for byte what it rendered before effects existed', () => {
  for (const tick of students.ticks) {
    for (const invocation of tick.invocations) {
      assert.equal('effects' in invocation, false, `${invocation.id} carries no effects key`);
      assert.deepEqual(invocationEffects(invocation), [], 'and reads as no effects, not as a crash');
      assert.equal(isOperationalCalculation(invocation), false);
    }
  }
  const rendered = `${serialize(renderRecord(students, { doc }))}\n`;
  const golden = readFileSync(GOLDEN, 'utf8');
  assert.equal(rendered, golden, 'the tree drifted from the one task 40 landed');
  assert.equal(Buffer.compare(Buffer.from(rendered, 'utf8'), Buffer.from(golden, 'utf8')), 0);

  // Not vacuous: the golden is the students page, not an empty string, and it
  // says nothing about effects.
  assert.ok(golden.includes('class="inv"'), 'the golden holds the cards');
  assert.ok(golden.includes('students-homework'));
  assert.equal(golden.includes('effect'), false, 'nothing about effects on a record that carries none');
  assert.equal(golden.split('\n').length > 200, true);
});

/* ---------------------------------------------------------------- */
/* (c) the same record renders to the same bytes                     */
/* ---------------------------------------------------------------- */

test('rendering the effects-demo record twice is byte-identical, and rendering never mutates the record', () => {
  const before = JSON.stringify(demo);
  const first = serialize(renderRecord(demo, { doc }));
  const second = serialize(renderRecord(demo, { doc }));
  assert.equal(first, second);
  assert.equal(Buffer.compare(Buffer.from(first, 'utf8'), Buffer.from(second, 'utf8')), 0);
  assert.equal(JSON.stringify(demo), before, 'the renderer reads the record and writes nothing back');

  // A second document shim renders the same tree: nothing is carried between renders.
  assert.equal(serialize(renderRecord(demo, { doc: createStubDocument() })), first);

  // The two records differ, so the equality above is not the serializer ignoring
  // what it was handed.
  assert.notEqual(first, serialize(renderRecord(students, { doc })));
});

test('the standalone page keeps the effects the record carries and is the same bytes twice', () => {
  const page = buildPage(demo);
  assert.equal(page, buildPage(demo));
  for (const field of ['"effects"', '"read_text"', '"write_text"', '"result_sha256"', 'oc.demo.read_roster']) {
    assert.ok(page.includes(field), `the embedded record keeps ${field}`);
  }
  assert.ok(page.includes('.effect-list {'), 'the page carries the effect rows');
  assert.ok(page.includes('.inv.oc {'), 'and the oc card');
  // The page ships the renderer, not a rendering.
  assert.equal(page.includes('class="effect-list"'), false);
});

/* ---------------------------------------------------------------- */
/* (d) renderEffects on its own                                      */
/* ---------------------------------------------------------------- */

test('renderEffects returns nothing for an empty list, a missing key and a list of non-objects', () => {
  const invocation = demo.ticks[1].invocations[0];
  assert.equal(renderEffects(doc, invocation), null, 'an empty list');
  assert.equal(renderEffects(doc, { ...invocation, effects: undefined }), null, 'a missing key');
  assert.equal(renderEffects(doc, { ...invocation, effects: [null, 3, 'x'] }), null, 'nothing that is an effect');
  assert.equal(renderInvocation(doc, { ...invocation, effects: undefined }).children.length,
    renderInvocation(doc, invocation).children.length, 'and the card is the same shape either way');
});
