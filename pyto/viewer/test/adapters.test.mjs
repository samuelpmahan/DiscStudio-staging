/**
 * Every adapter output passes validate; hit derivation matches RECORD.md; a
 * schema violation throws with the path that names it.
 *
 * The DiscStudio case is checked twice: against the committed fixture and
 * against a live run of ../../../src/runtime.js, so the fixture cannot drift
 * away from the runtime it claims to come from.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import {
  SCHEMA, MAX_ARRAY_ENTRIES, MAX_VALUE_BYTES,
  validate, RecordSchemaError, materialize, deriveHit, derivePartIndex, bareAddress,
  fromPytoRecord, fromDiscStudioReceipt, fromChessLabReceipts, fromWumpusRecords
} from '../adapters.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = (name) => JSON.parse(readFileSync(resolve(HERE, '..', 'fixtures', name), 'utf8'));

const pytoDoc = fixture('pyto-grouped-ablation.json');
const dsDoc = fixture('discstudio-display-card.json');
const chessDoc = fixture('chesslab-s0-s1.json');
const wumpusDoc = fixture('wumpus-belief-tick.json');

const invocations = (record) => record.ticks.flatMap((tick) => tick.invocations);
const byId = (record, id) => invocations(record).find((invocation) => invocation.id === id);

/* ---------------------------------------------------------------- */

test('every adapter output passes validate', () => {
  const records = [
    fromPytoRecord(pytoDoc),
    fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt, { version: 'transcribed-82f8fc9' }),
    fromDiscStudioReceipt(dsDoc.second.pql, dsDoc.second.receipt),
    fromChessLabReceipts(chessDoc.receipts, { pcr: 'chesslab.debugger' }),
    fromWumpusRecords(wumpusDoc.records, { pcr: 'wumpus.belief' })
  ];
  for (const record of records) {
    assert.equal(validate(record), record);
    assert.equal(record.schema, SCHEMA);
    record.ticks.forEach((tick, index) => assert.equal(tick.index, index));
  }
  assert.deepEqual(records.map((r) => r.source.runtime), ['pyto', 'discstudio', 'discstudio', 'chesslab', 'wumpus']);
});

test('fromPytoRecord is a validating pass-through, from an object or a string', () => {
  const fromObject = fromPytoRecord(pytoDoc);
  const fromText = fromPytoRecord(JSON.stringify(pytoDoc));
  assert.deepEqual(fromText, fromObject);
  assert.equal(fromObject, pytoDoc, 'the same object is returned, not a copy');
  assert.throws(() => fromPytoRecord({ ...pytoDoc, schema: 'pyto-run-record@2' }), /schema: expected "pyto-run-record@1"/);
});

/* ---------------------------------------------------------------- */
/* hit derivation                                                    */
/* ---------------------------------------------------------------- */

test('deriveHit: a px: binding not produced earlier in the run is a hit', () => {
  const produced = new Set(['scratch.ablation.split']);
  assert.equal(deriveHit(['px:input.ablation.rows'], produced), true, 'preexisting Part read');
  assert.equal(deriveHit(['px:scratch.ablation.split'], produced), false, 'produced by this run');
  assert.equal(deriveHit(['fn:split'], produced), false, 'a result ref is not a Part read');
  assert.equal(deriveHit([], produced), false, 'reads nothing');
  assert.equal(deriveHit([], produced, true), true, 'the runtime reported reuse');
});

test('pyto record: hits are exactly the invocations that read a preexisting Part', () => {
  const record = fromPytoRecord(pytoDoc);
  const hits = invocations(record).filter((invocation) => invocation.hit).map((invocation) => invocation.id);
  assert.deepEqual(hits, ['select', 'split']);
  assert.equal(record.counters.hits, 2);
  assert.equal(record.counters.hits + record.counters.computed, record.counters.invocations);
  // sheet reads scratch.ablation.comparison, produced by `compare` in this run.
  assert.equal(byId(record, 'sheet').hit, false);
});

test('DiscStudio: reused === true makes every invocation of the second run a hit', () => {
  const first = fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt);
  const second = fromDiscStudioReceipt(dsDoc.second.pql, dsDoc.second.receipt);
  assert.equal(dsDoc.first.receipt.computed, 4);
  assert.equal(dsDoc.second.receipt.reused, 4);
  assert.equal(second.counters.hits, 4);
  assert.equal(second.counters.computed, 0);
  assert.ok(invocations(second).every((invocation) => invocation.hit));
  // First run: nothing is reused, so only the reads of Parts seeded before the
  // run count. CardSvg reads only the card this run produced -> computed.
  const cardSvg = byId(first, 'px.render.single.buzzz-mint.svg');
  assert.equal(cardSvg.hit, false);
  assert.deepEqual(cardSvg.declared_consumes, ['px:px.render.single.buzzz-mint.card']);
  assert.equal(first.counters.hits, 3);
});

test('DiscStudio: material identity, memo revision and the SVG wrapper survive the mapping', () => {
  const first = fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt);
  const art = byId(first, 'px.render.single.buzzz-mint.art');
  assert.equal(art.calculation.address, 'fn.disc.art');
  assert.equal(art.calculation.implementation_sha256, null, 'runtime.js hashes the memo signature, never the body');
  assert.equal(art.calculation.identity_scope, 'registered-address-and-revision:1');
  assert.match(art.result_sha256, /^disc\.art:[0-9a-f]+$/);
  assert.equal(art.duration_ms, null, 'runtime.js records no durations');

  const svg = byId(first, 'px.render.single.buzzz-mint.svg');
  assert.equal(svg.value.kind, 'svg');
  assert.ok(svg.value.data.startsWith('<svg'));
  assert.match(svg.value.note, /DiscStudio card wrapper/);
});

test('DiscStudio adapter also accepts a live run of src/runtime.js', async () => {
  const { createStudioRuntime } = await import('../../../src/runtime.js');
  const { createSeed } = await import('../../../src/seed.js');
  const runtime = createStudioRuntime(createSeed());
  const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
  runtime.card('buzzz-mint', 'broadcast', context);
  const live = fromDiscStudioReceipt(runtime.pxc.get('px.pql.display-card'), runtime.pxc.get('px.receipt.display-card'));
  validate(live);
  assert.equal(live.pcr, 'display-card');
  const fromFixture = fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt);
  assert.deepEqual(live.ticks.map((t) => t.name), fromFixture.ticks.map((t) => t.name));
  assert.deepEqual(invocations(live).map((i) => i.id), invocations(fromFixture).map((i) => i.id));
  assert.deepEqual(live.counters, fromFixture.counters);
});

test('ChessLab: one invocation per frozen Calculation, values omitted, divergence preserved', () => {
  const record = fromChessLabReceipts(chessDoc.receipts, { pcr: 'chesslab.debugger' });
  assert.deepEqual(record.ticks.map((tick) => tick.name), ['chess.s0.materializeObjects', 'chess.s1.analyzeSides', 'chess.s1.scoreCandidates']);
  assert.deepEqual(record.ticks[0].invocations.map((i) => i.id), ['chess.s0.materializeObjects#0', 'chess.s0.materializeObjects#1']);
  assert.ok(invocations(record).every((i) => i.value.kind === 'omitted'));
  assert.match(invocations(record)[0].value.note, /retain no Part values/);

  const s1 = byId(record, 'chess.s1.analyzeSides');
  assert.deepEqual(s1.declared_consumes, ['px:px.chess.objects']);
  assert.deepEqual(s1.actual_consumes, ['px.chess.frame', 'px.chess.objects']);
  assert.equal(s1.hit, false, 'px.chess.objects was produced by S0 in this record');
  assert.equal(s1.calculation.implementation_sha256.length, 64);

  // A receipt with no frozenCalculations still yields one invocation, with a
  // null address rather than an invented one.
  const scored = byId(record, 'chess.s1.scoreCandidates');
  assert.equal(scored.calculation.address, null);
  assert.deepEqual(scored.writes, [{ address: 'px.chess.analysis', kind: 'refinement' }]);
});

test('Wumpus: values are present and the SVG Part is classified as svg', () => {
  const record = fromWumpusRecords(wumpusDoc.records, { pcr: 'wumpus.belief' });
  assert.deepEqual(record.ticks.map((tick) => tick.name), ['Sense', 'Believe', 'Render']);
  const sense = byId(record, 'tick-1');
  assert.equal(sense.calculation.address, 'fn.wumpus.sense');
  assert.equal(sense.calculation.identity_scope, 'registered-address-only');
  assert.deepEqual(sense.value.data, { breeze: false, stench: false, glitter: false });
  assert.deepEqual(sense.writes, [{ address: 'px.agent.percept', kind: 'new-address' }]);
  assert.deepEqual(Object.keys(sense.args), ['grid', 'at'], 'the calculation input map becomes args');

  const render = byId(record, 'tick-3');
  assert.equal(render.value.kind, 'svg');
  assert.ok(render.value.data.startsWith('<svg'));
  assert.equal(typeof render.duration_ms, 'number');
});

/* ---------------------------------------------------------------- */
/* materialize                                                       */
/* ---------------------------------------------------------------- */

test('materialize classifies text, svg, png data URLs and JSON', () => {
  assert.equal(materialize('plain').kind, 'text');
  assert.equal(materialize('<svg xmlns="http://www.w3.org/2000/svg"></svg>').kind, 'svg');
  assert.equal(materialize('  \n<svg/>').kind, 'svg');
  assert.equal(materialize('<?xml version="1.0"?><svg/>').kind, 'svg');
  assert.equal(materialize('data:image/png;base64,iVBORw0KGgo=').kind, 'png-data-url');
  assert.equal(materialize({ a: 1 }).kind, 'json');
  assert.equal(materialize(undefined).kind, 'omitted');
  assert.match(materialize(undefined).note, /did not retain/);
});

test('materialize honours RECORD.md size and array caps', () => {
  const long = Array.from({ length: MAX_ARRAY_ENTRIES + 55 }, (_, i) => i);
  const truncated = materialize(long);
  assert.equal(truncated.kind, 'json');
  assert.equal(truncated.data.length, MAX_ARRAY_ENTRIES);
  assert.match(truncated.note, new RegExp(`first ${MAX_ARRAY_ENTRIES} of ${long.length} entries`));

  const huge = 'x'.repeat(MAX_VALUE_BYTES + 1);
  const omitted = materialize(huge, { digest: 'abc123' });
  assert.equal(omitted.kind, 'omitted');
  assert.equal(omitted.data, null);
  assert.match(omitted.note, new RegExp(`${MAX_VALUE_BYTES + 1} bytes over the ${MAX_VALUE_BYTES}-byte cap; digest abc123`));

  const circular = {};
  circular.self = circular;
  assert.equal(materialize(circular).kind, 'omitted');
});

test('materialize counts UTF-8 bytes, not characters', () => {
  const emoji = '🥏'.repeat(MAX_VALUE_BYTES / 4);
  assert.equal(emoji.length, MAX_VALUE_BYTES / 2, 'half as many UTF-16 units as the cap');
  assert.equal(materialize(emoji).kind, 'text', 'exactly at the cap');
  assert.equal(materialize(emoji + '🥏').kind, 'omitted', 'one code point over');
});

/* ---------------------------------------------------------------- */
/* part index                                                        */
/* ---------------------------------------------------------------- */

test('derivePartIndex names the writer, the readers and what preexisted', () => {
  const record = fromPytoRecord(pytoDoc);
  const parts = derivePartIndex(record.ticks);
  assert.deepEqual(parts['input.ablation.rows'], { written_by: null, read_by: ['split'], preexisting: true });
  assert.deepEqual(parts['scratch.ablation.split'], { written_by: 'split', read_by: [], preexisting: false });
  assert.deepEqual(parts['scratch.ablation.comparison'].written_by, 'compare');
  assert.deepEqual(parts['scratch.ablation.comparison'].read_by, ['sheet', 'retain']);
  assert.equal(parts['scratch.ablation.comparison'].preexisting, false);
  assert.deepEqual(parts, record.parts, 'the fixture carries the derived index');
});

test('bareAddress strips only the testimony marker', () => {
  assert.equal(bareAddress('px:a.b'), 'a.b');
  assert.equal(bareAddress('fn:split'), 'split');
  assert.equal(bareAddress('a.b'), 'a.b');
  assert.equal(bareAddress(undefined), '');
});

/* ---------------------------------------------------------------- */
/* validate: every violation names its path                          */
/* ---------------------------------------------------------------- */

/** node's assert.throws returns undefined, so capture the error directly. */
const caught = (fn) => {
  try {
    fn();
  } catch (error) {
    return error;
  }
  throw new assert.AssertionError({ message: 'expected a RecordSchemaError, none was thrown' });
};

const mutate = (path, value) => {
  const clone = structuredClone(pytoDoc);
  const keys = path.split('.');
  let node = clone;
  for (const key of keys.slice(0, -1)) node = node[/^\d+$/.test(key) ? Number(key) : key];
  const last = keys.at(-1);
  if (value === undefined) delete node[last];
  else node[/^\d+$/.test(last) ? Number(last) : last] = value;
  return clone;
};

const cases = [
  ['schema', 'nope', 'schema'],
  ['pcr', 42, 'pcr'],
  ['source.runtime', 'matlab', 'source.runtime'],
  ['source.commit', 7, 'source.commit'],
  ['ticks.0.index', 3, 'ticks[0].index'],
  ['ticks.0.name', null, 'ticks[0].name'],
  ['ticks.0.invocations.0.id', '', 'ticks[0].invocations[0].id'],
  ['ticks.0.invocations.0.calculation.identity_scope', undefined, 'ticks[0].invocations[0].calculation.identity_scope'],
  ['ticks.0.invocations.0.inputs.groups', 'input.ablation.groups', 'ticks[0].invocations[0].inputs.groups'],
  ['ticks.0.invocations.0.declared_consumes.0', 'input.ablation.groups', 'ticks[0].invocations[0].declared_consumes[0]'],
  ['ticks.0.invocations.0.actual_consumes', 'input.ablation.groups', 'ticks[0].invocations[0].actual_consumes'],
  ['ticks.0.invocations.0.writes.0.kind', 'clobber', 'ticks[0].invocations[0].writes[0].kind'],
  ['ticks.0.invocations.0.writes.0.kind', undefined, 'ticks[0].invocations[0].writes[0].kind'],
  ['ticks.0.invocations.0.duration_ms', 'fast', 'ticks[0].invocations[0].duration_ms'],
  ['ticks.0.invocations.0.hit', 'yes', 'ticks[0].invocations[0].hit'],
  ['ticks.0.invocations.0.value.kind', 'binary', 'ticks[0].invocations[0].value.kind'],
  ['ticks.3.invocations.0.value.data', 12, 'ticks[3].invocations[0].value.data'],
  ['ticks.4.invocations.0.value.note', null, 'ticks[4].invocations[0].value.note'],
  ['ticks.4.invocations.0.value.data', 'something', 'ticks[4].invocations[0].value.data'],
  ['counters.invocations', 99, 'counters.invocations'],
  ['counters.hits', 1, 'counters.hits'],
  ['counters.computed', 1, 'counters.computed'],
  ['counters.wall_ms', 'quick', 'counters.wall_ms']
];

for (const [path, value, expectedPath] of cases) {
  test(`validate rejects ${path} and names ${expectedPath}`, () => {
    const error = caught(() => validate(mutate(path, value)));
    assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
    assert.equal(error.path, expectedPath, error.message);
    assert.ok(error.message.startsWith(`${SCHEMA} ${expectedPath}: `), error.message);
  });
}

test('validate rejects a duplicate invocation id, because ids anchor annotations', () => {
  const clone = structuredClone(pytoDoc);
  clone.ticks[1].invocations[0].id = 'split';
  const error = caught(() => validate(clone));
  assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
  assert.equal(error.path, 'ticks[1].invocations[0].id');
  assert.match(error.message, /duplicate invocation id "split"/);
});

test('validate rejects a malformed parts entry with the address in the path', () => {
  const clone = structuredClone(pytoDoc);
  clone.parts['scratch.ablation.split'].read_by = 'split';
  const error = caught(() => validate(clone));
  assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
  assert.equal(error.path, 'parts["scratch.ablation.split"].read_by');
});

test('validate rejects a non-object document', () => {
  assert.throws(() => validate(null), /document: expected an object/);
  assert.throws(() => validate([]), /document: expected an object/);
});

/* ---------------------------------------------------------------- */
/* the Python materializer's own output                              */
/* ---------------------------------------------------------------- */

const REAL_RECORD = resolve(HERE, '..', '..', 'experiments', 'grouped-ablation', 'evidence', 'run-1', 'record.json');
const realRecordExists = existsSync(REAL_RECORD);

test('the record pyto.materialize wrote for grouped-ablation run-1 validates unchanged', {
  skip: realRecordExists ? false : `${REAL_RECORD} is absent; the Python materializer has not written a record here yet`
}, () => {
  const record = fromPytoRecord(JSON.parse(readFileSync(REAL_RECORD, 'utf8')));
  assert.equal(record.source.runtime, 'pyto');
  assert.equal(record.counters.invocations, 15);
  // The same hit rule the viewer applies to every runtime: exactly the two
  // invocations that read a Part seeded before the run.
  const hits = invocations(record).filter((invocation) => invocation.hit).map((invocation) => invocation.id);
  assert.deepEqual(hits, ['select', 'split']);
  assert.equal(record.counters.hits, 2);
  assert.deepEqual(derivePartIndex(record.ticks), record.parts, 'the writer/reader index agrees with the invocations');
});
